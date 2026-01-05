# GitHub Copilot PR Review Instructions

When reviewing pull requests for this project, GitHub Copilot should focus on:

## Review Criteria

### 1. Code Quality
- **Type Safety**: Check for proper Python type hints (mypy compliance)
- **Error Handling**: Ensure all API endpoints have proper error handling
- **Async Patterns**: Verify proper async/await usage in FastAPI endpoints
- **Code Style**: Ensure consistency with project patterns (Ruff, Black formatting)

### 2. Security
- **SQL Injection**: Check for proper parameterized queries in database operations
- **API Keys**: Ensure no hardcoded credentials or API keys
- **Input Validation**: Verify Pydantic models are used for request validation
- **CORS**: Check CORS configuration isn't overly permissive
- **Authentication**: Verify authentication/authorization on protected endpoints

### 3. Performance
- **Database Queries**: Look for N+1 query problems
- **Async Operations**: Ensure I/O operations are async
- **Caching**: Recommend caching for frequently accessed data
- **WebSocket**: Check for proper WebSocket connection management

### 4. Testing
- **Test Coverage**: Verify new code has corresponding tests
- **Async Tests**: Ensure tests use pytest-asyncio properly
- **Mocking**: Check for proper mocking of external APIs

### 5. FastAPI Best Practices
- **Dependency Injection**: Use FastAPI's Depends() for shared logic
- **Response Models**: Ensure endpoints use response_model for validation
- **Status Codes**: Return appropriate HTTP status codes
- **APIRouter**: Use APIRouter for modular route organization

## Code-Specific Guidelines

### Backend (Python/FastAPI)
```python
# ✅ Good
@router.get("/market/{symbol}")
async def get_market_data(
    symbol: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> MarketDataResponse:
    ...
```

### Frontend (Next.js/React)
- Check for proper TypeScript typing
- Verify proper error boundaries
- Look for proper useEffect cleanup
- Ensure no memory leaks in event listeners

## Comment Format

When commenting on PRs, use this format:

```markdown
## Issue Category
**Severity:** High/Medium/Low
**Location:** file:line

**Problem:** Description of the issue...

**Suggestion:** How to fix it...

**Code Example:**
```python
# Show corrected code
```
```

## Positive Feedback
Also comment on well-written code:
```markdown
## ✅ Good Practice
Excellent use of [pattern/technique] in file:line
```
