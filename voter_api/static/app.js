const API_BASE = "";
let currentSurveyId = null;
let chartInstance = null;
// --- AUTH STATE ---
let CURRENT_USER = {
    role: null, // 'ADMIN' or 'COORDINATOR'
    mobile: null,
    village_id: null,
    village_name: null,
    token: null // For Admin
};

document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin/Coord Dashboard Loaded");

    // Check Session
    const session = localStorage.getItem('ec_session');
    if (session) {
        CURRENT_USER = JSON.parse(session);
        showDashboard();
    } else {
        // Show Login (Default)
        selectRole('ADMIN'); // Default Valid Tab
    }

    // Attach listener for assignment tab
    const assignSelect = document.getElementById('assignment-survey-select');
    if (assignSelect) {
        assignSelect.addEventListener('change', fetchAssignmentData);
    }
});

function selectRole(role) {
    const adminBtn = document.getElementById('btn-role-admin');
    const coordBtn = document.getElementById('btn-role-coordinator');
    const adminForm = document.getElementById('admin-login-form');
    const coordForm = document.getElementById('coordinator-login-form');
    const errorP = document.getElementById('login-error');

    errorP.style.display = 'none';

    if (role === 'ADMIN') {
        adminBtn.style.background = '#2563eb'; adminBtn.style.color = 'white';
        coordBtn.style.background = '#e5e7eb'; coordBtn.style.color = '#374151';
        adminForm.style.display = 'block';
        coordForm.style.display = 'none';
    } else {
        coordBtn.style.background = '#2563eb'; coordBtn.style.color = 'white';
        adminBtn.style.background = '#e5e7eb'; adminBtn.style.color = '#374151';
        coordForm.style.display = 'block';
        adminForm.style.display = 'none';
    }
}

async function handleLogin() {
    const errorP = document.getElementById('login-error');
    errorP.style.display = 'none';

    const adminFormVisible = document.getElementById('admin-login-form').style.display !== 'none';

    if (adminFormVisible) {
        // ADMIN LOGIN
        const secret = document.getElementById('adminSecret').value;
        if (secret === 'admin-secret-123') { // Hardcoded for Phase 1-5 as per plan
            CURRENT_USER = { role: 'ADMIN', token: secret };
            saveSession();
            showDashboard();
        } else {
            errorP.textContent = "Invalid Admin Secret Key";
            errorP.style.display = 'block';
        }
    } else {
        // COORDINATOR LOGIN
        const mobile = document.getElementById('coordMobile').value;
        if (!mobile) {
            errorP.textContent = "Please enter mobile number";
            errorP.style.display = 'block';
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mobile_no: mobile })
            });
            const data = await res.json();

            if (res.ok && data.status === 'success') {
                CURRENT_USER = {
                    role: 'COORDINATOR',
                    mobile: mobile,
                    village_id: data.village_id,
                    village_name: data.village_name,
                    mandal_name: data.mandal_name,   // NEW
                    district_name: data.district_name, // NEW
                    name: data.name // Added Name
                };
                saveSession();
                showDashboard();
            } else {
                errorP.textContent = data.detail || "Login Failed. Verify you are an approved Coordinator.";
                errorP.style.display = 'block';
            }
        } catch (e) {
            console.error(e);
            errorP.textContent = "Connection Error";
            errorP.style.display = 'block';
        }
    }
}

function saveSession() {
    localStorage.setItem('ec_session', JSON.stringify(CURRENT_USER));
}

function logout() {
    localStorage.removeItem('ec_session');
    location.reload();
}

function showDashboard() {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('dashboard-container').style.display = 'flex'; // It's flex in CSS usually? Or block. 
    // Actually the body has no layout, but app-container has flex typically? 
    // Let's check CSS if needed, but 'block' or 'flex' is fine.
    // Original app-container display property...
    document.getElementById('dashboard-container').style.display = 'flex';

    // APPLY ROLE RESTRICTIONS
    if (CURRENT_USER.role === 'COORDINATOR') {
        // Hide Restricted Tabs
        // document.querySelector('[data-tab="assignments"]').style.display = 'none'; // NOW ENABLED
        document.querySelector('[data-tab="surveys"]').style.display = 'none';

        // Rename Approvals to "My Team"
        const appTab = document.querySelector('[data-tab="approvals"]');
        appTab.innerHTML = '<span class="icon">ðŸ‘¥</span> My Team';

        // Rename Assignments to "Assign Team" to be clear
        const assignTab = document.querySelector('[data-tab="assignments"]');
        assignTab.innerHTML = '<span class="icon">âš™ï¸</span> Assign Team';

        // Add Logout Button to Sidebar? 
        // Or just header...
    }

    // Update User Display
    const userDisplay = document.getElementById('user-display');
    if (userDisplay) {
        let displayRole = CURRENT_USER.role;
        if (displayRole === 'COORDINATOR') displayRole = `COORD: ${CURRENT_USER.village_name || ''}`;
        userDisplay.innerHTML = `<strong>${CURRENT_USER.name || displayRole}</strong><br><small>${displayRole}</small>`;
    }

    // Load Data
    loadSurveys();
    loadApprovals(); // Logic inside will handle filtering

    if (CURRENT_USER.role === 'ADMIN') {
        loadSurveyList();
        // Show Add Coordinator Button
        const addBtn = document.getElementById('btn-add-coordinator');
        if (addBtn) addBtn.style.display = 'block';
    }
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    document.getElementById(`${tabId}-tab`).classList.add('active');
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');

    document.getElementById('page-title').textContent = tabId.charAt(0).toUpperCase() + tabId.slice(1);

    if (tabId === 'assignments') {
        loadAssignmentOptions(); // Refresh options when tab opens
    }
}

async function loadSurveys() {
    try {
        let url = `${API_BASE}/surveys/active`;

        // --- ADD COORDINATOR FILTER ---
        if (CURRENT_USER.role === 'COORDINATOR' && CURRENT_USER.village_name) {
            url += `?village_filter=${encodeURIComponent(CURRENT_USER.village_name)}`;
            if (CURRENT_USER.mandal_name) url += `&mandal_filter=${encodeURIComponent(CURRENT_USER.mandal_name)}`;
            if (CURRENT_USER.district_name) url += `&district_filter=${encodeURIComponent(CURRENT_USER.district_name)}`;
        }
        // ------------------------------

        const res = await fetch(url);
        if (!res.ok) return;
        const surveys = await res.json();

        const select = document.getElementById('surveySelect');
        if (!select) return;

        select.innerHTML = '';

        if (surveys.length > 0) {
            surveys.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.name;
                select.appendChild(opt);
            });
            currentSurveyId = surveys[0].id;
            loadDashboardData();
        } else {
            select.innerHTML = '<option>No Active Surveys</option>';
        }
    } catch (e) { console.error(e); }
}

async function loadDashboardData() {
    currentSurveyId = document.getElementById('surveySelect').value;
    if (!currentSurveyId) return;

    // Get Filters
    const ward = document.getElementById('filterWard').value;
    // const age = document.getElementById('filterAge').value; // Phase 2 Backend Support needed
    // const gender = document.getElementById('filterGender').value;

    let queryParams = `?survey_id=${currentSurveyId}`;
    if (ward) queryParams += `&ward=${ward}`;

    try {
        // Summary
        const sumRes = await fetch(`${API_BASE}/dashboard/summary${queryParams}`);
        const summary = (await sumRes.json()).data;

        document.getElementById('totalVoters').textContent = summary.total_voters;
        document.getElementById('effectiveVoters').textContent = summary.effective_voters;
        document.getElementById('completedSurveys').textContent = summary.completed_surveys;
        document.getElementById('completionPercentage').textContent = `${summary.completion_percentage}%`;

        // Progress (Always Ward Wise so no filter needed essentially, or filter filters the list)
        const progRes = await fetch(`${API_BASE}/dashboard/progress?survey_id=${currentSurveyId}`);
        const progress = (await progRes.json()).data;

        // Filter Progress Table locally if Ward selected
        const filteredProgress = ward ? progress.filter(p => p.ward_no == ward) : progress;

        const progBody = document.getElementById('progressTableBody');
        progBody.innerHTML = filteredProgress.map(p => `
            <tr>
                <td>Ward ${p.ward_no}</td>
                <td>${p.completed} / ${p.effective_voters}</td>
                <td>${p.total_voters}</td>
                <td><span class="badge" style="background:${p.status === 'COMPLETED' ? '#10b981' : '#f59e0b'}">${p.status}</span></td>
            </tr>
        `).join('');

        // Analytics (Apply same filters)
        const analRes = await fetch(`${API_BASE}/dashboard/analytics${queryParams}`);
        const analytics = (await analRes.json()).data;

        renderChart(analytics);
    } catch (e) { console.error(e); }
}

function renderChart(data) {
    const ctx = document.getElementById('analyticsChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    // PARTY COLORS MAPPING
    const partyColors = {
        'TRS': '#FF00FF', // Pink
        'BRS': '#FF00FF', // Pink
        'INC': '#0000FF', // Blue
        'CONGRESS': '#0000FF',
        'BJP': '#FF9933', // Saffron
        'CPM': '#FF0000', // Red
        'CPI': '#FF5252',
        'AIMIM': '#008000', // Green
        'TDP': '#FFFF00', // Yellow
        'OTHER': '#808080' // Grey
    };

    const bgColors = data.map(d => {
        const party = d.party ? d.party.toUpperCase().trim() : 'OTHER';
        return partyColors[party] || '#808080';
    });

    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.party),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: bgColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}
// --- ADD COORDINATOR FEATURES ---

function openAddCoordinatorModal() {
    const modal = document.getElementById('addCoordinatorModal');
    modal.style.display = 'block';

    // Load Districts if empty
    const distSelect = document.getElementById('coord-district');
    if (distSelect.options.length <= 1) {
        fetch(`${API_BASE}/locations/districts`)
            .then(res => res.json())
            .then(data => {
                distSelect.innerHTML = '<option value="">Select District</option>';
                data.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.id;
                    opt.textContent = d.name;
                    distSelect.appendChild(opt);
                });
            });
    }
}

function closeAddCoordinatorModal() {
    document.getElementById('addCoordinatorModal').style.display = 'none';
}

async function loadCoordMandals() {
    const distId = document.getElementById('coord-district').value;
    const mandalSelect = document.getElementById('coord-mandal');
    mandalSelect.innerHTML = '<option value="">Loading...</option>';

    if (!distId) return;

    try {
        const res = await fetch(`${API_BASE}/locations/mandals/${distId}`);
        const data = await res.json();
        mandalSelect.innerHTML = '<option value="">Select Mandal</option>';
        data.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = m.name;
            mandalSelect.appendChild(opt);
        });
    } catch (e) { }
}

async function loadCoordVillages() {
    const mandalId = document.getElementById('coord-mandal').value;
    const villageSelect = document.getElementById('coord-village');
    villageSelect.innerHTML = '<option value="">Loading...</option>';

    if (!mandalId) return;

    try {
        const res = await fetch(`${API_BASE}/locations/villages/${mandalId}`);
        const data = await res.json();
        villageSelect.innerHTML = '<option value="">Select Village</option>';
        data.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = v.name;
            villageSelect.appendChild(opt);
        });
    } catch (e) { }
}

async function createCoordinator() {
    const name = document.getElementById('coord-name').value;
    const mobile = document.getElementById('coord-mobile').value;

    // Location
    const distSelect = document.getElementById('coord-district');
    const mandalSelect = document.getElementById('coord-mandal');
    const villageSelect = document.getElementById('coord-village');

    const distName = distSelect.options[distSelect.selectedIndex]?.text;
    const mandalName = mandalSelect.options[mandalSelect.selectedIndex]?.text;
    const villageName = villageSelect.options[villageSelect.selectedIndex]?.text;
    const villageId = villageSelect.value;

    if (!name || !mobile || !villageId) {
        alert("Please fill all fields (Name, Mobile, Village)");
        return;
    }

    // 1. Register as COORDINATOR
    const payload = {
        name: name,
        mobile: mobile,
        district_name: distName,
        mandal_name: mandalName,
        village_name: villageName,
        ward_no: "0", // Default
        role: "COORDINATOR",
        village_id: parseInt(villageId)
    };

    try {
        // Register
        const res1 = await fetch(`${API_BASE}/register/surveyor`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data1 = await res1.json();

        if (data1.status === 'success' || data1.status === 'exists') {
            const reqId = data1.id;

            // 2. Approve Immediately
            const res2 = await fetch(`${API_BASE}/dashboard/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request_id: reqId, action: 'APPROVED' })
            });

            alert(`Success! Coordinator '${name}' (Mobile: ${mobile}) created and approved.`);
            closeAddCoordinatorModal();
            loadApprovals(); // Refresh list
        } else {
            alert("Failed to create coordinator. " + JSON.stringify(data1));
        }

    } catch (e) {
        console.error(e);
        alert("Error creating coordinator");
    }
}

async function loadApprovals() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/approvals`);
        let allRequests = await res.json();

        // --- FILTER FOR COORDINATOR ---
        if (CURRENT_USER.role === 'COORDINATOR') {
            // Only show requests for my village
            // Using lowercase comparison for safety
            const myVillage = (CURRENT_USER.village_name || "").toLowerCase().trim();
            allRequests = allRequests.filter(a => (a.village || "").toLowerCase().trim() === myVillage);
        }
        // -----------------------------

        // Split Data
        const pending = allRequests.filter(a => a.status === 'PENDING');
        const history = allRequests.filter(a => a.status !== 'PENDING');

        // 1. Render Pending
        document.getElementById('approvalsTableBody').innerHTML = pending.map(a => `
            <tr>
                <td>${a.id}</td>
                <td>${a.name}
                    ${a.role === 'COORDINATOR' ? '<br><span class="badge" style="background:#8b5cf6">COORDINATOR</span>' : ''}
                </td>
                <td>${a.mobile}</td>
                <td><small>${a.district || '-'}<br>${a.mandal || '-'}<br>${a.village || '-'}<br>Ward ${a.ward || '-'}</small></td>
                <td>${new Date(a.date).toLocaleDateString()}</td>
                <td>
                    <button class="btn-approve" onclick="handleApproval(${a.id}, 'APPROVED')">Approve</button>
                    <button class="btn-reject" onclick="handleApproval(${a.id}, 'REJECTED')">Reject</button>
                    ${CURRENT_USER.role === 'ADMIN' ? `<button class="btn btn-sm btn-danger ms-2" style="background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px;" onclick="deleteSurveyor(${a.id})">Delete</button>` : ''}
                </td>
            </tr>
        `).join('');

        // 2. Render History
        const historyBody = document.getElementById('approvalsHistoryTableBody');
        if (historyBody) {
            historyBody.innerHTML = history.map(a => `
                <tr>
                    <td>${a.id}</td>
                    <td>${a.name} 
                        ${a.role === 'COORDINATOR' ? '<br><span class="badge" style="background:#8b5cf6">COORDINATOR</span>' : ''}
                    </td>
                    <td>${a.mobile}</td>
                    <td><small>${a.district || '-'}<br>${a.mandal || '-'}<br>${a.village || '-'}<br>Ward ${a.ward || '-'}</small></td>
                    <td>${a.assigned_survey || '-'}</td>
                    <td>${new Date(a.date).toLocaleDateString()}</td>
                    <td>
                        <span class="badge" style="background:${a.status === 'APPROVED' ? '#10b981' : (a.status === 'REJECTED' ? '#ef4444' : '#6b7280')}">${a.status || 'PENDING'}</span>
                        ${CURRENT_USER.role === 'ADMIN' ? `<button class="btn btn-sm btn-danger ms-2" style="background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; margin-left: 10px;" onclick="deleteSurveyor(${a.id})">Delete</button>` : ''}
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error("Error loading approvals", e);
    }
}

async function handleApproval(id, action) {
    await fetch(`${API_BASE}/dashboard/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: id, action: action })
    });
    loadApprovals();
    // Also REFRESH the assignment dropdowns if we just approved someone!
    if (action === 'APPROVED') loadAssignmentOptions();
}

async function deleteSurveyor(id) {
    if (!confirm("Are you sure you want to delete this surveyor? This will also remove their survey assignments.")) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/dashboard/surveyor/${id}`, {
            method: 'DELETE'
        });
        const data = await res.json();

        if (data.status === 'success') {
            alert(data.message);
            loadApprovals(); // Refresh table
            loadAssignmentOptions(); // Refresh dropdowns
        } else {
            alert("Error: " + data.message);
        }
    } catch (e) {
        console.error("Error deleting surveyor:", e);
        alert("Failed to delete surveyor");
    }
}


function showCreateSurveyModal() {
    document.getElementById('createModal').style.display = 'flex';
    loadDistricts(); // Fetch districts when modal opens
}

function closeModal() { document.getElementById('createModal').style.display = 'none'; }

// --- LOCATION LOGIC ---

async function loadDistricts() {
    try {
        console.log("Fetching districts...");
        const res = await fetch(`${API_BASE}/locations/districts`);
        if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);

        const districts = await res.json();
        console.log("Districts loaded:", districts);

        const select = document.getElementById('scope-district');
        if (!select) return alert("UI Error: Cannot find District Dropdown");

        select.innerHTML = '<option value="">Select District</option>';

        if (districts.length === 0) {
            // alert("DEBUG: API returned 0 districts. Did you click Initialize Data?");
            select.innerHTML += '<option disabled>No Districts Found (Try Initialize)</option>';
        } else {
            districts.forEach(d => {
                select.innerHTML += `<option value="${d.id}">${d.name}</option>`;
            });
            // Auto select if only one (UX improvement)
            if (districts.length === 1) select.value = districts[0].id;
        }

    } catch (e) {
        console.error("Error loading districts", e);
        alert("Failed to load districts: " + e.message);
    }
}

async function loadDistrictMandals(distId) {
    if (!distId) return;
    try {
        const res = await fetch(`${API_BASE}/locations/mandals/${distId}`);
        const mandals = await res.json();

        // Populate Checklist
        const container = document.getElementById('mandal-list-container');
        container.innerHTML = mandals.map(m => `
            <div>
                <label>
                    <input type="checkbox" class="mandal-check" value="${m.id}" onchange="refreshVillages()"> 
                    ${m.name}
                </label>
            </div>
        `).join('');

        // Show Mandal Section
        document.getElementById('section-mandal').style.display = 'block';

        // Reset Villages
        document.getElementById('section-village').style.display = 'none';

        // Trigger generic update (defaults to ALL)
        refreshVillages();
    } catch (e) { console.error(e); }
}

function toggleMandalMode() {
    const mode = document.querySelector('input[name="mandalMode"]:checked').value;
    const list = document.getElementById('mandal-list-container');
    if (mode === 'SPECIFIC') {
        list.style.display = 'block';
    } else {
        list.style.display = 'none';
        refreshVillages(); // "All" selected
    }
}

async function refreshVillages() {
    // 1. Determine Scope of Mandals
    const distId = document.getElementById('scope-district').value;
    if (!distId) return;

    const mandalMode = document.querySelector('input[name="mandalMode"]:checked').value;
    let mandalIds = [];

    if (mandalMode === 'SPECIFIC') {
        const checks = document.querySelectorAll('.mandal-check:checked');
        if (checks.length === 0) {
            document.getElementById('village-list-container').innerHTML = '<div style="padding:10px;">Select at least one Mandal</div>';
            return;
        }
        mandalIds = Array.from(checks).map(c => c.value);
    } else {
        // "ALL" - we need to fetch all mandal IDs for this district? 
        // Actually, for "ALL", we can just pass "ALL" to the VILLAGE fetch if the API supports it?
        // Our /locations/villages API takes a single mandal_id usually. 
        // Let's check main.py. It has /locations/villages/{mandal_id} which returns villages for ONE mandal.
        // We might need a bulk endpoint or just fetch for all mandals if "SPECIFIC" is small.
        // BUT wait, create_survey API accepts "ALL". 
        // For UI display of villages, if "All Mandals" is selected, listing ALL villages of a district is HUGE (hundreds).
        // So maybe we hide the specific village list if "All Mandals" is selected?
        // YES. If "All Mandals", we assume "All Villages" by default or force it.
        // Let's simplify: If "All Mandals", we enable "All Villages" and hide specific list.
    }

    document.getElementById('section-village').style.display = 'block';
    // Update summary text
    updateSummary();
}

function toggleVillageMode() {
    const mode = document.querySelector('input[name="villageMode"]:checked').value;
    const list = document.getElementById('village-list-container');

    if (mode === 'SPECIFIC') {
        // Check if we can show list
        const mandalMode = document.querySelector('input[name="mandalMode"]:checked').value;
        if (mandalMode === 'ALL') {
            alert("To select specific villages, please select specific Mandals first (to avoid loading too many villages).");
            document.querySelector('input[name="villageMode"][value="ALL"]').checked = true;
            return;
        }

        list.style.display = 'block';
        loadSpecificVillages();
    } else {
        list.style.display = 'none';
    }
    updateSummary();
}

async function loadSpecificVillages() {
    const list = document.getElementById('village-list-container');
    list.innerHTML = 'Loading...';

    const mChecks = document.querySelectorAll('.mandal-check:checked');
    const mandalIds = Array.from(mChecks).map(c => c.value);

    // Fetch for each mandal
    let allVillages = [];
    for (const mid of mandalIds) {
        try {
            const res = await fetch(`${API_BASE}/locations/villages/${mid}`);
            const villages = await res.json();
            allVillages = allVillages.concat(villages);
        } catch (e) { }
    }

    list.innerHTML = allVillages.map(v => `
        <div>
            <label>
                <input type="checkbox" class="village-check" value="${v.id}" onchange="updateSummary()"> 
                ${v.name}
            </label>
        </div>
    `).join('');
}

function updateSummary() {
    const distText = document.getElementById('scope-district').options[document.getElementById('scope-district').selectedIndex]?.text || "None";
    const mandalMode = document.querySelector('input[name="mandalMode"]:checked').value;
    const villageMode = document.querySelector('input[name="villageMode"]:checked').value;

    let text = `District: ${distText}. `;

    if (mandalMode === 'ALL') text += "All Mandals. ";
    else {
        const count = document.querySelectorAll('.mandal-check:checked').length;
        text += `${count} Mandals. `;
    }

    if (villageMode === 'ALL') text += "All Villages (Auto-Wards).";
    else {
        const count = document.querySelectorAll('.village-check:checked').length;
        text += `${count} Villages (Auto-Wards).`;
    }

    document.getElementById('summary-text').textContent = text;
    document.getElementById('coverage-summary').style.display = 'block';
}



async function seedGeoData() {
    if (!confirm("Initialize Data: This will attempt to seed the database again. Continue?")) return;
    try {
        const res = await fetch(`${API_BASE}/admin/seed_geo`, {
            method: 'POST',
            headers: { 'X-Admin-Token': 'admin-secret-123' }
        });
        const data = await res.json();

        // Show detailed message from server
        alert(`Server Says:\n${data.message}`);

        // Auto-Verify by calling debug endpoint
        try {
            const diffRes = await fetch(`${API_BASE}/debug/geo`);
            const diffData = await diffRes.json();
            console.log("Debug Data:", diffData);
            if (diffData.district_count > 0) {
                alert(`Verification Success: Found ${diffData.district_count} Districts.`);
            } else {
                alert(`Verification Warning: Still 0 Districts found.`);
            }
        } catch (err) {
            console.warn("Debug check failed", err);
        }

        location.reload();
    } catch (e) {
        console.error(e);
        alert(`Failed to connect to API: ${e.message}`);
    }
}

async function createSurvey() {
    const name = document.getElementById('newSurveyName').value;
    if (!name) return alert("Enter Survey Name");

    const districtId = document.getElementById('scope-district').value;
    if (!districtId) return alert("Select a District");

    // Check if new UI elements exist (Coverage Selector)
    const mandalModeEl = document.querySelector('input[name="mandalMode"]:checked');

    // Fallback or Error if UI not ready
    if (!mandalModeEl) {
        return alert("UI Error: Coverage Selector not initialized. Refresh page.");
    }

    const mandalMode = mandalModeEl.value;
    const villageMode = document.querySelector('input[name="villageMode"]:checked').value;

    // Prepare Payload
    let payload = {
        name: name,
        district_id: parseInt(districtId),
        scope_type: "CUSTOM", // Backend logic will infer intent or we pass it
        survey_type: "TEST"
    };

    // Calc Mandals
    if (mandalMode === 'ALL') {
        payload.mandal_ids = "ALL";
    } else {
        const mChecks = document.querySelectorAll('.mandal-check:checked');
        if (mChecks.length === 0) return alert("Select at least one Mandal");
        const ids = Array.from(mChecks).map(cb => parseInt(cb.value));
        payload.mandal_ids = JSON.stringify(ids);
    }

    // Calc Villages
    if (villageMode === 'ALL') {
        payload.village_ids = "ALL";
    } else {
        const vChecks = document.querySelectorAll('.village-check:checked');
        if (vChecks.length === 0) return alert("Select at least one Village");
        const ids = Array.from(vChecks).map(cb => parseInt(cb.value));
        payload.village_ids = JSON.stringify(ids);
    }

    // Infer Scope Type for Backend (High level label)
    if (mandalMode === 'ALL' && villageMode === 'ALL') payload.scope_type = "DISTRICT";
    else if (villageMode === 'ALL') payload.scope_type = "MANDAL";
    else payload.scope_type = "VILLAGE";

    try {
        const res = await fetch(`${API_BASE}/surveys/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Token': 'admin-secret-123'
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.status === 'success') {
            alert(data.message);
            closeModal();
            loadSurveyList();
            loadAssignmentOptions();
        } else {
            alert("Error: " + (data.message || data.detail));
        }
    } catch (e) {
        console.error(e);
        alert("Creation Failed");
    }
}

// --- 5. ASSIGNMENTS LOGIC (FIXED: DROPDOWNS) ---

async function loadAssignmentOptions() {
    // 1. Populate Survey Dropdown
    try {
        const surveysResponse = await fetch(`${API_BASE}/surveys/active`);
        const surveys = await surveysResponse.json();
        const select = document.getElementById('assignment-survey-select');

        // Save current selection if any
        const currentVal = select.value;

        select.innerHTML = '<option value="">-- Select Survey --</option>';
        surveys.forEach(s => {
            select.innerHTML += `<option value="${s.id}">${s.name} (${s.scope_type} ${s.scope_value})</option>`;
        });

        if (currentVal) select.value = currentVal;
    } catch (error) {
        console.error("Error loading surveys for assignment:", error);
    }
    // 2. Populate Surveyor Dropdown (NEW)
    try {
        const res = await fetch(`${API_BASE}/dashboard/approvals`);
        const allRequests = await res.json();
        // Only APPROVED surveyors
        let approved = allRequests.filter(a => a.status === 'APPROVED');

        // FILTER: If Coordinator, only show MY village surveyors
        if (CURRENT_USER.role === 'COORDINATOR') {
            approved = approved.filter(a => a.village === CURRENT_USER.village_name);
        }

        const surveyorList = document.getElementById('available-surveyors-list');
        surveyorList.innerHTML = '';

        if (approved.length === 0) {
            surveyorList.innerHTML = '<li class="list-group-item">No Approved Surveyors Found</li>';
        } else {
            surveyorList.innerHTML = `
                <li class="list-group-item">
                    <label><strong>Select Surveyor to Assign:</strong></label>
                    <div class="input-group mt-2">
                        <select id="surveyor-select-dropdown" class="form-control">
                            <option value="">-- Choose Surveyor --</option>
                            ${approved.map(a => `<option value="${a.id}">${a.name} (${a.mobile}) - ${a.ward || 'No Ward'}</option>`).join('')}
                        </select>
                        <button class="btn btn-primary" onclick="assignSurveyorFromDropdown()">Assign</button>
                    </div>
                </li>
             `;
        }

    } catch (e) {
        console.error("Error loading approved surveyors", e);
    }
}

async function assignSurveyorFromDropdown() {
    const surveyId = document.getElementById('assignment-survey-select').value;
    const surveyorId = document.getElementById('surveyor-select-dropdown').value;

    if (!surveyId) return alert("Please SELECT A SURVEY first.");
    if (!surveyorId) return alert("Please SELECT A SURVEYOR.");

    const res = await fetch(`${API_BASE}/assignments/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ survey_id: surveyId, surveyor_id: surveyorId })
    });

    const data = await res.json();
    if (data.status === 'success') {
        alert("Assigned Successfully!");
        fetchAssignmentData(); // Refresh list
    } else if (data.status === 'exists') {
        alert("Surveyor is already assigned to this survey.");
    } else {
        alert("Error: " + data.message);
    }
}

async function fetchAssignmentData() {
    const surveyId = document.getElementById('assignment-survey-select').value;
    console.log("Fetching assignments for survey ID:", surveyId);
    if (!surveyId) {
        const list = document.getElementById('assigned-surveyors-list');
        if (list) list.innerHTML = '';
        return;
    }

    try {
        const assignedResponse = await fetch(`${API_BASE}/assignments/list?survey_id=${surveyId}`);
        const assigned = await assignedResponse.json();
        console.log("Assignments Received:", assigned);

        const assignedList = document.getElementById('assigned-surveyors-list');
        if (!assignedList) return;

        assignedList.innerHTML = '';
        if (assigned.length === 0) {
            assignedList.innerHTML = '<li class="list-group-item text-muted">No one assigned yet</li>';
        }

        assigned.forEach(a => {
            const name = a.surveyor_name || `Surveyor #${a.surveyor_id}`;
            const mobile = a.surveyor_mobile || '';

            assignedList.innerHTML += `
                <li class="list-group-item" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee;">
                    <div>
                        <strong>${name}</strong><br>
                        <small class="text-muted">${mobile}</small>
                    </div>
                    <span class="badge" style="background:#10b981; color:white; padding: 4px 8px; border-radius: 4px;">Assigned</span>
                </li>`;
        });

    } catch (e) {
        console.error("Error fetching assignments:", e);
    }
}


// --- 7. DELETE LOGIC ---

async function deleteSurvey(id) {
    if (!confirm("Are you sure you want to PERMANENTLY delete this survey? All collected data will be lost.")) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/surveys/${id}`, {
            method: 'DELETE',
            headers: {
                'X-Admin-Token': 'admin-secret-123'
            }
        });
        const data = await res.json();

        if (res.ok) {
            alert(data.message);
            location.reload();
        } else {
            alert("Error: " + data.detail);
        }
    } catch (e) {
        console.error(e);
        alert("Failed to delete survey");
    }
}

async function loadSurveyList() {
    try {
        const res = await fetch(`${API_BASE}/surveys/active`);
        if (!res.ok) return;
        const surveys = await res.json();

        const tbody = document.getElementById('surveys-table-body');
        if (!tbody) return;

        tbody.innerHTML = '';
        surveys.forEach(s => {
            tbody.innerHTML += `
                <tr>
                    <td>${s.id}</td>
                    <td>${s.name}</td>
                    <td>${s.scope_type} ${s.scope_value}</td>
                    <td><span class="badge bg-success">${s.status}</span></td>
                    <td>${s.survey_code}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="deleteSurvey(${s.id})">Delete</button>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error loading survey list:", e);
    }
}


// --- SURVEYOR CREATION (BY COORDINATOR) ---

function openAddSurveyorModal() {
    if (CURRENT_USER.role !== 'COORDINATOR') {
        alert("Only Coordinators can use this feature.");
        return;
    }
    const modal = document.getElementById('addSurveyorModal');
    modal.style.display = 'block';

    // Show location preview
    document.getElementById('srv-location-preview').textContent =
        `${CURRENT_USER.village_name}, ${CURRENT_USER.mandal_name} (District: ${CURRENT_USER.district_name})`;
}

function closeAddSurveyorModal() {
    document.getElementById('addSurveyorModal').style.display = 'none';
}

async function createSurveyor() {
    const name = document.getElementById('srv-name').value;
    const mobile = document.getElementById('srv-mobile').value;

    if (!name || !mobile) {
        alert("Please enter Name and Mobile.");
        return;
    }

    // Inherit Location from Coordinator
    const payload = {
        name: name,
        mobile: mobile,
        district_name: CURRENT_USER.district_name,
        mandal_name: CURRENT_USER.mandal_name,
        village_name: CURRENT_USER.village_name,
        ward_no: "0",
        role: "SURVEYOR",
        village_id: CURRENT_USER.village_id
    };

    try {
        // 1. Register
        const res1 = await fetch(`${API_BASE}/register/surveyor`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data1 = await res1.json();

        if (data1.status === 'success' || data1.status === 'exists') {
            const reqId = data1.id;

            // 2. Approve Immediately
            const res2 = await fetch(`${API_BASE}/dashboard/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request_id: reqId, action: 'APPROVED' })
            });
            const data2 = await res2.json();

            alert(`Success! Surveyor '${name}' added to your team.`);
            closeAddSurveyorModal();

            // Refresh dropdowns ONLY if we are on Assignments tab
            if (typeof loadAssignmentOptions === 'function') loadAssignmentOptions();

            // Also refresh approvals list if visible
            // loadApprovals(); 
        } else {
            alert("Failed to create surveyor. " + (data1.detail || data1.message));
        }

    } catch (e) {
        console.error(e);
        alert("Error creating surveyor");
    }
}

// --- VOTER DATA UPLOAD ---
async function handleVoterUpload(input) {
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    if (!CURRENT_USER || CURRENT_USER.role !== 'ADMIN') {
        alert("Unauthorized. Please login as Admin.");
        return;
    }

    if (!confirm(`Upload ${file.name}? This will add voters to the database.`)) {
        input.value = ''; // Reset
        return;
    }

    // Get Selected Context
    const distId = document.getElementById('up-district').value;
    const mandalId = document.getElementById('up-mandal').value;
    const villageId = document.getElementById('up-village').value;
    const wardId = document.getElementById('up-ward').value;

    if (!wardId) {
        alert("Please select District > Mandal > Village > Ward before uploading.");
        input.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('secret_key', CURRENT_USER.token);
    formData.append('district_id', distId);
    formData.append('mandal_id', mandalId);
    formData.append('village_id', villageId);
    formData.append('ward_id', wardId);

    try {
        // Show loading state
        const btn = document.querySelector('button[onclick*="voterUploadFile"]');
        const originalText = btn.textContent;
        btn.textContent = "⏳ Uploading...";
        btn.disabled = true;

        const res = await fetch(`${API_BASE}/admin/upload-voters`, {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            alert("✅ Success: " + data.message);
            // Optional: Refresh dashboard stats if you had a function for it
            if (window.loadDashboardStats) loadDashboardStats();
        } else {
            alert("❌ Error: " + (data.detail || "Upload failed"));
        }
    } catch (e) {
        console.error(e);
        alert("❌ Connection Error");
    } finally {
        // Reset UI
        input.value = '';
        const btn = document.querySelector('button[onclick*="voterUploadFile"]');
        if (btn) { // Check if element still exists
            btn.textContent = "📤 Upload Voters (CSV)";
            btn.disabled = false;
        }
    }
}

// --- BULK UPLOAD CASCADING VALUES ---

async function loadUpDistricts() {
    const sel = document.getElementById('up-district');
    try {
        const res = await fetch(`${API_BASE}/locations/districts`);
        const data = await res.json();
        sel.innerHTML = '<option value="">Select District</option>';
        data.forEach(d => sel.innerHTML += `<option value="${d.id}">${d.name}</option>`);
    } catch (e) { }
}

async function loadUpMandals() {
    const distId = document.getElementById('up-district').value;
    const sel = document.getElementById('up-mandal');
    sel.innerHTML = '<option value="">Select Mandal</option>';
    document.getElementById('up-village').innerHTML = '<option value="">Select Village</option>';
    document.getElementById('up-ward').innerHTML = '<option value="">Select Ward</option>';

    if (!distId) return;
    try {
        const res = await fetch(`${API_BASE}/locations/mandals/${distId}`);
        const data = await res.json();
        data.forEach(d => sel.innerHTML += `<option value="${d.id}">${d.name}</option>`);
    } catch (e) { }
}

async function loadUpVillages() {
    const manId = document.getElementById('up-mandal').value;
    const sel = document.getElementById('up-village');
    sel.innerHTML = '<option value="">Select Village</option>';
    document.getElementById('up-ward').innerHTML = '<option value="">Select Ward</option>';

    if (!manId) return;
    try {
        const res = await fetch(`${API_BASE}/locations/villages/${manId}`);
        const data = await res.json();
        data.forEach(d => sel.innerHTML += `<option value="${d.id}">${d.name}</option>`);
    } catch (e) { }
}

async function loadUpWards() {
    const vilId = document.getElementById('up-village').value;
    const sel = document.getElementById('up-ward');
    sel.innerHTML = '<option value="">Select Ward</option>';

    if (!vilId) return;
    try {
        const res = await fetch(`${API_BASE}/locations/wards/${vilId}`);
        const data = await res.json();
        data.forEach(d => sel.innerHTML += `<option value="${d.id}">${d.name}</option>`);
    } catch (e) { }
}

// Call on startup
document.addEventListener('DOMContentLoaded', () => {
    // Existing startup logic...
    loadUpDistricts();
});
