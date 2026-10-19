// Food Manager - Core Frontend JavaScript

const state = {
    currentView: 'employee', // 'employee' | 'kitchen' | 'admin'
    selectedDate: new Date().toISOString().split('T')[0],
    currentUser: null,
    phoneFrameOn: true,
    allUsers: [],
    menusData: {},
    attendanceSummary: null,
    myAttendance: {},
    activeRsvpSlot: null,
    trendChartInstance: null
};

document.addEventListener('DOMContentLoaded', async () => {
    initDate();
    await loadCurrentUser();
    await loadUsers();
    await refreshAllData();
});

function initDate() {
    const input = document.getElementById('appDateInput');
    if (input) input.value = state.selectedDate;
}

function changeDateOffset(offset) {
    const d = new Date(state.selectedDate);
    d.setDate(d.getDate() + offset);
    state.selectedDate = d.toISOString().split('T')[0];
    const input = document.getElementById('appDateInput');
    if (input) input.value = state.selectedDate;
    refreshAllData();
}

function onDateChanged(val) {
    if (!val) return;
    state.selectedDate = val;
    refreshAllData();
}

// User & Role Management
async function loadCurrentUser() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.authenticated && data.user) {
            state.currentUser = data.user;
        } else {
            // Default to guest
            await selectUserAccount('guest');
            return;
        }
        updateUserLabels();
    } catch (e) {
        console.error("Error loading user:", e);
    }
}

async function loadUsers() {
    try {
        const res = await fetch('/api/users/list');
        const data = await res.json();
        state.allUsers = data.users || [];
    } catch (e) {
        console.error("Error loading users:", e);
    }
}

function updateUserLabels() {
    if (!state.currentUser) return;
    const empLabel = document.getElementById('empUserLabel');
    if (empLabel) empLabel.textContent = `Hi, ${state.currentUser.username === 'guest' ? 'Guest' : state.currentUser.full_name.split(' ')[0]}`;

    const kitchenName = document.getElementById('kitchenStaffName');
    if (kitchenName) {
        kitchenName.textContent = state.currentUser.role === 'kitchen' ? state.currentUser.full_name : 'Chef Ramesh';
    }
}

async function selectUserAccount(username) {
    let target = state.allUsers.find(u => u.username === username);
    if (!target) {
        // Fallback by role
        if (username === 'chef') target = state.allUsers.find(u => u.role === 'kitchen');
        else if (username === 'admin') target = state.allUsers.find(u => u.role === 'admin');
        else target = state.allUsers.find(u => u.role === 'employee');
    }
    if (!target) return;

    try {
        const res = await fetch('/api/auth/switch-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: target.id })
        });
        const data = await res.json();
        if (data.status === 'success') {
            state.currentUser = data.user;
            updateUserLabels();

            // Auto-switch view to match role
            if (data.user.role === 'kitchen') switchAppView('kitchen');
            else if (data.user.role === 'admin') switchAppView('admin');
            else switchAppView('employee');

            closeAllDropdowns();
            showToast(`Switched to ${data.user.full_name}`, 'info');
            await refreshAllData();
        }
    } catch (e) {
        console.error("Error switching user:", e);
    }
}

function toggleUserDropdown(id) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden');
}

function closeAllDropdowns() {
    ['empDropdown', 'kitchenTopDropdown'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('#empDropdown') && !e.target.closest('button[onclick*="empDropdown"]')) {
        const el = document.getElementById('empDropdown');
        if (el) el.classList.add('hidden');
    }
    if (!e.target.closest('#kitchenTopDropdown') && !e.target.closest('button[onclick*="kitchenTopDropdown"]')) {
        const el = document.getElementById('kitchenTopDropdown');
        if (el) el.classList.add('hidden');
    }
});

// View Switching
function switchAppView(viewName) {
    state.currentView = viewName;

    // View containers
    const vEmp = document.getElementById('viewEmployeeContainer');
    const vKit = document.getElementById('viewKitchenContainer');
    const vAdm = document.getElementById('viewAdminContainer');

    vEmp.classList.add('hidden');
    vKit.classList.add('hidden');
    vAdm.classList.add('hidden');

    // Nav buttons styling
    const bEmp = document.getElementById('btnViewEmp');
    const bKit = document.getElementById('btnViewKitchen');
    const bAdm = document.getElementById('btnViewAdmin');

    const activeCls = 'bg-emerald-600 text-white shadow-xs';
    const inactiveCls = 'bg-slate-800 text-slate-300 hover:bg-slate-700';

    bEmp.className = `px-3 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${viewName === 'employee' ? activeCls : inactiveCls}`;
    bKit.className = `px-3 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${viewName === 'kitchen' ? activeCls : inactiveCls}`;
    bAdm.className = `px-3 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${viewName === 'admin' ? activeCls : inactiveCls}`;

    if (viewName === 'employee') vEmp.classList.remove('hidden');
    else if (viewName === 'kitchen') vKit.classList.remove('hidden');
    else if (viewName === 'admin') vAdm.classList.remove('hidden');

    refreshAllData();
    lucide.createIcons();
}

function togglePhoneFrame() {
    state.phoneFrameOn = !state.phoneFrameOn;
    const wrapper = document.getElementById('employeePhoneWrapper');
    const label = document.getElementById('phoneFrameLabel');

    if (wrapper) {
        if (state.phoneFrameOn) {
            wrapper.className = "mobile-frame-container w-full bg-[#FAF7F2] flex flex-col justify-between border border-slate-200/60 shadow-xl";
            if (label) label.textContent = "Frame: ON";
        } else {
            wrapper.className = "w-full max-w-4xl mx-auto rounded-3xl bg-[#FAF7F2] flex flex-col justify-between border border-slate-200 shadow-sm";
            if (label) label.textContent = "Frame: OFF";
        }
    }
}

// Master Data Refresh
async function refreshAllData() {
    await Promise.all([
        fetchMenus(),
        fetchAttendanceSummary(),
        fetchMyAttendance()
    ]);

    renderEmployeeCards();
    renderKitchenDashboard();
    if (state.currentView === 'admin') {
        renderAdminDashboard();
    }
    lucide.createIcons();
}

async function fetchMenus() {
    try {
        const res = await fetch(`/api/menus?date_str=${state.selectedDate}`);
        const data = await res.json();
        state.menusData = {};
        if (data.items) {
            data.items.forEach(item => {
                state.menusData[item.slot.id] = item.menu;
            });
        }
    } catch (e) {
        console.error("Error fetching menus:", e);
    }
}

async function fetchAttendanceSummary() {
    try {
        const res = await fetch(`/api/attendance/summary?date_str=${state.selectedDate}`);
        const data = await res.json();
        state.attendanceSummary = data;
    } catch (e) {
        console.error("Error fetching summary:", e);
    }
}

async function fetchMyAttendance() {
    if (!state.currentUser) return;
    try {
        const res = await fetch(`/api/attendance/my?date_str=${state.selectedDate}`);
        if (res.ok) {
            const data = await res.json();
            state.myAttendance = {};
            if (data.items) {
                data.items.forEach(it => {
                    state.myAttendance[it.slot.id] = it;
                });
            }
        }
    } catch (e) {
        console.error("Error fetching my attendance:", e);
    }
}

// =================================================================
// RENDER EMPLOYEE HOME (IMAGE 1)
// =================================================================

function renderEmployeeCards() {
    const slots = ['breakfast', 'lunch', 'dinner'];
    slots.forEach(slot => {
        const menu = state.menusData[slot];
        const att = state.myAttendance[slot];

        // Format items into bullet points
        let items = ['Fresh preparation', 'Seasonal sides', 'Hot beverage'];
        if (menu && menu.main_items) {
            items = menu.main_items.split(',').map(s => s.trim()).filter(Boolean);
        }

        const itemsElId = slot === 'breakfast' ? 'empBfItems' : slot === 'lunch' ? 'empLunchItems' : 'empDinnerItems';
        const itemsEl = document.getElementById(itemsElId);
        if (itemsEl) {
            itemsEl.innerHTML = items.map(it => `
                <li class="flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-slate-800"></span>
                    <span>${it}</span>
                </li>
            `).join('');
        }

        // Image
        const imgElId = slot === 'breakfast' ? 'empBfImage' : slot === 'lunch' ? 'empLunchImage' : 'empDinnerImage';
        const imgEl = document.getElementById(imgElId);
        if (imgEl && menu && menu.image_url) {
            imgEl.src = menu.image_url;
        }

        // Button RSVP state
        const btnTextId = slot === 'breakfast' ? 'btnTextBf' : slot === 'lunch' ? 'btnTextLunch' : 'btnTextDinner';
        const btnTextEl = document.getElementById(btnTextId);
        if (btnTextEl) {
            if (att && att.status === 'not_attending') {
                btnTextEl.textContent = "Skipping (Click to Attend)";
            } else {
                // Default: Will you come?
                btnTextEl.textContent = "Will you come?";
            }
        }
    });
}

function promptMealRsvp(slotId) {
    state.activeRsvpSlot = slotId;
    const titleEl = document.getElementById('modalRsvpTitle');
    const slotName = slotId.charAt(0).toUpperCase() + slotId.slice(1);
    const timeLabel = slotId === 'breakfast' ? '8:45 AM' : slotId === 'lunch' ? '1:00 PM' : '7:00 PM';
    
    if (titleEl) titleEl.textContent = `Will you come for ${slotName}? (${timeLabel})`;

    // Reset skip box
    const skipBox = document.getElementById('modalSkipReasonBox');
    if (skipBox) skipBox.classList.add('hidden');
    document.getElementById('modalSkipReasonInput').value = '';

    document.getElementById('modalEmployeeRsvp').classList.remove('hidden');
    lucide.createIcons();
}

function toggleSkipReasonField() {
    const skipBox = document.getElementById('modalSkipReasonBox');
    if (skipBox.classList.contains('hidden')) {
        skipBox.classList.remove('hidden');
        document.getElementById('modalSkipReasonInput').focus();
    } else {
        // Confirm skip
        confirmEmployeeRsvp('not_attending');
    }
}

function closeEmployeeRsvpModal() {
    state.activeRsvpSlot = null;
    document.getElementById('modalEmployeeRsvp').classList.add('hidden');
}

async function confirmEmployeeRsvp(status) {
    if (!state.activeRsvpSlot) return;
    const slot = state.activeRsvpSlot;
    const reason = document.getElementById('modalSkipReasonInput').value.trim() || (status === 'not_attending' ? 'Opted out' : '');

    try {
        const payload = {
            date: state.selectedDate,
            items: [{
                meal_slot: slot,
                status: status,
                note: reason
            }]
        };

        const res = await fetch('/api/attendance/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            closeEmployeeRsvpModal();
            showToast(status === 'attending' ? `Confirmed: You are attending ${slot.toUpperCase()}!` : `Marked: Skipping ${slot.toUpperCase()}`, status === 'attending' ? 'success' : 'info');
            await refreshAllData();
        }
    } catch (e) {
        console.error("Error saving attendance:", e);
    }
}

// =================================================================
// RENDER KITCHEN STAFF DASHBOARD (IMAGE 2)
// =================================================================

function renderKitchenDashboard() {
    const summary = state.attendanceSummary ? state.attendanceSummary.summary : null;

    const slots = ['breakfast', 'lunch', 'dinner'];
    slots.forEach(slot => {
        const menu = state.menusData[slot];
        const slotSummary = summary ? summary[slot] : null;

        // Serves count (defaults to 45 if full)
        const count = slotSummary ? slotSummary.attending_count : 45;

        // Items list
        let items = ['Poha', 'Boiled Egg', 'Tea'];
        if (slot === 'lunch') items = ['Rice', 'Dal Tadka', 'Mixed Veg', 'Roti', 'Salad'];
        if (slot === 'dinner') items = ['Roti', 'Paneer Sabzi', 'Jeera Rice', 'Salad'];
        if (menu && menu.main_items) {
            items = menu.main_items.split(',').map(s => s.trim()).filter(Boolean);
        }

        const itemsElId = slot === 'breakfast' ? 'kitchenBfItems' : slot === 'lunch' ? 'kitchenLunchItems' : 'kitchenDinnerItems';
        const itemsEl = document.getElementById(itemsElId);
        if (itemsEl) {
            itemsEl.innerHTML = items.map(it => `
                <li class="flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-slate-800"></span>
                    <span>${it}</span>
                </li>
            `).join('');
        }

        // Serves
        const servesElId = slot === 'breakfast' ? 'kitchenBfServes' : slot === 'lunch' ? 'kitchenLunchServes' : 'kitchenDinnerServes';
        const servesEl = document.getElementById(servesElId);
        if (servesEl) servesEl.textContent = count;

        // Pill and Cooking Status Text
        const pillId = slot === 'breakfast' ? 'kitchenBfPill' : slot === 'lunch' ? 'kitchenLunchPill' : 'kitchenDinnerPill';
        const pillEl = document.getElementById(pillId);
        const statusTextId = slot === 'breakfast' ? 'kitchenBfStatusText' : slot === 'lunch' ? 'kitchenLunchStatusText' : 'kitchenDinnerStatusText';
        const statusTextEl = document.getElementById(statusTextId);

        let prepStatus = menu ? menu.prep_status : (slot === 'breakfast' ? 'Ready to Serve' : slot === 'lunch' ? 'In Progress' : 'Not Started');
        let cookingState = menu ? menu.cooking_state : (slot === 'breakfast' ? 'Completed' : slot === 'lunch' ? 'Cooking' : 'Not Started');

        if (pillEl) {
            pillEl.textContent = prepStatus;
            if (prepStatus === 'Ready to Serve') pillEl.className = "bg-[#44A63B] text-white text-[11px] font-bold px-3 py-1 rounded-full shadow-2xs";
            else if (prepStatus === 'In Progress') pillEl.className = "bg-[#EE8125] text-white text-[11px] font-bold px-3 py-1 rounded-full shadow-2xs";
            else pillEl.className = "bg-[#829DB8] text-white text-[11px] font-bold px-3 py-1 rounded-full shadow-2xs";
        }

        if (statusTextEl) {
            statusTextEl.textContent = cookingState;
        }
    });

    // Quick counts box
    const totalBf = summary && summary.breakfast ? summary.breakfast.attending_count : 45;
    const totalLu = summary && summary.lunch ? summary.lunch.attending_count : 45;
    const totalDi = summary && summary.dinner ? summary.dinner.attending_count : 45;

    document.getElementById('countBf').textContent = totalBf;
    document.getElementById('countLunch').textContent = totalLu;
    document.getElementById('countDinner').textContent = totalDi;
}

// Toggle cooking status directly from card
async function toggleCookingStatus(slot) {
    const menu = state.menusData[slot];
    let current = menu ? menu.prep_status : 'Not Started';

    let nextPrep = 'Ready to Serve';
    let nextState = 'Completed';

    if (current === 'Ready to Serve') {
        nextPrep = 'In Progress';
        nextState = 'Cooking';
    } else if (current === 'In Progress') {
        nextPrep = 'Not Started';
        nextState = 'Not Started';
    } else {
        nextPrep = 'Ready to Serve';
        nextState = 'Completed';
    }

    try {
        const res = await fetch('/api/menus/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: state.selectedDate,
                meal_slot: slot,
                prep_status: nextPrep,
                cooking_state: nextState
            })
        });
        if (res.ok) {
            showToast(`${slot.toUpperCase()} status updated to: ${nextPrep}`, 'success');
            await refreshAllData();
        }
    } catch (e) {
        console.error("Error updating status:", e);
    }
}

// Kitchen Menu Modal
function openMenuEditModal(slot) {
    document.getElementById('editMenuSlot').value = slot;
    const menu = state.menusData[slot];
    document.getElementById('editMenuItems').value = menu ? menu.main_items : '';
    document.getElementById('editPrepStatus').value = menu ? menu.prep_status : 'Ready to Serve';
    document.getElementById('editCookingState').value = menu ? menu.cooking_state : 'Completed';

    document.getElementById('modalKitchenMenuEdit').classList.remove('hidden');
    lucide.createIcons();
}

function closeKitchenMenuModal() {
    document.getElementById('modalKitchenMenuEdit').classList.add('hidden');
}

async function submitKitchenMenu(e) {
    e.preventDefault();
    const slot = document.getElementById('editMenuSlot').value;
    const items = document.getElementById('editMenuItems').value.trim();
    const prep = document.getElementById('editPrepStatus').value;
    const cook = document.getElementById('editCookingState').value;

    try {
        const res = await fetch('/api/menus/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: state.selectedDate,
                meal_slot: slot,
                main_items: items,
                prep_status: prep,
                cooking_state: cook
            })
        });
        if (res.ok) {
            showToast("Menu and status saved successfully!", 'success');
            closeKitchenMenuModal();
            await refreshAllData();
        }
    } catch (e) {
        console.error("Error saving menu:", e);
    }
}

// Ingredients prep calculator modal
function openIngredientsModal() {
    const summary = state.attendanceSummary ? state.attendanceSummary.summary : null;
    const count = summary && summary.lunch ? summary.lunch.attending_count : 45;

    const listEl = document.getElementById('ingredientsListContainer');
    if (listEl) {
        listEl.innerHTML = `
            <div class="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span class="text-slate-500 font-semibold block text-[11px]">Raw Basmati Rice</span>
                <span class="text-lg font-black text-emerald-700 mt-0.5 block">${(count * 0.08).toFixed(1)} kg</span>
                <span class="text-[10px] text-slate-400">Yields ~150g cooked / plate</span>
            </div>
            <div class="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span class="text-slate-500 font-semibold block text-[11px]">Toor Dal / Lentils</span>
                <span class="text-lg font-black text-emerald-700 mt-0.5 block">${(count * 0.05).toFixed(1)} kg</span>
                <span class="text-[10px] text-slate-400">Yields ${(count * 0.14).toFixed(1)} L dal</span>
            </div>
            <div class="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span class="text-slate-500 font-semibold block text-[11px]">Whole Wheat Atta (Roti)</span>
                <span class="text-lg font-black text-emerald-700 mt-0.5 block">${(count * 0.09).toFixed(1)} kg</span>
                <span class="text-[10px] text-slate-400">${count * 3} rotis total</span>
            </div>
            <div class="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span class="text-slate-500 font-semibold block text-[11px]">Fresh Vegetables / Paneer</span>
                <span class="text-lg font-black text-emerald-700 mt-0.5 block">${(count * 0.16).toFixed(1)} kg</span>
                <span class="text-[10px] text-slate-400">Curry & subzi</span>
            </div>
            <div class="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span class="text-slate-500 font-semibold block text-[11px]">Eggs / Breakfast Special</span>
                <span class="text-lg font-black text-emerald-700 mt-0.5 block">${count * 2} pcs</span>
                <span class="text-[10px] text-slate-400">Boiled or scrambled</span>
            </div>
            <div class="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span class="text-slate-500 font-semibold block text-[11px]">Tea / Coffee / Milk</span>
                <span class="text-lg font-black text-emerald-700 mt-0.5 block">${(count * 0.15).toFixed(1)} L</span>
                <span class="text-[10px] text-slate-400">Hot beverage serving</span>
            </div>
        `;
    }

    document.getElementById('modalIngredientsPrep').classList.remove('hidden');
    lucide.createIcons();
}

function closeIngredientsModal() {
    document.getElementById('modalIngredientsPrep').classList.add('hidden');
}

function printPrepSheet() {
    const s = state.attendanceSummary ? state.attendanceSummary.summary : null;
    const printArea = document.getElementById('printableKitchenSheet');
    if (!printArea) return;

    printArea.innerHTML = `
        <div style="font-family: sans-serif; padding: 24px;">
            <div style="border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 24px;">FOOD MANAGER - KITCHEN PREPARATION SHEET</h1>
                <p style="margin: 4px 0 0 0; font-size: 13px; color: #555;">Date: <strong>${state.selectedDate}</strong> | Confirmed Roster</p>
            </div>
            <div style="display: flex; gap: 20px; margin-bottom: 25px;">
                <div style="flex: 1; border: 1px solid #ddd; padding: 12px; border-radius: 8px;">
                    <h3 style="margin: 0 0 8px 0;">BREAKFAST (8:45 AM)</h3>
                    <p style="font-size: 20px; margin: 0; font-weight: bold;">Serves: ${s && s.breakfast ? s.breakfast.attending_count : 45}</p>
                    <p style="font-size: 12px; color: #666;">Status: ${s && s.breakfast && s.breakfast.menu ? s.breakfast.menu.prep_status : 'Ready to Serve'}</p>
                </div>
                <div style="flex: 1; border: 1px solid #ddd; padding: 12px; border-radius: 8px;">
                    <h3 style="margin: 0 0 8px 0;">LUNCH (1:00 PM)</h3>
                    <p style="font-size: 20px; margin: 0; font-weight: bold;">Serves: ${s && s.lunch ? s.lunch.attending_count : 45}</p>
                    <p style="font-size: 12px; color: #666;">Status: ${s && s.lunch && s.lunch.menu ? s.lunch.menu.prep_status : 'In Progress'}</p>
                </div>
                <div style="flex: 1; border: 1px solid #ddd; padding: 12px; border-radius: 8px;">
                    <h3 style="margin: 0 0 8px 0;">DINNER (7:00 PM)</h3>
                    <p style="font-size: 20px; margin: 0; font-weight: bold;">Serves: ${s && s.dinner ? s.dinner.attending_count : 45}</p>
                    <p style="font-size: 12px; color: #666;">Status: ${s && s.dinner && s.dinner.menu ? s.dinner.menu.prep_status : 'Not Started'}</p>
                </div>
            </div>
        </div>
    `;

    window.print();
}

// =================================================================
// RENDER ADMIN DASHBOARD
// =================================================================

async function renderAdminDashboard() {
    try {
        const resStats = await fetch(`/api/admin/stats?date_str=${state.selectedDate}`);
        const stats = await resStats.json();

        document.getElementById('kpiTotalStaff').textContent = stats.total_employees || 45;
        
        let confirmed = 0;
        if (state.attendanceSummary && state.attendanceSummary.summary) {
            const sm = state.attendanceSummary.summary;
            confirmed += (sm.breakfast ? sm.breakfast.attending_count : 45);
            confirmed += (sm.lunch ? sm.lunch.attending_count : 45);
            confirmed += (sm.dinner ? sm.dinner.attending_count : 45);
        } else {
            confirmed = 135;
        }
        document.getElementById('kpiConfirmedMeals').textContent = confirmed;
        document.getElementById('kpiOptOuts').textContent = stats.today_opt_outs || 0;
        document.getElementById('kpiSavings').textContent = `₹${(stats.estimated_savings_rupees || 0).toLocaleString()}`;

        // Chart
        renderAdminChart(stats.trend_7_days || []);

        // Depts
        renderAdminDepts(stats.departments || []);

        // Users
        renderAdminUsersTable();
    } catch (e) {
        console.error("Error rendering admin:", e);
    }
}

function renderAdminChart(trendData) {
    const ctx = document.getElementById('adminTrendChart');
    if (!ctx) return;

    if (state.trendChartInstance) {
        state.trendChartInstance.destroy();
    }

    const labels = trendData.map(d => d.display);
    const servings = trendData.map(d => d.servings);
    const optOuts = trendData.map(d => d.opt_outs);

    state.trendChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Plates Served (Attended)',
                    data: servings,
                    backgroundColor: '#136B39',
                    borderRadius: 6
                },
                {
                    label: 'Plates Saved (Opted-Out)',
                    data: optOuts,
                    backgroundColor: '#EE8125',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true, grid: { display: false } },
                y: { stacked: true, grid: { color: '#f1f5f9' }, beginAtZero: true }
            },
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
            }
        }
    });
}

function renderAdminDepts(depts) {
    const el = document.getElementById('adminDeptList');
    if (!el) return;
    const total = depts.reduce((acc, d) => acc + d.count, 0) || 45;

    el.innerHTML = depts.map(d => {
        const pct = Math.round((d.count / total) * 100);
        return `
            <div>
                <div class="flex items-center justify-between text-xs mb-1">
                    <span class="font-semibold text-slate-700">${d.department}</span>
                    <span class="text-slate-500 font-bold">${d.count} (${pct}%)</span>
                </div>
                <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-emerald-600 h-full rounded-full" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

function renderAdminUsersTable() {
    const tbody = document.getElementById('adminUserTbody');
    if (!tbody) return;

    tbody.innerHTML = state.allUsers.map(u => `
        <tr class="hover:bg-slate-50">
            <td class="px-6 py-3 font-bold text-slate-900">${u.full_name} <span class="text-[10px] text-slate-400 font-normal">(@${u.username})</span></td>
            <td class="px-6 py-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${u.role==='kitchen'?'bg-amber-100 text-amber-800':u.role==='admin'?'bg-purple-100 text-purple-800':'bg-emerald-100 text-emerald-800'}">${u.role}</span></td>
            <td class="px-6 py-3 text-slate-500">${u.department || 'General'}</td>
            <td class="px-6 py-3 font-semibold text-emerald-700">${u.dietary_preference || 'Regular'}</td>
            <td class="px-6 py-3 text-right">
                <span class="inline-flex items-center gap-1 text-[11px] text-emerald-700 font-semibold">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Active
                </span>
            </td>
        </tr>
    `).join('');
}

function filterAdminUserTable() {
    const q = document.getElementById('adminUserSearch').value.toLowerCase();
    const rows = document.getElementById('adminUserTbody').getElementsByTagName('tr');
    for (let r of rows) {
        r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    }
}

function downloadCSVReport() {
    window.location.href = `/api/admin/export-csv?date_str=${state.selectedDate}`;
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    let colorClass = 'bg-[#0C2329] text-white shadow-xl';
    let icon = 'info';

    if (type === 'success') {
        colorClass = 'bg-[#136B39] text-white shadow-lg';
        icon = 'check-circle-2';
    } else if (type === 'error') {
        colorClass = 'bg-rose-700 text-white shadow-lg';
        icon = 'alert-triangle';
    }

    toast.className = `flex items-center gap-2.5 px-4 py-3 rounded-2xl text-xs font-semibold transform transition-all duration-300 translate-y-2 opacity-0 pointer-events-auto ${colorClass}`;
    toast.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4 shrink-0"></i> <span>${message}</span>`;

    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
