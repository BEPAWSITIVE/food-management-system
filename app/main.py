import os
import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, status, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import get_db, init_db
from app.auth import hash_password, verify_password

# Initialize FastAPI app
app = FastAPI(title="Foods Manager", description="Corporate Food & Meal Attendance Management System")

# Ensure DB is initialized
init_db()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Models for request bodies
class LoginRequest(BaseModel):
    username: str
    password: str

class SwitchUserRequest(BaseModel):
    user_id: int

class UpdateAttendanceItem(BaseModel):
    meal_slot: str
    status: str  # 'attending' or 'not_attending'
    note: Optional[str] = ""

class UpdateAttendanceBatchRequest(BaseModel):
    date: str
    items: List[UpdateAttendanceItem]

class UpdateMenuRequest(BaseModel):
    date: str
    meal_slot: str
    main_items: str
    side_items: Optional[str] = ""
    beverage: Optional[str] = ""
    dietary_tags: Optional[str] = ""
    special_note: Optional[str] = ""
    image_url: Optional[str] = ""
    prep_status: Optional[str] = "Not Started"
    cooking_state: Optional[str] = "Not Started"

class UpdateMenuStatusRequest(BaseModel):
    date: str
    meal_slot: str
    prep_status: str
    cooking_state: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = ""
    role: str
    department: Optional[str] = "General"
    dietary_preference: Optional[str] = "Regular"

class UpdateUserRequest(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = ""
    role: str
    department: Optional[str] = "General"
    dietary_preference: Optional[str] = "Regular"
    active: Optional[int] = 1

# Helper function to get user from cookie or authorization header
def get_current_user_from_req(request: Request):
    user_id = request.cookies.get("fm_user_id")
    if not user_id:
        # Check header
        auth = request.headers.get("X-User-Id")
        if auth and auth.isdigit():
            user_id = auth
    if not user_id:
        return None
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, email, role, department, dietary_preference, active FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

# ==================== HTML PAGE ROUTE ====================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Foods Manager is loading... Please create templates/index.html</h1>"

# ==================== AUTH ROUTES ====================

@app.post("/api/auth/login")
async def login(req: LoginRequest, response: Response):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND active = 1", (req.username.strip(),))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_dict = {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "department": user["department"],
        "dietary_preference": user["dietary_preference"]
    }
    
    # Set session cookie
    response.set_cookie(key="fm_user_id", value=str(user["id"]), httponly=False, samesite="lax", max_age=86400*7)
    return {"status": "success", "user": user_dict}

@app.post("/api/auth/switch-user")
async def switch_user(req: SwitchUserRequest, response: Response):
    """Convenient switch endpoint for demo/testing across Admin, Chef, and Employees."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, email, role, department, dietary_preference, active FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = dict(user)
    response.set_cookie(key="fm_user_id", value=str(user["id"]), httponly=False, samesite="lax", max_age=86400*7)
    return {"status": "success", "user": user_dict}

@app.get("/api/auth/me")
async def get_me(request: Request):
    user = get_current_user_from_req(request)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}

@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="fm_user_id")
    return {"status": "success", "message": "Logged out"}

@app.get("/api/users/list")
async def list_users_for_switcher():
    """List users grouped by role for the fast demo switcher."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role, department, dietary_preference FROM users WHERE active = 1 ORDER BY role, id")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"users": users}

# ==================== MEAL SLOTS & TIMINGS ====================

@app.get("/api/meal-slots")
async def get_meal_slots():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meal_slots ORDER BY display_order")
    slots = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"slots": slots}

# ==================== MENU ROUTES ====================

@app.get("/api/menus")
async def get_menus(date_str: Optional[str] = None):
    target_date = date_str or date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()

    # Get all slots
    cursor.execute("SELECT * FROM meal_slots ORDER BY display_order")
    slots = [dict(row) for row in cursor.fetchall()]

    # Get menus for this date
    cursor.execute("SELECT * FROM menus WHERE date = ?", (target_date,))
    menus_by_slot = {row["meal_slot"]: dict(row) for row in cursor.fetchall()}

    result = []
    for slot in slots:
        slot_id = slot["id"]
        menu = menus_by_slot.get(slot_id)
        result.append({
            "slot": slot,
            "has_menu": menu is not None,
            "menu": menu or {
                "date": target_date,
                "meal_slot": slot_id,
                "main_items": "Menu yet to be updated by kitchen staff",
                "side_items": "",
                "beverage": "",
                "dietary_tags": "Pending update",
                "special_note": "Please check back closer to serving time.",
                "image_url": f"/static/images/{'poha.jpg' if slot_id=='breakfast' else 'thali.jpg' if slot_id=='lunch' else 'paneer.jpg'}",
                "prep_status": "Not Started",
                "cooking_state": "Not Started",
                "updated_by": "Pending"
            }
        })

    conn.close()
    return {"date": target_date, "items": result}

@app.post("/api/menus/update")
async def update_menu(req: UpdateMenuRequest, request: Request):
    user = get_current_user_from_req(request)
    updated_by_name = user["full_name"] if user else "Kitchen Staff"

    # Default image if empty
    img = req.image_url
    if not img:
        if req.meal_slot == 'breakfast': img = '/static/images/poha.jpg'
        elif req.meal_slot == 'lunch': img = '/static/images/thali.jpg'
        else: img = '/static/images/paneer.jpg'
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO menus (date, meal_slot, main_items, side_items, beverage, dietary_tags, special_note, image_url, prep_status, cooking_state, updated_by, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(date, meal_slot) DO UPDATE SET
        main_items = excluded.main_items,
        side_items = excluded.side_items,
        beverage = excluded.beverage,
        dietary_tags = excluded.dietary_tags,
        special_note = excluded.special_note,
        image_url = CASE WHEN excluded.image_url != '' THEN excluded.image_url ELSE menus.image_url END,
        prep_status = CASE WHEN excluded.prep_status != '' THEN excluded.prep_status ELSE menus.prep_status END,
        cooking_state = CASE WHEN excluded.cooking_state != '' THEN excluded.cooking_state ELSE menus.cooking_state END,
        updated_by = excluded.updated_by,
        updated_at = CURRENT_TIMESTAMP
    ''', (
        req.date,
        req.meal_slot,
        req.main_items,
        req.side_items or "",
        req.beverage or "",
        req.dietary_tags or "",
        req.special_note or "",
        img,
        req.prep_status or "Not Started",
        req.cooking_state or "Not Started",
        updated_by_name
    ))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Menu for {req.meal_slot.capitalize()} on {req.date} updated successfully!"}

@app.post("/api/menus/status")
async def update_menu_status(req: UpdateMenuStatusRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE menus SET
        prep_status = ?,
        cooking_state = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE date = ? AND meal_slot = ?
    ''', (req.prep_status, req.cooking_state, req.date, req.meal_slot))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Status updated for {req.meal_slot.capitalize()}"}

@app.get("/api/menus/presets")
async def get_menu_presets():
    """Quick templates that Kitchen Staff can pick with 1 click."""
    presets = [
        {
            "category": "Breakfast",
            "name": "South Indian Classic",
            "main_items": "Steaming Idli, Crispy Medu Vada, Coconut & Tomato Chutney",
            "side_items": "Hot Drumstick Sambar, Fresh Papaya slices",
            "beverage": "South Indian Filter Coffee / Masala Tea",
            "dietary_tags": "Vegetarian, South Indian, Jain option",
            "special_note": "Prepared with organic ghee and freshly milled batter."
        },
        {
            "category": "Breakfast",
            "name": "North Indian Hearty",
            "main_items": "Aloo & Paneer Paratha, Spiced Poha with Peanuts",
            "side_items": "Fresh Homemade Curd, Green Mint Chutney, Pickle",
            "beverage": "Adrak Chai / Fresh Watermelon Juice",
            "dietary_tags": "Vegetarian, High Energy",
            "special_note": "100% whole wheat parathas served with white butter."
        },
        {
            "category": "Lunch",
            "name": "Royal North Indian Thali",
            "main_items": "Paneer Butter Masala, Dal Makhani, Steamed Basmati Rice & Butter Roti",
            "side_items": "Cucumber Boondi Raita, Fresh Green Salad, Roasted Papad",
            "beverage": "Chilled Sweet Lassi / Spiced Chaas",
            "dietary_tags": "Vegetarian, North Indian",
            "special_note": "Slow cooked dal with aromatic spices. High protein lunch."
        },
        {
            "category": "Lunch",
            "name": "South Indian Thali",
            "main_items": "Vegetable Korma, Mysore Rasam, Steamed Rice & Poori",
            "side_items": "Beans Poriyal, Crispy Appalam, Curd Rice",
            "beverage": "Fresh Lime Soda / Buttermilk",
            "dietary_tags": "Vegetarian, Traditional",
            "special_note": "Light, wholesome and easily digestible."
        },
        {
            "category": "Dinner",
            "name": "Dum Biryani Special",
            "main_items": "Hyderabadi Veg Dum Biryani, Paneer Tikka Masala, Fluffy Phulkas",
            "side_items": "Mirchi Ka Salan, Onion Mint Raita, Masala Papad",
            "beverage": "Warm Gulab Jamun & Kesar Badam Milk",
            "dietary_tags": "Vegetarian, Mughlai Delight",
            "special_note": "Dum cooked with saffron and fresh herbs."
        },
        {
            "category": "Dinner",
            "name": "Indo-Chinese Fusion",
            "main_items": "Veg Hakka Noodles, Vegetable Manchurian in Hot Garlic Gravy, Fried Rice",
            "side_items": "Crispy Veg Spring Rolls, Sweet Corn Soup",
            "beverage": "Vanilla Ice Cream with Hot Chocolate Fudge",
            "dietary_tags": "Indo-Chinese, Fusion",
            "special_note": "No added MSG. Made with fresh garden vegetables."
        }
    ]
    return {"presets": presets}

# ==================== ATTENDANCE (DEFAULT = COMING / ATTENDING) ====================

@app.get("/api/attendance/my")
async def get_my_attendance(date_str: Optional[str] = None, request: Request = None):
    user = get_current_user_from_req(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please login first")

    target_date = date_str or date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()

    # Get meal slots
    cursor.execute("SELECT * FROM meal_slots ORDER BY display_order")
    slots = [dict(row) for row in cursor.fetchall()]

    # Get menus for this date
    cursor.execute("SELECT * FROM menus WHERE date = ?", (target_date,))
    menus_by_slot = {row["meal_slot"]: dict(row) for row in cursor.fetchall()}

    # Get existing attendance records for this user and date
    cursor.execute("SELECT * FROM attendance WHERE user_id = ? AND date = ?", (user["id"], target_date))
    attendance_by_slot = {row["meal_slot"]: dict(row) for row in cursor.fetchall()}

    conn.close()

    items = []
    for slot in slots:
        slot_id = slot["id"]
        record = attendance_by_slot.get(slot_id)
        menu = menus_by_slot.get(slot_id)

        # Core logic: If user hasn't explicitly set status, DEFAULT IS 'attending'
        if record:
            current_status = record["status"]
            note = record.get("note", "")
            is_default = False
        else:
            current_status = "attending"
            note = ""
            is_default = True

        items.append({
            "slot": slot,
            "status": current_status,  # 'attending' or 'not_attending'
            "is_default": is_default,
            "note": note,
            "menu": menu
        })

    return {
        "date": target_date,
        "user": user,
        "items": items
    }

@app.post("/api/attendance/update")
async def update_attendance(req: UpdateAttendanceBatchRequest, request: Request):
    user = get_current_user_from_req(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please login first")

    conn = get_db()
    cursor = conn.cursor()

    for item in req.items:
        cursor.execute('''
        INSERT INTO attendance (user_id, date, meal_slot, status, note, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, date, meal_slot) DO UPDATE SET
            status = excluded.status,
            note = excluded.note,
            updated_at = CURRENT_TIMESTAMP
        ''', (user["id"], req.date, item.meal_slot, item.status, item.note or ""))

    conn.commit()
    conn.close()
    return {"status": "success", "message": "Meal attendance preferences updated successfully!"}

# ==================== KITCHEN & ADMIN HEADCOUNT SUMMARY ====================

@app.get("/api/attendance/summary")
async def get_attendance_summary(date_str: Optional[str] = None):
    target_date = date_str or date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()

    # Active employees
    cursor.execute("SELECT id, username, full_name, department, dietary_preference FROM users WHERE role = 'employee' AND active = 1")
    employees = [dict(row) for row in cursor.fetchall()]
    total_employees = len(employees)

    # Meal slots
    cursor.execute("SELECT * FROM meal_slots ORDER BY display_order")
    slots = [dict(row) for row in cursor.fetchall()]

    # Menus
    cursor.execute("SELECT * FROM menus WHERE date = ?", (target_date,))
    menus = {row["meal_slot"]: dict(row) for row in cursor.fetchall()}

    # Explicit attendance records for this date
    cursor.execute('''
    SELECT a.*, u.full_name, u.department, u.dietary_preference 
    FROM attendance a 
    JOIN users u ON a.user_id = u.id 
    WHERE a.date = ?
    ''', (target_date,))
    att_rows = [dict(r) for r in cursor.fetchall()]

    summary_by_slot = {}

    for slot in slots:
        slot_id = slot["id"]
        # Find explicit opt-outs and explicit attendings
        slot_records = {r["user_id"]: r for r in att_rows if r["meal_slot"] == slot_id}
        
        attending_users = []
        opted_out_users = []
        dietary_breakdown = {"Regular": 0, "Vegetarian": 0, "Non-Vegetarian": 0, "Vegan": 0, "Jain": 0}

        for emp in employees:
            uid = emp["id"]
            diet = emp.get("dietary_preference", "Regular")
            rec = slot_records.get(uid)

            if rec and rec["status"] == "not_attending":
                opted_out_users.append({
                    "id": emp["id"],
                    "name": emp["full_name"],
                    "department": emp["department"],
                    "dietary_preference": diet,
                    "note": rec.get("note", "Opted out"),
                    "updated_at": rec.get("updated_at")
                })
            else:
                # DEFAULT IS ATTENDING
                attending_users.append({
                    "id": emp["id"],
                    "name": emp["full_name"],
                    "department": emp["department"],
                    "dietary_preference": diet,
                    "note": rec.get("note", "") if rec else "Default attending",
                    "is_default": rec is None
                })
                dietary_breakdown[diet] = dietary_breakdown.get(diet, 0) + 1

        summary_by_slot[slot_id] = {
            "slot": slot,
            "menu": menus.get(slot_id),
            "total_capacity": total_employees,
            "attending_count": len(attending_users),
            "opted_out_count": len(opted_out_users),
            "attendance_rate": round((len(attending_users) / total_employees * 100), 1) if total_employees > 0 else 0,
            "dietary_breakdown": dietary_breakdown,
            "attending_users": attending_users,
            "opted_out_users": opted_out_users
        }

    conn.close()
    return {
        "date": target_date,
        "total_employees": total_employees,
        "summary": summary_by_slot
    }

# ==================== ADMIN ANALYTICS & USER MANAGEMENT ====================

@app.get("/api/admin/stats")
async def get_admin_stats(date_str: Optional[str] = None):
    target_date = date_str or date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'employee' AND active = 1")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'kitchen' AND active = 1")
    total_kitchen = cursor.fetchone()[0]

    # Calculate estimated wastage reduction for today
    # Every opted-out meal saves roughly $4.50 / Rs. 120 and prevents unconsumed food
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'not_attending'", (target_date,))
    opted_out_count = cursor.fetchone()[0]
    estimated_savings = opted_out_count * 150  # Rs. 150 per meal

    # 7-day attendance trend
    today = date.today()
    trend = []
    for i in range(6, -1, -1):
        d_str = (today - timedelta(days=i)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'not_attending'", (d_str,))
        opt_out = cursor.fetchone()[0]
        # Total possible meal servings across 3 meals = total_employees * 3
        total_servings = total_employees * 3
        actual_servings = max(0, total_servings - opt_out)
        trend.append({
            "date": d_str,
            "display": (today - timedelta(days=i)).strftime("%a, %b %d"),
            "servings": actual_servings,
            "opt_outs": opt_out
        })

    # Department participation
    cursor.execute('''
    SELECT department, COUNT(*) as count 
    FROM users 
    WHERE role = 'employee' AND active = 1 
    GROUP BY department
    ''')
    departments = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {
        "total_employees": total_employees,
        "total_kitchen": total_kitchen,
        "today_opt_outs": opted_out_count,
        "estimated_savings_rupees": estimated_savings,
        "trend_7_days": trend,
        "departments": departments
    }

@app.get("/api/admin/users")
async def list_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, email, role, department, dietary_preference, active, created_at FROM users ORDER BY role, id")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"users": users}

@app.post("/api/admin/users")
async def create_user(req: CreateUserRequest):
    conn = get_db()
    cursor = conn.cursor()
    try:
        pw_hash = hash_password(req.password)
        cursor.execute('''
        INSERT INTO users (username, password_hash, full_name, email, role, department, dietary_preference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (req.username.strip(), pw_hash, req.full_name.strip(), req.email.strip(), req.role, req.department, req.dietary_preference))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return {"status": "success", "message": f"User {req.username} created successfully!", "id": new_id}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")

@app.put("/api/admin/users")
async def update_user(req: UpdateUserRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE users SET
        full_name = ?,
        email = ?,
        role = ?,
        department = ?,
        dietary_preference = ?,
        active = ?
    WHERE id = ?
    ''', (req.full_name, req.email, req.role, req.department, req.dietary_preference, req.active, req.id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "User updated successfully!"}

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    # Prevent deleting admin user 1
    if user_id == 1:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot delete root administrator")
    cursor.execute("DELETE FROM attendance WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "User deleted successfully!"}

# ==================== CSV REPORT EXPORT ====================

@app.get("/api/admin/export-csv")
async def export_attendance_csv(date_str: Optional[str] = None):
    target_date = date_str or date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, full_name, department, dietary_preference FROM users WHERE role = 'employee' AND active = 1 ORDER BY full_name")
    employees = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT user_id, meal_slot, status, note FROM attendance WHERE date = ?", (target_date,))
    attendance_map = {(row["user_id"], row["meal_slot"]): (row["status"], row["note"]) for row in cursor.fetchall()}

    conn.close()

    lines = ["Employee ID,Employee Name,Department,Dietary Preference,Breakfast (8:45 AM),Lunch (1:00 PM),Dinner (7:00 PM),Opt-out Notes"]
    
    for emp in employees:
        uid = emp["id"]
        # Default is Attending if not marked
        bf_status, bf_note = attendance_map.get((uid, "breakfast"), ("attending", ""))
        lu_status, lu_note = attendance_map.get((uid, "lunch"), ("attending", ""))
        di_status, di_note = attendance_map.get((uid, "dinner"), ("attending", ""))

        notes = []
        if bf_note: notes.append(f"Breakfast: {bf_note}")
        if lu_note: notes.append(f"Lunch: {lu_note}")
        if di_note: notes.append(f"Dinner: {di_note}")
        notes_str = "; ".join(notes).replace('"', '""')

        line = f'{uid},"{emp["full_name"]}","{emp["department"]}","{emp["dietary_preference"]}",{bf_status.capitalize()},{lu_status.capitalize()},{di_status.capitalize()},"{notes_str}"'
        lines.append(line)

    csv_content = "\n".join(lines)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=FoodsManager_Attendance_{target_date}.csv"}
    )
