from datetime import datetime, date, timedelta
from app.database import get_db, init_db
from app.auth import hash_password

def seed_data():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # Clear existing data if re-seeding
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM menus")
    cursor.execute("DELETE FROM attendance")

    # Base users
    users_data = [
        # Admin
        ("admin", hash_password("admin123"), "Admin Officer (Sunita Rao)", "admin@foodmanager.org", "admin", "Administration", "Regular"),
        # Kitchen Staff
        ("chef", hash_password("chef123"), "Kitchen Staff (Chef Ramesh)", "kitchen@foodmanager.org", "kitchen", "Kitchen Operations", "Regular"),
        ("chef2", hash_password("chef123"), "Sous Chef (Meera Joseph)", "meera.chef@foodmanager.org", "kitchen", "Kitchen Operations", "Regular"),
    ]

    # Named employees
    named_employees = [
        ("guest", hash_password("guest123"), "Guest Employee", "guest@company.com", "employee", "General", "Regular"),
        ("emp1", hash_password("emp123"), "Rahul Sharma", "rahul.s@company.com", "employee", "Engineering", "Regular"),
        ("emp2", hash_password("emp123"), "Priya Patel", "priya.p@company.com", "employee", "Design", "Vegetarian"),
        ("emp3", hash_password("emp123"), "Amit Verma", "amit.v@company.com", "employee", "QA & Testing", "Non-Vegetarian"),
        ("emp4", hash_password("emp123"), "Sneha Reddy", "sneha.r@company.com", "employee", "Human Resources", "Vegetarian"),
        ("emp5", hash_password("emp123"), "Vikram Singh", "vikram.s@company.com", "employee", "Engineering", "Regular"),
        ("emp6", hash_password("emp123"), "Ananya Gupta", "ananya.g@company.com", "employee", "Marketing", "Vegan"),
        ("emp7", hash_password("emp123"), "Karan Malhotra", "karan.m@company.com", "employee", "Finance", "Jain"),
        ("emp8", hash_password("emp123"), "Deepa Nair", "deepa.n@company.com", "employee", "Data & AI", "Regular"),
        ("emp9", hash_password("emp123"), "Rohan Joshi", "rohan.j@company.com", "employee", "Cloud & DevOps", "Vegetarian"),
        ("emp10", hash_password("emp123"), "Neha Kapoor", "neha.k@company.com", "employee", "Product Management", "Regular"),
        ("emp11", hash_password("emp123"), "Suresh Kumar", "suresh.k@company.com", "employee", "IT Support", "Regular"),
        ("emp12", hash_password("emp123"), "Tanvi Sen", "tanvi.s@company.com", "employee", "Communications", "Vegetarian")
    ]
    users_data.extend(named_employees)

    # Add additional employees up to 45 so "Serves 45" matches the exact design
    dept_cycle = ["Engineering", "Product", "Operations", "Sales", "Customer Support", "Finance", "Design"]
    diet_cycle = ["Regular", "Vegetarian", "Non-Vegetarian", "Jain", "Vegan"]
    current_count = len(named_employees)
    for i in range(current_count + 1, 46):
        dept = dept_cycle[i % len(dept_cycle)]
        diet = diet_cycle[i % len(diet_cycle)]
        users_data.append((
            f"emp{i}",
            hash_password("emp123"),
            f"Staff Member {i}",
            f"staff{i}@company.com",
            "employee",
            dept,
            diet
        ))

    cursor.executemany('''
    INSERT INTO users (username, password_hash, full_name, email, role, department, dietary_preference)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', users_data)

    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    # Seed Menus matching EXACTLY the user's UI mockup!
    menus_data = [
        # Today
        (today_str, "breakfast", 
         "Poha, Boiled Egg, Tea", 
         "Mint Chutney, Sev, Lemon wedges", 
         "Ginger Masala Tea", 
         "High Protein, Fresh", 
         "Cooked fresh today with organic peanuts & fresh curry leaves.", 
         "/static/images/poha.jpg",
         "Ready to Serve",
         "Completed",
         "Head Chef Ramesh"),

        (today_str, "lunch", 
         "Rice, Dal Tadka, Mixed Veg, Roti, Salad", 
         "Pickle, Roasted Papad, Onion Salad", 
         "Spiced Chaas", 
         "Balanced Meal, Homestyle", 
         "Cooked fresh today with whole spices.", 
         "/static/images/thali.jpg",
         "In Progress",
         "Cooking",
         "Head Chef Ramesh"),

        (today_str, "dinner", 
         "Roti, Paneer Sabzi, Jeera Rice, Salad", 
         "Cucumber Raita, Green Salad", 
         "Warm Almond Milk", 
         "High Protein, Comfort Food", 
         "Cooked fresh today with fresh cottage cheese.", 
         "/static/images/paneer.jpg",
         "Not Started",
         "Not Started",
         "Sous Chef Meera"),

        # Tomorrow
        (tomorrow_str, "breakfast", 
         "Aloo Paratha, Curd, Pickle, Tea", 
         "Fresh Butter, Mint Chutney", 
         "Masala Chai", 
         "North Indian Classic", 
         "Made with fresh whole wheat.", 
         "/static/images/poha.jpg",
         "Not Started",
         "Not Started",
         "Head Chef Ramesh"),

        (tomorrow_str, "lunch", 
         "Rajma Masala, Steamed Rice, Tandoori Roti, Salad", 
         "Mixed Veg Raita, Papad", 
         "Sweet Lassi", 
         "Traditional Indian", 
         "Slow cooked overnight rajma.", 
         "/static/images/thali.jpg",
         "Not Started",
         "Not Started",
         "Sous Chef Meera"),

        (tomorrow_str, "dinner", 
         "Veg Dum Biryani, Salan, Roti, Salad", 
         "Boondi Raita, Onion salad", 
         "Gulab Jamun", 
         "Mughlai Special", 
         "Dum cooked with aromatic spices.", 
         "/static/images/paneer.jpg",
         "Not Started",
         "Not Started",
         "Head Chef Ramesh")
    ]

    cursor.executemany('''
    INSERT INTO menus (date, meal_slot, main_items, side_items, beverage, dietary_tags, special_note, image_url, prep_status, cooking_state, updated_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', menus_data)

    conn.commit()
    conn.close()
    print("Database seeded with 45 staff members and exact UI mockup menus!")

if __name__ == '__main__':
    seed_data()
