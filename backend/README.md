# Bylaw Database API Backend

A FastAPI-based backend for managing municipal bylaws and source documents with comprehensive version tracking and liability protection.

## Features

- **Municipality Management**: CRUD operations for municipalities with statistics
- **Bylaw Management**: Full version tracking and change history
- **Source Document Preservation**: Secure storage and retrieval for liability protection
- **Admin Panel**: Scraping configuration and system management
- **Audit Logging**: Comprehensive audit trail for all operations
- **Type Safety**: Full type hints and Pydantic models
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## Architecture

### Core Components

1. **FastAPI Application** (`src/main.py`)
   - CORS middleware configuration
   - Exception handling
   - Health checks
   - API routing

2. **Database Models** (`src/models/`)
   - `municipality.py` - Municipality data models
   - `bylaw.py` - Bylaw and version models
   - `source_document.py` - Document storage models
   - `audit.py` - Audit logging models

3. **API Routers** (`src/api/routers/`)
   - `municipalities.py` - Municipality endpoints
   - `bylaws.py` - Bylaw CRUD with versioning
   - `source_documents.py` - Document retrieval
   - `admin.py` - Administrative functions

4. **Utilities** (`src/utils/`)
   - `supabase_client.py` - Database client wrapper
   - `config.py` - Configuration management

## Installation

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Required Environment Variables**
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_ANON_KEY` - Supabase anonymous key
   - `SUPABASE_SERVICE_KEY` - Supabase service role key
   - `SECRET_KEY` - JWT secret key
   - `ALLOWED_ORIGINS` - CORS allowed origins

## Running the Application

### Development Mode
```bash
python run.py
```

### Production Mode
```bash
pip install gunicorn
gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```bash
docker build -t bylaw-db-api .
docker run -p 8000:8000 bylaw-db-api
```

## API Documentation

Once running, access the API documentation at:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## API Endpoints

### Municipalities
- `GET /api/v1/municipalities` - List municipalities
- `POST /api/v1/municipalities` - Create municipality
- `GET /api/v1/municipalities/{id}` - Get municipality
- `PUT /api/v1/municipalities/{id}` - Update municipality
- `DELETE /api/v1/municipalities/{id}` - Delete municipality
- `GET /api/v1/municipalities/{id}/stats` - Get statistics

### Bylaws
- `GET /api/v1/bylaws` - List bylaws
- `POST /api/v1/bylaws` - Create bylaw
- `GET /api/v1/bylaws/{id}` - Get bylaw with versions
- `PUT /api/v1/bylaws/{id}` - Update bylaw
- `DELETE /api/v1/bylaws/{id}` - Delete bylaw
- `GET /api/v1/bylaws/{id}/versions` - Get all versions
- `POST /api/v1/bylaws/{id}/versions` - Create new version

### Source Documents
- `GET /api/v1/source-documents` - List documents
- `POST /api/v1/source-documents` - Create document
- `GET /api/v1/source-documents/{id}` - Get document
- `GET /api/v1/source-documents/{id}/content` - Get content
- `GET /api/v1/source-documents/{id}/raw-html` - Get HTML
- `GET /api/v1/source-documents/{id}/pdf` - Get PDF

### Admin
- `GET /api/v1/admin/health` - System health
- `GET /api/v1/admin/scraping-configs` - Scraping configurations
- `POST /api/v1/admin/scraping-configs` - Create config
- `GET /api/v1/admin/scraping-jobs` - List jobs
- `POST /api/v1/admin/scraping-jobs` - Start job
- `GET /api/v1/admin/audit-logs` - Audit logs

## Database Schema

The application uses Supabase/PostgreSQL with the following key tables:

- `municipalities` - Municipality information
- `bylaws` - Bylaw records
- `bylaw_versions` - Version history
- `source_documents` - Document storage metadata
- `adu_requirements` - Extracted ADU requirements
- `scraping_configs` - Scraping configurations
- `scraping_jobs` - Job tracking
- `audit_log` - Audit trail

## Data Models

### Municipality
```python
{
    "id": "uuid",
    "name": "City Name",
    "province": "Province",
    "website_url": "https://example.com",
    "scraping_enabled": true,
    "metadata": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### Bylaw
```python
{
    "id": "uuid",
    "municipality_id": "uuid",
    "bylaw_number": "2024-001",
    "title": "Accessory Dwelling Unit Bylaw",
    "category": "adu",
    "status": "active",
    "effective_date": "2024-01-01",
    "full_text": "...",
    "versions": [...],
    "current_version": {...}
}
```

### Source Document
```python
{
    "id": "uuid",
    "municipality_id": "uuid",
    "document_url": "https://example.com/bylaw.pdf",
    "document_type": "pdf",
    "scraped_at": "2024-01-01T00:00:00Z",
    "preservation_status": "preserved",
    "raw_html_path": "path/to/file.html",
    "pdf_path": "path/to/file.pdf"
}
```

## Security

- **Authentication**: Supabase Auth integration
- **Authorization**: Row-level security policies
- **API Keys**: Service key for admin operations
- **CORS**: Configurable origin restrictions
- **Rate Limiting**: Built-in protection
- **Input Validation**: Pydantic model validation

## Monitoring

- **Health Checks**: `/health` endpoint
- **Audit Logging**: All operations logged
- **Error Handling**: Structured error responses
- **Request Logging**: Comprehensive request tracking

## Development

### Code Structure
```
backend/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models/              # Pydantic models
│   ├── api/routers/         # API endpoints
│   └── utils/               # Utilities
├── tests/                   # Test files
├── requirements.txt         # Dependencies
└── run.py                   # Startup script
```

### Testing
```bash
pytest tests/
```

### Code Quality
```bash
black src/
flake8 src/
mypy src/
```

## Deployment

### Environment Variables
Set all required environment variables for production:
- Use strong secret keys
- Configure proper CORS origins
- Set up monitoring and logging
- Enable security headers

### Database Setup
1. Create Supabase project
2. Run database migrations
3. Set up row-level security policies
4. Configure storage buckets

### Monitoring
- Set up health check monitoring
- Configure log aggregation
- Set up error tracking
- Monitor API performance

## Contributing

1. Follow Python best practices
2. Add type hints to all functions
3. Write comprehensive tests
4. Update documentation
5. Follow semantic versioning

## License

MIT License - see LICENSE file for details.