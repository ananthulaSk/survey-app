
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
