# Foods Manager 🍽️

**Foods Manager** is a corporate food management and kitchen attendance system designed to optimize meal preparation, streamline kitchen logistics, and prevent food wastage across 3 daily meal timings.

---

## 🕒 Core Meal Timings & Schedule
The application is pre-configured for the 3 daily company meal slots:
1. **Breakfast**: Serving at **8:45 AM** (Cutoff: 8:00 AM)
2. **Lunch**: Serving at **1:00 PM** (Cutoff: 12:00 PM)
3. **Dinner**: Serving at **7:00 PM** (Cutoff: 6:00 PM)

---

## 🌟 The 3 System Roles

### 1. 👨‍💼 Administrator
- **Executive Analytics**: Real-time KPI counters for total staff, confirmed meal plates across the day, food wastage prevented, and cost savings.
- **Consumption Analytics**: 7-day stacked bar charts tracking plates served vs. plates saved.
- **User Directory**: Add, modify, or deactivate employees, kitchen staff, and admins.
- **Data Export**: 1-click CSV download of daily attendance with employee names, departments, dietary requirements, and opt-out remarks.

### 2. 👨‍🍳 Kitchen Staff (Chefs & Cooks)
- **Menu Management**: Publish and update menus for Breakfast, Lunch, and Dinner with dishes, sides, beverages, and allergen/dietary tags.
- **Kitchen Quick Presets**: 1-click templates for South Indian, North Indian, Mughlai Dum Biryani, and Indo-Chinese menus.
- **Live Headcount Command**: Live counters showing exact confirmed attendee numbers vs. skipped counts.
- **Smart Prep Calculator**: Calculates ingredient prep weights (rice in kg, dal/curry in liters, rotis/breads in pieces) based on active headcounts.
- **Printable Kitchen Sheet**: Formatted kitchen clipboard printout for the meal serving counter.

### 3. 👤 Employees (Eating Staff)
- **Today's Menu Display**: See what's cooking for Breakfast, Lunch, and Dinner.
- **Default Attendance Policy**:
  > **By default, every employee is marked as "Attending" (Will come / Yes) for all 3 meals.**
- **Simple Opt-Out Toggle**: If an employee won't be attending, they can toggle to *"Skipping"* with an optional note (e.g., WFH, meeting, doctor visit).
- **1-Click Bulk Actions**: "I will eat all 3 meals" or "Opt-out of all 3 today".
- **Dietary Registration**: Tracks Vegetarian, Non-Vegetarian, Jain, Vegan preferences.

---

## 🚀 How to Run

### 1. Start the Server
Open your terminal in the project directory:
```powershell
cd C:\Users\Deepak\.gemini\antigravity\scratch\foods-manager
python run.py
```

### 2. Open in Browser
Visit:
```
http://localhost:8050
```

---

## 🎨 Faithful UI Implementation (Mockups 1 & 2)
The web application includes both UI screens shared in your design:
1. **Employee / Guest Mobile UI (Image 1)**:
   - "Good Food Brings People Together" header with brush underline & fork-spoon doodle.
   - Poha (`#FFF8E7`), Thali (`#FDF1ED`), and Paneer (`#EFF6FC`) meal cards with exact badge colors, bullet lists, and "Will you come? →" CTA buttons.
   - Default attendance opt-out model with one-click interactive RSVP.
   - Desktop Phone Frame toggle (Preview mobile frame or expand full-width).
2. **Kitchen Staff Dashboard (Image 2)**:
   - Deep forest green sidebar (`#0B2827`) with navigation icons and Kitchen Staff profile.
   - Meal cards with "Ready to Serve", "In Progress", and "Not Started" pills, "Serves 45" counters, and cooking status.
   - Bottom "Quick Counts" box (Breakfast: 45, Lunch: 45, Dinner: 45).
3. **Top Switcher Bar**:
   - Easily switch between Employee Home (Image 1), Kitchen Staff (Image 2), and Admin Dashboard.

## 🔑 Demo Accounts (Pre-Seeded)

The webapp includes a **Top Quick Role Switcher** banner for testing any role with a single click:

| Role | Username | Password | Full Name | Department / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Sunita Rao | Admin Dashboard & Users |
| **Kitchen Staff** | `chef` | `chef123` | Chef Ramesh Kumar | Menu Updates & Headcounts |
| **Sous Chef** | `chef2` | `chef123` | Meera Joseph | Kitchen Operations |
| **Employee 1** | `emp1` | `emp123` | Rahul Sharma | Engineering (Regular) |
| **Employee 2** | `emp2` | `emp123` | Priya Patel | Design (Vegetarian) |
| **Employee 3** | `emp3` | `emp123` | Amit Verma | QA (Non-Vegetarian) |
| **Employee 7** | `emp7` | `emp123` | Karan Malhotra | Finance (Jain) |

---

## 🧪 Automated Testing
Run the comprehensive test suite verifying all 7 core flows:
```powershell
python -m app.test_app
```
Test results verify:
1. Root index rendering
2. Meal slot configuration (8:45 AM, 1:00 PM, 7:00 PM)
3. Menu publication and retrieval
4. **Default "Attending" behavior for all employees across all 3 meals**
5. Employee opt-out toggling
6. Real-time kitchen headcount updates
7. Admin dashboard calculations and CSV export
