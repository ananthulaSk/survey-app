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
    const approvals = await res.json();

    document.getElementById('approvalsTableBody').innerHTML = approvals.map(a => `
        <tr>
            <td>${a.name}</td>
            <td>${a.mobile}</td>
            <td>${new Date(a.date).toLocaleDateString()}</td>
            <td>
                <button class="btn-approve" onclick="handleApproval(${a.id}, 'APPROVED')">Approve</button>
                <button class="btn-reject" onclick="handleApproval(${a.id}, 'REJECTED')">Reject</button>
            </td>
        </tr>
    `).join('');
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, scope_type: 'WARD', scope_value: ward })
    });

    const result = await res.json();
    alert(result.message);
    closeModal();
    loadSurveys();
}
