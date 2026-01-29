
⚠️ ANTIGRAVITY HARD CONSTRAINT FILE
ELECTION SURVEY APPLICATION — SINGLE SOURCE OF TRUTH

This document is a HARD CONSTRAINT CONTRACT.
DO NOT summarize, compress, reinterpret, or weaken any rule.
EVERY rule is mandatory.
If anything is unclear → STOP and ASK.
If a conflict exists → DO NOT auto-resolve.

====================================================================
SECTION 1: CORE PRINCIPLES (AUTHORITY)
====================================================================
- This is an Election Survey App, NOT an official election system
- Data correctness > speed > UI polish
- Ward-level isolation is a SECURITY BOUNDARY
- Backend is the final authority; frontend is never trusted
- Survey data must be auditable and reproducible

====================================================================
SECTION 2: BACKEND RULES (FastAPI / Python)
====================================================================
- ALL endpoints MUST be `async def`
- ONLY `AsyncSession` is allowed (no sync DB access)
- Pydantic v2 ONLY (no v1 syntax, no orm_mode)
- SQLAlchemy Models ≠ Pydantic Schemas
- ALL errors MUST return JSON using HTTPException
- Backend MUST NEVER return HTML responses
- Related queries MUST use joinedload() to avoid N+1
- Any DB schema change REQUIRES Alembic migration

====================================================================
SECTION 3: API CONTRACT LAW (CRITICAL)
====================================================================
- Every endpoint MUST define:
  - Request schema (Pydantic)
  - Response schema (Pydantic)
- Frontend may ONLY consume declared JSON fields
- Backend must NEVER silently change JSON shape
- Endpoint renames require frontend update in SAME change
- Non-JSON backend response is ALWAYS a BUG

====================================================================
SECTION 4: ELECTION DATA ISOLATION (MOST CRITICAL)
====================================================================
- Surveyors MUST see ONLY voters from their assigned ward
- Ward filtering MUST be enforced in backend queries
- Frontend ward filters are advisory ONLY
- Missing ward context MUST reject the request
- Cross-ward data leakage is ZERO tolerance

====================================================================
SECTION 5: SURVEY DATA INTEGRITY
====================================================================
- Every voter response MUST store:
  - survey_id
  - voter_id
  - ward_no
  - surveyor_id
  - timestamp
- Responses are append-only (no silent overwrite)
- Any correction MUST be traceable (audit-safe)
- No auto-correction of political data

====================================================================
SECTION 6: FRONTEND RULES (Flutter Web)
====================================================================
- Web-first layout (desktop safe)
- NEVER assume mobile screen
- LayoutBuilder OR MediaQuery is mandatory
- Desktop MUST use ConstrainedBox
- NO default Material blue theme
- API calls ONLY via service layer
- NEVER call APIs inside build()
- Services MUST initialize before UI renders
- UI MUST handle loading / empty / denied states
- JSON parsing MUST be type-safe and defensive

====================================================================
SECTION 7: WORKFLOW ORDER (MANDATORY)
====================================================================
1. Define Pydantic data model
2. Validate ward & role isolation
3. Verify Flutter can parse response
4. Implement backend logic
5. Implement frontend consumption
6. Test using ward-bound test accounts

Skipping steps is NOT allowed.

====================================================================
SECTION 8: DEPLOYMENT & OPERATIONS
====================================================================
- Frontend code change REQUIRES `flutter build web`
- Docker deploy REQUIRES CACHEBUST update
- Cloud Run deploy REQUIRES traffic = 100%
- Cached frontend MUST be invalidated or bypassed
- Deploy success ≠ live traffic

====================================================================
SECTION 9: AUTO-LOGIC FORBIDDEN
====================================================================
- Do NOT guess missing logic
- Do NOT infer voter intent
- Do NOT auto-correct survey answers
- Do NOT fabricate analytics
- Do NOT downgrade async → sync
- Do NOT simplify rules for convenience

====================================================================
SECTION 10: DOMAIN CONTEXT (REFERENCE)
====================================================================
SYSTEM PURPOSE:
- Secure, ward-isolated election survey platform
- Used for internal voter sentiment analysis only
- NOT for declaring winners or official predictions

USER ROLES:
- Admin: Full system control
- Coordinator: Survey & assignment management
- Surveyor: Data collection (ward-bound)

SURVEY FLOW:
1. Admin creates survey
2. Surveyors assigned via SurveyAssignment
3. Surveyor fetches next voter (ward-filtered)
4. Surveyor submits response
5. Data stored with audit context

DATA IMPORT (VOTER LISTS):
- CSV ward values may be inconsistent
- `safe_int()` extracts first integer via regex
- Dropdown-selected ward overrides invalid CSV ward

ANALYTICS INTENT:
- Aggregated counts only
- Ward / booth-level summaries
- Trends over time
- No individual voter exposure

SYSTEM INITIALIZATION:
- Empty database supported
- Geo data auto-seeded if missing
- Survey creation self-heals missing district IDs

LEGAL & ETHICAL LIMITS:
- No coercion logic
- No voter manipulation
- No individual profiling beyond survey scope

====================================================================
SECTION 11: EXAMPLES (NON-AUTHORITATIVE)
====================================================================
EXAMPLE: VOTER FETCH RESPONSE
{
  "voter_id": 10234,
  "name": "Ramesh",
  "ward_no": 4,
  "age_group": "36-45",
  "gender": "M"
}

EXAMPLE: SURVEY RESPONSE PAYLOAD
{
  "survey_id": 7,
  "voter_id": 10234,
  "preferred_party": "Party A",
  "confidence_level": 3,
  "submitted_at": "2026-01-29T10:21:00Z"
}

FORBIDDEN OUTPUTS:
❌ Declaring winners
❌ Individual voter predictions
❌ Official election claims
