# Amazon Q Developer PR Review Instructions

## Context: STOCKTRADE Crypto Trading Platform

This is a quantitative cryptocurrency trading platform built with:
- **Backend**: FastAPI (Python 3.14), SQLAlchemy 2.0, Pydantic 2.0
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Database**: PostgreSQL/TimescaleDB (prod), SQLite (dev)
- **Real-time**: WebSocket for live updates

## Review Focus Areas

### 1. Critical Security Issues
```bash
# Look for:
- Hardcoded API keys or credentials
- SQL injection vulnerabilities in database queries
- Missing authentication on sensitive endpoints
- CORS misconfigurations
- Insecure dependency versions
```

### 2. API Design & Consistency
- **Endpoint Naming**: RESTful conventions (/api/v1/resource)
- **HTTP Methods**: Proper use of GET, POST, PUT, DELETE, PATCH
- **Status Codes**: Correct codes (200, 201, 400, 401, 404, 500)
- **Response Format**: Consistent JSON structure
- **Error Responses**: Standardized error format

### 3. Database & Data Integrity
```python
# Check for proper patterns:
# ✅ Good - Using SQLAlchemy core properly
stmt = select(MarketData).where(MarketData.symbol == symbol)
result = await session.execute(stmt)

# ❌ Bad - Raw SQL with potential injection
query = f"SELECT * FROM market_data WHERE symbol = '{symbol}'"
```

### 4. Async/Await Correctness
```python
# Ensure all I/O is async:
# ✅ Good
async def get_data():
    data = await fetch_from_api()  # Note: await
    return data

# ❌ Bad - Blocking call in async function
async def get_data():
    data = requests.get(url)  # Blocking!
    return data
```

### 5. Testing Requirements
- New features must have tests
- Test file naming: `test_<module>.py`
- Use `pytest-asyncio` for async tests
- Mock external API calls (Binance, CoinGecko)

### 6. Performance Patterns
```python
# Watch for:
- N+1 query problems (looping database calls)
- Missing async on I/O operations
- Unnecessary large data fetches
- Memory leaks in WebSocket handlers
```

## Specific File Patterns

### API Routes (`api/*.py`)
- Use `APIRouter` for organization
- All endpoints should have type hints
- Use `Depends()` for shared dependencies
- Include docstrings for OpenAPI

### Services (`services/*.py`)
- Business logic goes here
- Keep endpoints thin
- Async methods for I/O
- Proper error handling

### Models (`models/*.py`)
- Use Pydantic for validation
- SQLAlchemy models with relationships
- Proper indexes for query performance

## Review Comment Template

When you find issues, use this format:

```markdown
### 🚨 [Security/Performance/Bug/etc]
**File:** `path/to/file.py:123`

**Issue:** [Clear description]

**Risk:** [What could go wrong]

**Fix:**
```python
# Show the corrected code
```

**Why:** [Explanation of why this is better]
```

## Approval Criteria

A PR should be approved when:
- ✅ All CI checks pass (tests, linting, security scan)
- ✅ No critical security issues
- ✅ Code follows project patterns
- ✅ Tests are included for new code
- ✅ Documentation updated if needed
- ✅ No breaking changes without discussion

## Red Flags (Request Changes)
- Hardcoded credentials
- SQL injection vulnerabilities
- Missing authentication on protected routes
- Breaking API changes without versioning
- Removed functionality without deprecation
