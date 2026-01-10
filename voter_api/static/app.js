const API_BASE = "http://127.0.0.1:8000";
let currentSurveyId = null;
let chartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
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

    try {
        // Summary
        const sumRes = await fetch(`${API_BASE}/dashboard/summary?survey_id=${currentSurveyId}`);
        const summary = (await sumRes.json()).data;

        document.getElementById('totalVoters').textContent = summary.total_voters;
        document.getElementById('effectiveVoters').textContent = summary.effective_voters;
        document.getElementById('completedSurveys').textContent = summary.completed_surveys;
        document.getElementById('completionPercentage').textContent = `${summary.completion_percentage}%`;

        // Progress
        const progRes = await fetch(`${API_BASE}/dashboard/progress?survey_id=${currentSurveyId}`);
        const progress = (await progRes.json()).data;
        const progBody = document.getElementById('progressTableBody');
        progBody.innerHTML = progress.map(p => `
            <tr>
                <td>Ward ${p.ward_no}</td>
                <td>${p.completed} / ${p.effective_voters}</td>
                <td>${p.total_voters}</td>
                <td><span class="badge" style="background:${p.status === 'COMPLETED' ? '#10b981' : '#f59e0b'}">${p.status}</span></td>
            </tr>
        `).join('');

        // Analytics
        const analRes = await fetch(`${API_BASE}/dashboard/analytics?survey_id=${currentSurveyId}`);
        const analytics = (await analRes.json()).data;

        renderChart(analytics);
    } catch (e) { console.error(e); }
}

function renderChart(data) {
    const ctx = document.getElementById('analyticsChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.party),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
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
                <td>${new Date(a.date).toLocaleDateString()}</td>
                <td>
                    <button class="btn-approve" onclick="handleApproval(${a.id}, 'APPROVED')">Approve</button>
                    <button class="btn-reject" onclick="handleApproval(${a.id}, 'REJECTED')">Reject</button>
                    <button class="btn btn-sm btn-danger ms-2" style="background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px;" onclick="deleteSurveyor(${a.id})">Delete</button>
                </td>
            </tr>
        `).join('');

        // 2. Render History
        const historyBody = document.getElementById('approvalsHistoryTableBody');
        if (historyBody) {
            historyBody.innerHTML = history.map(a => `
                <tr>
                    <td>${a.id}</td>
                    <td>${a.name}</td>
                    <td>${a.mobile}</td>
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

function showCreateSurveyModal() { document.getElementById('createModal').style.display = 'flex'; }
function closeModal() { document.getElementById('createModal').style.display = 'none'; }

async function createSurvey() {
    const name = document.getElementById('newSurveyName').value;
    const ward = document.getElementById('newSurveyWard').value;

    if (!name || !ward) return alert("Fill all fields");

    const res = await fetch(`${API_BASE}/surveys/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Token': 'admin-secret-123'
        },
        body: JSON.stringify({ name: name, scope_type: 'WARD', scope_value: ward })
    });

    const result = await res.json();
    alert(result.message);
    closeModal();
    loadSurveys();
    loadSurveyList();
    loadAssignmentOptions();
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
