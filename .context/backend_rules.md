# Backend Development Rules

## Code Style
- **Type Hinting:** Strictly enforce Python type hints on all function arguments and return values.
- **Async:** Use `async def` for all route handlers and database queries.

## Architecture Patterns
- **Pydantic Models:** Use Pydantic schemas for all Request and Response bodies. strictly separate DB models (SQLAlchemy) from API models (Pydantic).
- **Dependency Injection:** Use `Depends()` for database sessions and authentication.
- **Error Handling:** Use `HTTPException` for all error responses. Never return raw 500 errors; wrap them.

## Database (SQLAlchemy)
- Use `AsyncSession` for all DB interactions.
- Avoid N+1 queries by using `select().options(joinedload(...))` when fetching related data.
