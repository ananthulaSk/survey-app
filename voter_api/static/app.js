const API_BASE = ""; // Relative path for Cloud Deployment
let currentSurveyId = null;
let chartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin Dashboard v7 Loaded");
    loadSurveys();
    loadApprovals();
    loadSurveyList(); // Adding the missing load

    // Attach listener for assignment tab
    const assignSelect = document.getElementById('assignment-survey-select');
    if (assignSelect) {
        assignSelect.addEventListener('change', fetchAssignmentData);
    }
});

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
        const res = await fetch(`${API_BASE}/surveys/active`);
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

async function loadApprovals() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/approvals`);
        const allRequests = await res.json();

        // Split Data
        const pending = allRequests.filter(a => a.status === 'PENDING');
        const history = allRequests.filter(a => a.status !== 'PENDING');

        // 1. Render Pending
        document.getElementById('approvalsTableBody').innerHTML = pending.map(a => `
            <tr>
                <td>${a.id}</td>
                <td>${a.name}</td>
                <td>${a.mobile}</td>
                <td><small>${a.district || '-'}<br>${a.mandal || '-'}<br>${a.village || '-'}<br>Ward ${a.ward || '-'}</small></td>
                <td>${new Date(a.date).toLocaleDateString()}</td>
                <td>
                    <button class="btn-approve" onclick="handleApproval(${a.id}, 'APPROVED')">Approve</button>
                    <button class="btn-reject" onclick="handleApproval(${a.id}, 'REJECTED')">Reject</button>
                    <button class="btn btn-sm btn-danger ms-2" style="background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px;" onclick="deleteSurveyor(${a.id})">Delete</button>
                </td>
            </tr>
        `).join('');

        // 2. Render History
        if (historyBody) {
            historyBody.innerHTML = history.map(a => `
                <tr>
                    <td>${a.id}</td>
                    <td>${a.name}</td>
                    <td>${a.mobile}</td>
                    <td><small>${a.district || '-'}<br>${a.mandal || '-'}<br>${a.village || '-'}<br>Ward ${a.ward || '-'}</small></td>
                    <td>${a.assigned_survey || '-'}</td>
                    <td>${new Date(a.date).toLocaleDateString()}</td>
                    <td>
                        <span class="badge" style="background:${a.status === 'APPROVED' ? '#10b981' : (a.status === 'REJECTED' ? '#ef4444' : '#6b7280')}">${a.status || 'PENDING'}</span>
                        <button class="btn btn-sm btn-danger ms-2" style="background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; margin-left: 10px;" onclick="deleteSurveyor(${a.id})">Delete</button>
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
        const res = await fetch(`${API_BASE}/locations/districts`);
        const districts = await res.json();
        const select = document.getElementById('scope-district');
        select.innerHTML = '<option value="">Select District</option>';
        districts.forEach(d => {
            select.innerHTML += `<option value="${d.id}">${d.name}</option>`;
        });
    } catch (e) { console.error("Error loading districts", e); }
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
        const surveysResponse = await fetch('/surveys/active');
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
        const approved = allRequests.filter(a => a.status === 'APPROVED');

        const surveyorList = document.getElementById('available-surveyors-list');
        surveyorList.innerHTML = '';

        // We will render them as a clean list of "Assign" buttons or a dropdown
        // Let's use a nice list with an "Assign" button next to each name

        if (approved.length === 0) {
            surveyorList.innerHTML = '<li class="list-group-item">No Approved Surveyors Found</li>';
        } else {
            // Create a dropdown container inside the list just to be clean, 
            // OR just list them. A specific dropdown input is better for UX.
            // Replacing the list content with a "Select to Assign" UI

            surveyorList.innerHTML = `
                <li class="list-group-item">
                    <label><strong>Select Surveyor to Assign:</strong></label>
                    <div class="input-group mt-2">
                        <select id="surveyor-select-dropdown" class="form-control">
                            <option value="">-- Choose Surveyor --</option>
                            ${approved.map(a => `<option value="${a.id}">${a.name} (${a.mobile})</option>`).join('')}
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

async function fetchAssignmentData() {
    const surveyId = document.getElementById('assignment-survey-select').value;
    if (!surveyId) return;

    try {
        // A. Get Assignments for this Survey
        const assignedResponse = await fetch(`/assignments/list?survey_id=${surveyId}`);
        const assigned = await assignedResponse.json();

        const assignedList = document.getElementById('assigned-surveyors-list');

        assignedList.innerHTML = '';
        if (assigned.length === 0) {
            assignedList.innerHTML = '<li class="list-group-item text-muted">No one assigned yet</li>';
        }

        assigned.forEach(a => {
            assignedList.innerHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${a.surveyor_name}</strong><br>
                        <small class="text-muted">${a.surveyor_mobile}</small>
                    </div>
                    <span class="badge bg-success">Assigned</span>
                </li>`;
        });

    } catch (e) {
        console.error(e);
    }
}

async function assignSurveyorFromDropdown() {
    const surveyId = document.getElementById('assignment-survey-select').value;
    const surveyorId = document.getElementById('surveyor-select-dropdown').value;

    if (!surveyId) return alert("Please SELECT A SURVEY first.");
    if (!surveyorId) return alert("Please SELECT A SURVEYOR.");

    const res = await fetch('/assignments/create', {
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
