⚠️ ANTIGRAVITY HARD CONSTRAINT FILE
ELECTION SURVEY SYSTEM — SINGLE SOURCE OF TRUTH

This document is a HARD CONSTRAINT CONTRACT.

NO rule may be weakened, summarized, or bypassed.

If any rule is unclear → STOP and ASK.

If rules conflict → DO NOT auto-resolve.

Convenience is never a justification for violation.

====================================================
1. AUTHORITY & CORE PRINCIPLES
====================================================

The Backend is the single source of truth. Frontend is never trusted.

Data correctness and auditability override speed and UI polish.

Ward-level isolation is a non-negotiable security boundary.

No auto-logic, inference, or silent correction is permitted.

This system is for internal analysis only, not official election results.

====================================================
2. BACKEND CONSTRAINTS (FastAPI / SQLAlchemy)
====================================================

All endpoints MUST be async def.

ONLY AsyncSession is permitted for database access.

Pydantic v2 ONLY. No v1 syntax. No orm_mode.

SQLAlchemy models MUST remain separate from Pydantic schemas.

All errors MUST return JSON via HTTPException. HTML is forbidden.

Related queries MUST use joinedload() to prevent N+1 queries.

Any schema change REQUIRES an Alembic migration.

Manual database editing is forbidden.

====================================================
3. API & DATA CONTRACT LAW (CRITICAL)
====================================================

Every endpoint MUST define:

Request schema (Pydantic)

Response schema (Pydantic)

Backend MUST NOT silently change JSON structures.

Endpoint renames require simultaneous frontend updates.

Frontend may ONLY consume declared fields.

Non-JSON backend responses are ALWAYS a bug.

Ward filtering MUST be enforced at SQL level using auth context.

====================================================
4. ELECTION DATA ISOLATION (SECURITY BOUNDARY)
====================================================

Surveyors may access ONLY voters in assigned wards.

Ward context MUST be validated in every relevant query.

Frontend filters are advisory only.

Missing ward context MUST reject the request.

Cross-ward data leakage is ZERO tolerance.

====================================================
5. SURVEY DATA INTEGRITY & AUDITABILITY
====================================================

Every voter response MUST store:

survey_id

voter_id

ward_no

surveyor_id

timestamp

Rules:

Responses are append-only.

Silent overwrites are forbidden.

All corrections must be traceable.

No automated modification of political data.

====================================================
6. FRONTEND CONSTRAINTS (Flutter Web)
====================================================

Web-first, desktop-safe layout is mandatory.

LayoutBuilder or ConstrainedBox MUST be used.

Mobile-first assumptions are forbidden.

API calls MUST go through a Service Layer.

API calls inside build() are forbidden.

Services MUST initialize before UI render.

UI MUST handle: Loading, Empty, Error, Denied states.

JSON parsing MUST be defensive and type-safe.

Deep linking MUST preserve session context.

====================================================
7. DEVELOPMENT WORKFLOW (MANDATORY)
====================================================

All features MUST follow this order:

Define Pydantic models

Validate ward & role isolation

Verify Flutter parsing

Implement backend logic

Implement frontend consumption

Test using ward-bound accounts

Skipping steps is forbidden.

====================================================
8. MIGRATION, DEPLOYMENT & OPERATIONS
====================================================

Frontend changes REQUIRE flutter build web.

Docker builds REQUIRE cache-busting updates.

Environment variables MUST be validated before deploy.

Production/Staging DB mismatch is forbidden.

Cloud Run traffic may move to 100% ONLY after:

Successful migration

Data verification

Cached frontend MUST be invalidated.

Deploy success ≠ Live traffic success.

====================================================
9. AUTO-LOGIC & FABRICATION FORBIDDEN
====================================================

The system MUST NOT:

Guess missing logic

Infer voter intent

Auto-correct responses

Fabricate analytics

Downgrade async → sync

Bypass validation for convenience

Any violation is a critical defect.

====================================================
10. DOMAIN & ETHICAL LIMITS
====================================================

SYSTEM PURPOSE:

Secure, ward-isolated survey platform

Internal voter sentiment analysis only

Not an official election authority

PROHIBITED:

Declaring winners

Individual voter prediction

Manipulation logic

Profiling beyond survey scope

Political targeting automation

====================================================
11. DATA IMPORT & INITIALIZATION
====================================================

CSV ward values may be inconsistent.

safe_int() must extract numeric ward IDs.

UI-selected ward overrides invalid CSV data.

Empty database must be supported.

Geo data may be auto-seeded.

Survey creation must self-heal missing references.

====================================================
12. EXAMPLES (NON-AUTHORITATIVE)
====================================================
Voter Fetch Response
{
  "voter_id": 10234,
  "name": "Ramesh",
  "ward_no": 4,
  "age_group": "36-45",
  "gender": "M"
}

Survey Submission
{
  "survey_id": 7,
  "voter_id": 10234,
  "preferred_party": "Party A",
  "confidence_level": 3,
  "submitted_at": "2026-01-29T10:21:00Z"
}


====================================================
10. RECENT CRITICAL DECISIONS (v20.100+)
====================================================

1. **Session Persistence**: 
   - `Role` (ADMIN/SURVEYOR) MUST be persisted in SharedPreferences. 
   - Failure to do so causes Admin privileges to be lost on page reload.

2. **Survey Creation Safety**:
   - Creating a survey MUST NOT fail if location metadata (Names) cannot be fetched.
   - Use `try/except` blocks and default to "Unknown" for District/Mandal/Village names.

3. **Consolidated Survey Logic**:
   - There must be ONLY ONE `get_active_surveys` endpoint.
   - It must handle BOTH Admin (List All) and Surveyor (Filter by Assignment) logic.
   - Duplicate endpoints cause conflicting behavior and invisible data.

4. **Snapshot Integrity**:
   - `SurveyVoter` snapshots are created at Survey Creation time.
   - They MUST include `ward_no` mapped correctly from `WardMaster`.

====================================================
END OF CONSTITUTION
====================================================