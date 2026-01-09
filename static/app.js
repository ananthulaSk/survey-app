const API_BASE = "http://127.0.0.1:8000";
let currentSurveyId = null;
let chartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSurveys();
    loadApprovals();
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    document.getElementById(`${tabId}-tab`).classList.add('active');
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');

    document.getElementById('page-title').textContent = tabId.charAt(0).toUpperCase() + tabId.slice(1);
}

async function loadSurveys() {
    const res = await fetch(`${API_BASE}/surveys/active`);
    const surveys = await res.json();

    const select = document.getElementById('surveySelect');
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
}

async function loadDashboardData() {
    currentSurveyId = document.getElementById('surveySelect').value;
    if (!currentSurveyId) return;

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
                <td><span class="badge" style="background:${a.status === 'APPROVED' ? '#10b981' : (a.status === 'REJECTED' ? '#ef4444' : '#6b7280')}">${a.status || 'PENDING'}</span></td>
            </tr>
        `).join('');
    }
}

async function handleApproval(id, action) {
    await fetch(`${API_BASE}/dashboard/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: id, action: action })
    });
    loadApprovals();
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
}

// --- 5. ASSIGNMENTS LOGIC ---

async function loadAssignments() {
    // 1. Load active surveys into dropdown
    try {
        const surveysResponse = await fetch('/surveys/active');
        const surveys = await surveysResponse.json();
        const select = document.getElementById('assignment-survey-select');
        select.innerHTML = '<option value="">-- Select Survey --</option>';
        surveys.forEach(s => {
            select.innerHTML += `<option value="${s.id}">${s.name} (${s.scope_type} ${s.scope_value})</option>`;
        });
    } catch (error) {
        console.error("Error loading surveys for assignment:", error);
    }
}

async function fetchAssignmentData() {
    const surveyId = document.getElementById('assignment-survey-select').value;
    if (!surveyId) return;

    try {
        // A. Get Assignments for this Survey
        const assignedResponse = await fetch(`/assignments/list?survey_id=${surveyId}`);
        const assigned = await assignedResponse.json();

        const availableList = document.getElementById('available-surveyors-list');
        const assignedList = document.getElementById('assigned-surveyors-list');

        assignedList.innerHTML = '';
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

        // Placeholder for Available - Manual Entry for now
        availableList.innerHTML = '<li class="list-group-item text-muted">To assign, please enter surveyor ID manually below (Temporary)</li>';

        availableList.innerHTML += `
             <li class="list-group-item">
                <div class="input-group">
                    <input type="text" id="manual-surveyor-id" class="form-control" placeholder="Surveyor ID">
                    <button class="btn btn-primary" onclick="assignSurveyorManual()">Assign</button>
                </div>
             </li>
        `;

    } catch (e) {
        console.error(e);
    }
}

async function assignSurveyorManual() {
    const surveyId = document.getElementById('assignment-survey-select').value;
    const surveyorId = document.getElementById('manual-surveyor-id').value;

    if (!surveyId || !surveyorId) {
        alert("Please select survey and enter surveyor ID");
        return;
    }

    const res = await fetch('/assignments/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ survey_id: surveyId, surveyor_id: surveyorId })
    });

    const data = await res.json();
    if (data.status === 'success') {
        fetchAssignmentData(); // Refresh
        document.getElementById('manual-surveyor-id').value = '';
    } else {
        alert("Error: " + data.message);
    }
}

// Attach listener if elements exist
const assignSelect = document.getElementById('assignment-survey-select');
if (assignSelect) {
    assignSelect.addEventListener('change', fetchAssignmentData);
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
            location.reload(); // Simple reload to refresh all lists
        } else {
            alert("Error: " + data.detail);
        }
    } catch (e) {
        console.error(e);
        alert("Failed to delete survey");
    }
}

// Function to populate the surveys table (which we added a holder for)
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

// Hook into existing load sequence or make sure to call it
// We can just add it to the end of the init chain or expose it globally
// For simplicity, let's auto-load it if the table exists
document.addEventListener('DOMContentLoaded', () => {
    loadSurveyList();
});
