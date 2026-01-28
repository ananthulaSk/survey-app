# Project Context & Architecture Guidelines

## 1. Technical Stack Overview
**The "Truth" Source for all architectural decisions.**

- **Application:** Modern web-based survey platform.
- **Backend:** FastAPI (Python 3.10) with Uvicorn & SQLAlchemy.
- **Frontend:** Flutter Web (SDK ^3.10.4) with Dart.
- **Database:** PostgreSQL (implied via SQLAlchemy) / Cloud SQL.
- **Infrastructure:** Docker (Multi-stage), Google Cloud Run, Cloud Build CI/CD.
- **Region:** asia-south1 (Mumbai).

---

## 2. Backend Rules (Python/FastAPI)
**Strictly follow these patterns for any backend code.**

### Architecture
- **Async First:** ALL route handlers and DB queries must be `async def`.
- **Validation:** Use **Pydantic v2** models for all Request/Response bodies.
- **Separation:** Strictly separate `SQLAlchemy Models` (DB tables) from `Pydantic Schemas` (API data).
- **Dependency Injection:** Use `Depends()` for DB sessions and current user auth.
- **Error Handling:** Always wrap errors in `HTTPException`. Never return raw 500s.

### Database (SQLAlchemy)
- **Session:** Use `AsyncSession` exclusively.
- **Queries:** Avoid N+1 issues by using `select().options(joinedload(...))` for related data.
- **Migrations:** All schema changes must be accompanied by a migration script (Alembic).

---

## 3. Frontend Rules (Flutter Web)
**Strictly follow these patterns for any Dart/Flutter code.**

### Design & UI
- **Aesthetics:** NO default "Material Blue". Use a custom `ThemeData` defined in `main.dart`.
- **Icons:** Use `cupertino_icons` primarily.
- **Responsiveness (CRITICAL):**
  - **Never** assume a mobile screen.
  - ALWAYS use `LayoutBuilder` or `MediaQuery` to adapt layouts.
  - **Desktop:** Use `ConstrainedBox` to prevent full-width stretching on large screens.
  - **Mobile:** Ensure touch targets are large enough (44px+).

### Implementation
- **Charts:** Use `fl_chart` for all visualizations. Enable tooltips for mouse users.
- **State Management:** Keep business logic SEPARATE from UI widgets (use a Service/Repository pattern).
- **Networking:** Use the `http` package. All API calls must go through a dedicated service layer (e.g., `survey_service.dart`), never called directly inside `build()`.
- **Performance:** Use `const` constructors everywhere possible to optimize Web rendering.

---

## 4. Workflow Protocol (The "Antigravity" Process)
**Before writing code for complex features, the AI must:**
1.  **Plan:** Propose the JSON structure (Pydantic model) first.
2.  **Verify:** Ensure the Flutter frontend can easily consume that JSON structure.

## 5. Recent Architectures & Critical Logic (Phase 5 & 6)

### A. Data Security (Ward Isolation)
- **Constraint:** Surveyors MUST only see voters from their assigned Ward, even if the Survey spans multiple wards.
- **Backend Implementation:**
    - All voter-fetching endpoints (`/voters/next`, `/voters/search`, etc.) accept an optional `ward` parameter.
    - If `ward` is present, the query is strictly filtered by `ward_no`.
- **Frontend Implementation:**
    - `ApiService` captures `ward_no` upon login/status check.
    - This `ward_no` is automatically injected into all voter fetch calls.
    - **Re-Login Required** on mobile to fetch new policy.

### B. Robust Data Import (Smart Parsing)
- **Problem:** CSVs often contain "Ward 4", "Ward No 4", or "4". Legacy logic failed on strings.
- **Solution (v19.23+):**
    - `safe_int()` helper uses Regex to extract the first integer from any string.
    - **Snapshot Creation (v19.25+):** Uses dual-verification. checks `ward_id` (Dropdown Context) FIRST. If `ward_no` in data is 0/invalid, it **Auto-Corrects** it based on the Dropdown selection.

### C. Assignments (Phase 5)
- **Logic:** Surveyors are not "owned" by a survey permanently.
- **Table:** `SurveyAssignment` links `Survey` <-> `Surveyor`.
- **UI:** Dropdowns must display "Name (Mobile) - Ward X" to prevent assignment errors.

## 6. Test Accounts
- **Admin Secret:** `admin-secret-123`
- **Test Surveyor:**
  - **Mobile:** `6666666666`
  - **Name:** `TEST_USER_API_2`
  - **Device ID:** `test_script_002`
- **Test Coordinator:**
  - **Mobile:** `9876543210` (If created via UI)


## 7. System Initialization & Troubleshooting
**Critical behavior for Fresh Deployments (Empty Database).**

### A. Admin Dashboard "Empty State"
- **Behavior:** Upon first login, if NO surveys exist, the Dashboard will show a **"Create First Survey"** block.
- **Reason:** The original "Static" dashboard was removed. The system now enforces "Active Survey" context to display analytics.
- **Action:** Admin MUST click "Create First Survey" to initialize the system.

### B. Self-Healing Survey Creation (v19.73+)
- **Problem:** On fresh Cloud SQL instances, District IDs vary (e.g., 1 vs 33). Hardcoding IDs causes "Scope Resolution Failed".
- **Solution:** The `/surveys/create` endpoint is **Self-Healing**:
    - If `district_id` is omitted or 0, the backend **Auto-Selects** the first available District.
    - If the Database is empty, it **Auto-Seeds** Geo Data (Districts/Mandals) before creation.
    - **Frontend:** Sends `district_id: 0` to trigger this logic safely.
