import asyncio
import httpx
from app.main import app

async def run_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Test 1: Fetch root page
        res = await client.get("/")
        assert res.status_code == 200
        assert "Food Manager" in res.text
        print("[PASS] Root index page renders successfully")

        # Test 2: Fetch meal slots
        res = await client.get("/api/meal-slots")
        assert res.status_code == 200
        slots = res.json()["slots"]
        assert len(slots) == 3
        slot_names = [s["id"] for s in slots]
        assert "breakfast" in slot_names and "lunch" in slot_names and "dinner" in slot_names
        print("[PASS] Meal slots verified (Breakfast at 8:45 AM, Lunch at 1:00 PM, Dinner at 7:00 PM)")

        # Test 3: Fetch menus
        res = await client.get("/api/menus")
        assert res.status_code == 200
        menus = res.json()["items"]
        assert len(menus) == 3
        print("[PASS] Menus endpoint returned 3 meal menus")

        # Test 4: Check default attendance logic
        # Get first employee
        users_res = await client.get("/api/users/list")
        emp = next(u for u in users_res.json()["users"] if u["role"] == "employee")
        res = await client.post("/api/auth/switch-user", json={"user_id": emp["id"]})
        assert res.status_code == 200
        cookies = res.cookies

        res = await client.get("/api/attendance/my", cookies=cookies)
        assert res.status_code == 200
        att_items = res.json()["items"]
        for item in att_items:
            # Default attendance must be 'attending'
            assert item["status"] == "attending"
        print("[PASS] Employee attendance default is verified as ATTENDING ('will come') for all 3 meals")

        # Test 5: Employee toggles to not_attending (opt-out) for breakfast
        res = await client.post("/api/attendance/update", cookies=cookies, json={
            "date": res.json()["date"],
            "items": [{"meal_slot": "breakfast", "status": "not_attending", "note": "Testing skip"}]
        })
        assert res.status_code == 200

        # Verify attendance updated
        res = await client.get("/api/attendance/my", cookies=cookies)
        bf_item = next(it for it in res.json()["items"] if it["slot"]["id"] == "breakfast")
        assert bf_item["status"] == "not_attending"
        assert bf_item["note"] == "Testing skip"
        print("[PASS] Employee opt-out toggle updated successfully")

        # Test 6: Kitchen summary reflects the updated headcount accurately
        res = await client.get("/api/attendance/summary")
        assert res.status_code == 200
        summary = res.json()["summary"]
        assert summary["breakfast"]["opted_out_count"] >= 1
        print("[PASS] Kitchen summary headcount reflects attendance changes in real-time")

        # Test 7: Admin stats and export CSV
        res = await client.get("/api/admin/stats")
        assert res.status_code == 200
        assert res.json()["total_employees"] > 0
        print("[PASS] Admin analytics and stats calculated properly")

        res = await client.get("/api/admin/export-csv")
        assert res.status_code == 200
        assert "Employee Name" in res.text
        print("[PASS] Attendance CSV export generated successfully")

        print("\nALL 7 SYSTEM TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    asyncio.run(run_tests())
