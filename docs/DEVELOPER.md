# Developer Guide

This guide provides information for developers who want to contribute to the Crypto Quant Laboratory project.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Organization](#code-organization)
3. [API Development](#api-development)
4. [Database Development](#database-development)
5. [Testing](#testing)
6. [Code Quality](#code-quality)
7. [Contributing Guidelines](#contributing-guidelines)
8. [Debugging](#debugging)
9. [Performance Optimization](#performance-optimization)
10. [Security Best Practices](#security-best-practices)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Git
- VS Code or similar IDE (recommended with Python extensions)

### Initial Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/STOCKTRADE.git
   cd STOCKTRADE
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   source venv/Scripts/activate

   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies

   # Install development tools
   pip install pytest pytest-cov pytest-asyncio black ruff mypy pre-commit
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your development settings
   ```

### IDE Setup (VS Code)

1. **Install recommended extensions**
   - Python (Microsoft)
   - Pylance (Microsoft)
   - Black Formatter (ms-python.black-formatter)
   - Python Test Explorer (LittleFoxTeam.vscode-python-test-adapter)
   - Docker (ms-azuretools.vscode-docker)
   - GitLens (eamodio.gitlens)

2. **Create launch.json for debugging**
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: FastAPI",
         "type": "python",
         "request": "launch",
         "module": "uvicorn",
         "args": [
           "api.main:app",
           "--host",
           "0.0.0.0",
           "--port",
           "8000",
           "--reload"
         ],
         "jinja": true,
         "justMyCode": false
       },
       {
         "name": "Python: Tests",
         "type": "python",
         "request": "launch",
         "module": "pytest",
         "args": [
           "tests",
           "-v"
         ],
         "justMyCode": false
       }
     ]
   }
   ```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Code Organization

### Project Structure

```
STOCKTRADE/
├── api/                    # FastAPI endpoints
│   ├── main.py            # Application entry point
│   ├── __init__.py        # Package initialization
│   └── *.py              # Module-specific endpoints
├── core/                  # Core application functionality
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connection and session
│   ├── middleware.py      # Request middleware
│   └── websocket.py       # WebSocket management
├── models/                # Data models and schemas
│   ├── __init__.py
│   └── *.py              # Pydantic models
├── services/              # Business logic
│   ├── __init__.py
│   └── *.py              # Service classes
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_api.py        # API tests
│   ├── test_services.py  # Service tests
│   └── test_models.py     # Model tests
├── data/                  # Database and data files
└── frontend/              # Next.js application
```

### Design Patterns Used

1. **Repository Pattern**: Data access abstraction
2. **Service Layer**: Business logic separation
3. **Dependency Injection**: For testing and flexibility
4. **Async/Await**: For non-blocking I/O
5. **Factory Pattern**: For object creation

### Code Principles

1. **SOLID Principles**: Follow SOLID design principles
2. **DRY**: Don't Repeat Yourself
3. **KISS**: Keep It Simple, Stupid
4. **YAGNI**: You Ain't Gonna Need It
5. **Async Best Practices**: Use async/await consistently

## API Development

### Creating New Endpoints

1. **Create new module in `api/`**
   ```python
   # api/your_module.py
   from fastapi import APIRouter, HTTPException, Depends
   from typing import List
   from models.your_model import YourModel, YourModelCreate
   from services.your_service import YourService

   router = APIRouter(prefix="/api/your-module", tags=["your-module"])

   @router.get("/", response_model=List[YourModel])
   async def get_items():
       """Get all items"""
       service = YourService()
       return await service.get_all()

   @router.post("/", response_model=YourModel)
   async def create_item(item: YourModelCreate):
       """Create a new item"""
       service = YourService()
       return await service.create(item)
   ```

2. **Include in main application**
   ```python
   # api/main.py
   from api.your_module import router as your_module_router

   app.include_router(your_module_router)
   ```

3. **Add tests**
   ```python
   # tests/test_api.py
   import pytest
   from fastapi.testclient import TestClient

   def test_get_items(client: TestClient):
       response = client.get("/api/your-module/")
       assert response.status_code == 200
       assert isinstance(response.json(), list)
   ```

### Best Practices for API Development

1. **Use proper HTTP methods**
   - GET: Retrieve data
   - POST: Create new resource
   - PUT: Update existing resource
   - DELETE: Delete resource

2. **Use appropriate status codes**
   - 200 OK: Successful request
   - 201 Created: Resource created
   - 400 Bad Request: Invalid request
   - 401 Unauthorized: Authentication required
   - 403 Forbidden: Insufficient permissions
   - 404 Not Found: Resource not found
   - 500 Internal Server Error: Server error

3. **Validate input with Pydantic**
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional

   class ItemCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=100)
       description: Optional[str] = None
       price: float = Field(..., gt=0)
   ```

4. **Handle errors gracefully**
   ```python
   from fastapi import HTTPException
   from fastapi.responses import JSONResponse
   from fastapi.exceptions import RequestValidationError
   from starlette.exceptions import HTTPException as StarletteHTTPException

   app.add_exception_handler(RequestValidationError, validation_exception_handler)
   app.add_exception_handler(StarletteHTTPException, http_exception_handler)

   async def validation_exception_handler(request, exc):
       return JSONResponse(
           status_code=422,
           content={"detail": exc.errors(), "body": exc.body},
       )
   ```

### WebSocket Development

1. **Create WebSocket endpoint**
   ```python
   from fastapi import WebSocket, WebSocketDisconnect

   @app.websocket("/ws/your-channel")
   async def websocket_endpoint(websocket: WebSocket):
       await websocket.accept()
       try:
           while True:
               data = await websocket.receive_json()
               # Process message
               response = await process_message(data)
               await websocket.send_json(response)
       except WebSocketDisconnect:
           pass
   ```

2. **Use WebSocket manager**
   ```python
   from core.websocket import WebSocketManager

   ws_manager = WebSocketManager()

   @app.websocket("/ws/your-channel")
   async def websocket_endpoint(websocket: WebSocket):
       await ws_manager.connect(websocket)
       try:
           while True:
               data = await websocket.receive_json()
               # Broadcast to all connected clients
               await ws_manager.broadcast(data)
       except WebSocketDisconnect:
           ws_manager.disconnect(websocket)
   ```

## Database Development

### SQLAlchemy Models

1. **Create base model**
   ```python
   # models/base.py
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy import Column, Integer, DateTime
   from datetime import datetime

   Base = declarative_base()

   class TimestampMixin:
       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   ```

2. **Create specific model**
   ```python
   # models/your_model.py
   from sqlalchemy import Column, String, Integer, Float, Boolean
   from models.base import Base, TimestampMixin

   class YourModel(Base, TimestampMixin):
       __tablename__ = "your_models"

       id = Column(Integer, primary_key=True, index=True)
       name = Column(String, index=True)
       value = Column(Float)
       active = Column(Boolean, default=True)
   ```

3. **Create Pydantic schema**
   ```python
   # models/your_model.py
   from pydantic import BaseModel
   from typing import Optional

   class YourModelBase(BaseModel):
       name: str
       value: float
       active: bool = True

   class YourModelCreate(YourModelBase):
       pass

   class YourModelUpdate(BaseModel):
       name: Optional[str] = None
       value: Optional[float] = None
       active: Optional[bool] = None

   class YourModel(YourModelBase):
       id: int

       class Config:
           from_attributes = True
   ```

### Database Operations

1. **Use repository pattern**
   ```python
   # repositories/your_repository.py
   from sqlalchemy.orm import Session
   from models.your_model import YourModel
   from typing import List, Optional

   class YourRepository:
       def __init__(self, db: Session):
           self.db = db

       def get_all(self) -> List[YourModel]:
           return self.db.query(YourModel).all()

       def get_by_id(self, id: int) -> Optional[YourModel]:
           return self.db.query(YourModel).filter(YourModel.id == id).first()

       def create(self, data: dict) -> YourModel:
           db_item = YourModel(**data)
           self.db.add(db_item)
           self.db.commit()
           self.db.refresh(db_item)
           return db_item

       def update(self, id: int, data: dict) -> Optional[YourModel]:
           db_item = self.get_by_id(id)
           if db_item:
               for key, value in data.items():
                   setattr(db_item, key, value)
               self.db.commit()
               self.db.refresh(db_item)
           return db_item

       def delete(self, id: int) -> bool:
           db_item = self.get_by_id(id)
           if db_item:
               self.db.delete(db_item)
               self.db.commit()
               return True
           return False
   ```

2. **Use in services**
   ```python
   # services/your_service.py
   from sqlalchemy.orm import Session
   from repositories.your_repository import YourRepository

   class YourService:
       def __init__(self, db: Session):
           self.repository = YourRepository(db)

       async def get_all(self):
           return self.repository.get_all()

       async def create(self, data):
           return self.repository.create(data)
   ```

### Database Migrations

1. **Set up Alembic**
   ```bash
   pip install alembic
   alembic init alembic
   ```

2. **Configure Alembic**
   ```ini
   # alembic.ini
   [alembic]
   script_location = alembic
   sqlalchemy.url = sqlite:///./data/crypto_quant.db
   ```

3. **Create migration**
   ```bash
   alembic revision --autogenerate -m "Add your model"
   ```

4. **Apply migration**
   ```bash
   alembic upgrade head
   ```

## Testing

### Test Structure

```
tests/
├── conftest.py           # Test configuration and fixtures
├── test_api.py           # API endpoint tests
├── test_services.py      # Service layer tests
├── test_models.py        # Model validation tests
└── integration/         # Integration tests
    ├── test_full_workflow.py
    └── test_websocket.py
```

### Writing Tests

1. **Fixtures (conftest.py)**
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from api.main import app
   from core.database import get_db
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from models.base import Base

   # Test database
   SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
   engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
   TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

   Base.metadata.create_all(bind=engine)

   def override_get_db():
       try:
           db = TestingSessionLocal()
           yield db
       finally:
           db.close()

   app.dependency_overrides[get_db] = override_get_db

   @pytest.fixture
   def client():
       return TestClient(app)

   @pytest.fixture
   def db():
       return TestingSessionLocal()
   ```

2. **API Tests**
   ```python
   # tests/test_api.py
   def test_get_items(client):
       response = client.get("/api/your-module/")
       assert response.status_code == 200
       assert isinstance(response.json(), list)

   def test_create_item(client):
       item_data = {"name": "Test Item", "value": 10.5}
       response = client.post("/api/your-module/", json=item_data)
       assert response.status_code == 201
       assert response.json()["name"] == "Test Item"

   def test_create_item_invalid_data(client):
       response = client.post("/api/your-module/", json={"invalid": "data"})
       assert response.status_code == 422
   ```

3. **Service Tests**
   ```python
   # tests/test_services.py
   import pytest
   from services.your_service import YourService

   @pytest.mark.asyncio
   async def test_get_all_items(db):
       service = YourService(db)
       items = await service.get_all()
       assert isinstance(items, list)

   @pytest.mark.asyncio
   async def test_create_item(db):
       service = YourService(db)
       item_data = {"name": "Test Service Item", "value": 15.0}
       item = await service.create(item_data)
       assert item.name == "Test Service Item"
   ```

4. **Integration Tests**
   ```python
   # tests/integration/test_full_workflow.py
   def test_create_and_retrieve_item(client):
       # Create item
       create_data = {"name": "Integration Test", "value": 20.0}
       create_response = client.post("/api/your-module/", json=create_data)
       assert create_response.status_code == 201
       item_id = create_response.json()["id"]

       # Retrieve item
       get_response = client.get(f"/api/your-module/{item_id}")
       assert get_response.status_code == 200
       assert get_response.json()["name"] == "Integration Test"
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto

# Run tests with markers
pytest -m "not integration"
```

### Mocking and Fixtures

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_database():
    with patch('core.database.get_db') as mock:
        mock_session = Mock()
        mock.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_service():
    return Mock()

@patch('services.your_service.YourService')
def test_with_mock_service(mock_class, mock_database):
    # Configure mock
    mock_class.return_value.get_all.return_value = []

    # Test
    service = YourService(mock_database)
    result = service.get_all()

    # Assert
    assert result == []
    mock_class.return_value.get_all.assert_called_once()
```

## Code Quality

### Code Formatting

1. **Black (Code Formatter)**
   ```bash
   # Format all code
   black .

   # Check formatting
   black --check .

   # Check diff
   black --diff .
   ```

2. **Ruff (Linter and Formatter)**
   ```bash
   # Check for issues
   ruff check .

   # Auto-fix issues
   ruff check --fix .

   # Check specific rules
   ruff check --select E,W,F .
   ```

### Type Checking

1. **MyPy**
   ```bash
   # Check types
   mypy .

   # Check with specific config
   mypy --ignore-missing-imports .

   # Continue on errors
   mypy --ignore-missing-imports --continue-on-error .
   ```

### Static Analysis

1. **Pre-commit hooks**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/psf/black
       rev: 23.3.0
       hooks:
         - id: black
           language_version: python3
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.6
       hooks:
         - id: ruff
           args: [--fix]
     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.3.0
       hooks:
         - id: mypy
           additional_dependencies: [types-requests]
   ```

2. **Code Complexity**
   ```bash
   # Install radon
   pip install radon

   # Check metrics
   radon cc api/ -nb -a

   # Maintainability index
   radon cc api/ -nb -nb -a
   ```

### Documentation

1. **Docstring Standards**
   ```python
   """Module docstring.

   This is a multi-line docstring that follows the Google style.
   """

   def function_with_docs(arg1: str, arg2: int = 10) -> bool:
       """Function description.

       Args:
           arg1: Description of arg1.
           arg2: Description of arg2. Defaults to 10.

       Returns:
           Description of return value.

       Raises:
           ValueError: If arg1 is invalid.
       """
       if not arg1:
           raise ValueError("arg1 cannot be empty")
       return len(arg1) > arg2
   ```

2. **API Documentation**
   - Use FastAPI's automatic documentation
   - Provide detailed descriptions for endpoints
   - Include examples for complex operations

## Contributing Guidelines

### Workflow

1. **Fork the repository**
   - Create your fork on GitHub

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Write tests for new features
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Run all tests
   pytest

   # Check code quality
   black --check .
   ruff check .
   mypy .
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a pull request**
   - PR title should follow conventional commits
   - Include detailed description
   - Link related issues
   - Add screenshots if applicable

### Commit Message Format

Use conventional commits:

```
<type>(<scope>): <description>

[body]

[footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(api): add new endpoint for portfolio analysis

Adds a new GET endpoint to retrieve portfolio performance metrics
with support for date range filtering.

Closes #123

feat(auth): implement JWT authentication

- Add JWT token generation and validation
- Update middleware to check tokens
- Add refresh token mechanism

BREAKING CHANGE: All API endpoints now require authentication
```

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass (both unit and integration)
- [ ] Tests are added for new features
- [ ] Documentation is updated
- [ ] PR description is clear and comprehensive
- [ ] Changes are reviewed and approved
- [ ] CI/CD pipeline passes

## Debugging

### Debugging Setup

1. **Python debugger configuration**
   ```json
   // .vscode/launch.json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: Current File",
         "type": "python",
         "request": "launch",
         "module": "pytest",
         "args": ["${file}"],
         "justMyCode": false
       }
     ]
   }
   ```

2. **Debug mode in FastAPI**
   ```python
   if DEBUG:
       import logging
       logging.basicConfig(level=logging.DEBUG)
   ```

### Common Debugging Techniques

1. **Logging**
   ```python
   import logging

   logger = logging.getLogger(__name__)

   async def function():
       logger.debug("Debug message")
       logger.info("Info message")
       logger.warning("Warning message")
       logger.error("Error message")
   ```

2. **Breakpoints**
   ```python
   import pdb; pdb.set_trace()

   # Or using VS Code
   import breakpoint; breakpoint()
   ```

3. **Database Queries Debugging**
   ```python
   from sqlalchemy.dialects import postgresql

   # Print generated SQL
   print(str(query.statement.compile(dialect=postgresql.dialect())))
   ```

4. **WebSocket Debugging**
   ```python
   # In WebSocket endpoint
   print(f"Received: {data}")
   print(f"WebSocket state: {websocket.state}")
   ```

### Performance Debugging

1. **Profile application**
   ```python
   import cProfile
   import pstats

   def profile_function():
       pr = cProfile.Profile()
       pr.enable()
       # Your code here
       pr.disable()
       stats = pstats.Stats(pr)
       stats.sort_stats('cumulative')
       stats.print_stats()
   ```

2. **Database query analysis**
   ```python
   from sqlalchemy.engine import Engine
   from sqlalchemy import event

   @event.listens_for(Engine, "before_cursor_execute")
   def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
       context._query_start_time = time.time()

   @event.listens_for(Engine, "after_cursor_execute")
   def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
       total = time.time() - context._query_start_time
       if total > 0.1:  # Log slow queries
           print(f"Slow query: {total:.2f}s\n{statement}\n")
   ```

## Performance Optimization

### Application Optimization

1. **Async/Await Best Practices**
   ```python
   # Good
   async def endpoint():
       data = await database_query()
       result = await process_data(data)
       return result

   # Bad - Mixing sync and async
   def endpoint():
       data = database_sync_query()  # Blocking
       result = process_data_sync(data)  # Blocking
       return result
   ```

2. **Database Optimization**
   ```python
   # Use eager loading
   from sqlalchemy.orm import joinedload

   # Instead of N+1 queries
   items = await db.query(Item).options(joinedload(Item.related)).all()

   # Use batch operations
   for chunk in data_chunks:
       db.bulk_save_objects(chunk)
   ```

3. **Caching Strategy**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def expensive_operation(param):
       # Expensive computation
       return result
   ```

### Memory Optimization

1. **Use generators for large datasets**
   ```python
   # Instead of loading all data at once
   async def get_large_dataset():
       for item in database_query():
           yield item
   ```

2. **Memory profiling**
   ```python
   import tracemalloc

   tracemalloc.start()
   # Your code here
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   for stat in top_stats[:10]:
       print(stat)
   ```

### WebSocket Optimization

1. **Connection pooling**
   ```python
   # Limit concurrent connections per client
   MAX_CONNECTIONS_PER_CLIENT = 5
   ```

2. **Message batching**
   ```python
   # Batch messages before sending
   async def batch_messages(messages):
       batch = []
       for message in messages:
           batch.append(message)
           if len(batch) >= 100:
               await websocket.send_json(batch)
               batch = []
       if batch:
           await websocket.send_json(batch)
   ```

## Security Best Practices

### Input Validation

1. **Always validate user input**
   ```python
   from pydantic import BaseModel, constr, validator

   class SafeModel(BaseModel):
       name: constr(max_length=100)
       email: constr(regex=r'^[^@]+@[^@]+\.[^@]+$')

       @validator('name')
       def validate_name(cls, v):
           if not v.isalpha():
               raise ValueError('Name must contain only letters')
           return v
   ```

2. **SQL Injection Prevention**
   ```python
   # Use SQLAlchemy's parameterized queries
   # Bad: Direct string formatting
   query = f"SELECT * FROM users WHERE id = {user_id}"

   # Good: Use SQLAlchemy
   query = db.query(User).filter(User.id == user_id)
   ```

### Authentication and Authorization

1. **API Key Authentication**
   ```python
   from fastapi import Header, HTTPException

   async def get_api_key(api_key: str = Header(...)):
       if api_key != API_KEY:
           raise HTTPException(status_code=403, detail="Invalid API Key")
       return api_key
   ```

2. **JWT Implementation**
   ```python
   import jwt
   from datetime import datetime, timedelta

   def create_token(user_id: str) -> str:
       payload = {
           'user_id': user_id,
           'exp': datetime.utcnow() + timedelta(hours=24)
       }
       return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
   ```

### Data Sanitization

1. **Escape HTML content**
   ```python
   import html

   def sanitize_html(content: str) -> str:
       return html.escape(content)
   ```

2. **File upload security**
   ```python
   ALLOWED_EXTENSIONS = {'.jpg', '.png', '.pdf'}
   MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

   def validate_file(file):
       if not file.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
           raise ValueError("Invalid file type")

       if len(file.read()) > MAX_FILE_SIZE:
           file.seek(0)  # Reset file pointer
           raise ValueError("File too large")
   ```

### Environment Variables

1. **Never hardcode secrets**
   ```python
   import os
   from dotenv import load_dotenv

   load_dotenv()

   SECRET_KEY = os.getenv('SECRET_KEY')
   if not SECRET_KEY:
       raise ValueError("SECRET_KEY not set")
   ```

2. **Use secure storage**
   - Use AWS Secrets Manager or Azure Key Vault
   - For development, use `.env` file (add to `.gitignore`)
   - For production, use environment variables or secret management service

### Monitoring Security

1. **Log security events**
   ```python
   SECURITY_LOG_FORMAT = '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
   security_logger = logging.getLogger('security')
   security_logger.setLevel(logging.WARNING)
   handler = logging.FileHandler('security.log')
   handler.setFormatter(logging.Formatter(SECURITY_LOG_FORMAT))
   security_logger.addHandler(handler)
   ```

2. **Monitor for suspicious activity**
   ```python
   # Rate limiting for authentication
   from fastapi import FastAPI, Request
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)

   @app.post("/login")
   @limiter.limit("5 per minute")
   async def login(request: Request, credentials: dict):
       # Login logic
       pass
   ```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

For questions or help, join our Discord community or create an issue on GitHub.