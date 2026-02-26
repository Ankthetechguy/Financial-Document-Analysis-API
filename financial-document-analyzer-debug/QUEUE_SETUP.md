# Financial Document Analyzer - Queue Worker & Database Integration

## New Features Implemented ✨

This enhanced version includes:
- **Celery Task Queue** - Async document analysis with background workers
- **Redis Broker** - Job queue management
- **SQLAlchemy Database** - Store analysis results persistently
- **Task Tracking** - Monitor analysis progress and retrieve results

---

## Setup & Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Redis Server

**Option A: Docker (Recommended)**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Option B: Windows Installer**
- Download from https://github.com/microsoftarchive/redis/releases
- Or use WSL: `wsl apt-get install redis-server`

**Option C: Local Installation**
- macOS: `brew install redis`
- Linux: `sudo apt-get install redis-server`

### 3. Initialize Database

```bash
python migrations.py
```

This creates the SQLite database and all required tables:
- `analysis_tasks` - Tracks analysis jobs
- `user_analysis_history` - User interaction history
- `analysis_metrics` - Performance metrics

### 4. Environment Setup (Optional)

Create a `.env` file to customize settings:

```env
# Database Configuration
DATABASE_URL=sqlite:///./financial_analysis.db
# Or for PostgreSQL: postgresql://user:password@localhost/dbname

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Running the Application

You need **3 terminal windows**:

### Terminal 1: Redis Server
```bash
redis-server
# Or if installed via Docker, it's already running
```

### Terminal 2: FastAPI Server
```bash
python main.py
# Server runs on http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Terminal 3: Celery Worker
```bash
python worker.py
# Or use Celery directly:
# celery -A celery_app worker --loglevel=info
```

---

## API Endpoints

### Health Check
```bash
GET /
```

### Submit Analysis Task (Async)
```bash
POST /analyze
Content-Type: multipart/form-data

Parameters:
  - file: PDF file to analyze (required)
  - query: Analysis query (optional, default provided)

Response:
{
  "status": "queued",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "celery_task_id": "abc123def456",
  "message": "Analysis queued. Use task_id to check status",
  "file_processed": "document.pdf"
}
```

### Get Task Status
```bash
GET /tasks/{task_id}

Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "document.pdf",
  "query": "Analyze this financial document",
  "status": "processing",  // pending, processing, completed, failed
  "created_at": "2026-02-27T10:00:00",
  "started_at": "2026-02-27T10:00:05",
  "completed_at": null,
  "duration_seconds": null,
  "analysis_result": null,
  "error_message": null,
  "celery_status": {
    "state": "STARTED",
    "info": {...}
  }
}
```

### Get Analysis Result
```bash
GET /tasks/{task_id}/result

Response (when completed):
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "file_name": "document.pdf",
  "query": "Analyze this financial document",
  "result": {
    "analysis": "..."
  },
  "completed_at": "2026-02-27T10:15:30",
  "duration_seconds": 325.5
}
```

### List All Tasks
```bash
GET /tasks?status=completed&limit=50

Query Parameters:
  - status: Filter by status (optional)
  - limit: Max results (default: 50)

Response:
{
  "count": 10,
  "tasks": [...]
}
```

### Check Celery Health
```bash
GET /celery/health

Response:
{
  "status": "ok",
  "celery_task_id": "xyz789"
}
```

---

## Database Schema

### AnalysisTask
Stores analysis job information:
- `id` (UUID) - Primary key
- `file_name` - Uploaded filename
- `file_path` - Stored file location
- `query` - User's analysis query
- `status` - Job status (pending/processing/completed/failed)
- `analysis_result` - JSON result
- `error_message` - Error details if failed
- `created_at` - Submission time
- `started_at` - Processing start time
- `completed_at` - Completion time
- `duration_seconds` - Processing time
- `celery_task_id` - Associated Celery task

### UserAnalysisHistory
Tracks user analysis interactions:
- `id` (UUID) - Primary key
- `user_id` - User identifier (optional)
- `analysis_task_id` - Link to AnalysisTask
- `document_name` - Original filename
- `document_type` - File type
- `document_size` - File size in bytes
- `analysis_type` - Type of analysis
- `key_findings` - JSON key findings
- `created_at` - Timestamp

### AnalysisMetrics
Performance and cost metrics:
- `id` (UUID) - Primary key
- `analysis_task_id` - Link to AnalysisTask
- `processing_time_ms` - Processing duration
- `document_pages` - Page count (if PDF)
- `tokens_used` - LLM tokens consumed
- `model_used` - LLM model name
- `estimated_cost_usd` - API cost
- `created_at` - Timestamp

---

## Example Usage (Python)

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. Submit a document for analysis
with open("financial_report.pdf", "rb") as f:
    files = {"file": f}
    data = {"query": "Analyze this quarterly report"}
    response = requests.post(f"{BASE_URL}/analyze", files=files, data=data)
    task_id = response.json()["task_id"]
    print(f"Task queued: {task_id}")

# 2. Check status
for i in range(30):
    status_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status == "completed":
        break
    elif status == "failed":
        print("Analysis failed!")
        break
    
    time.sleep(5)  # Wait 5 seconds

# 3. Get the result
result_response = requests.get(f"{BASE_URL}/tasks/{task_id}/result")
result = result_response.json()
print(f"Analysis completed in {result['duration_seconds']}s")
print(result["result"])
```

---

## Configuration Options

### Celery Settings
Edit `config.py` to adjust:
- `TASK_SERIALIZER` - JSON or pickle
- `task_time_limit` - Hard timeout (30 min default)
- `task_soft_time_limit` - Soft timeout (25 min default)

### Database Backends
Supported databases:
- SQLite (development): `sqlite:///./financial_analysis.db`
- PostgreSQL (production): `postgresql://user:pass@host/db`
- MySQL: `mysql+pymysql://user:pass@host/db`

### Redis Configuration
For production clustering:
```env
CELERY_BROKER_URL=redis://password@localhost:6379/0
CELERY_RESULT_BACKEND=redis://password@localhost:6379/1
```

---

## Monitoring & Debugging

### View Celery Logs
```bash
celery -A celery_app worker --loglevel=debug
```

### Monitor Celery Tasks (Requires Flower)
```bash
pip install flower
celery -A celery_app flower
# Open http://localhost:5555
```

### Check Database
```python
from database import SessionLocal
from models import AnalysisTask

db = SessionLocal()
tasks = db.query(AnalysisTask).all()
for task in tasks:
    print(f"{task.id}: {task.status} - {task.file_name}")
```

### View Redis Queue
```bash
redis-cli
> KEYS *
> LLEN celery  # Number of pending tasks
```

---

## Troubleshooting

### "Redis connection refused"
- Check Redis is running: `redis-cli ping` should return PONG
- Verify port 6379 is not in use

### "Task not found in database"
- Check database initialization: `python migrations.py`
- Verify database file exists: `ls -la financial_analysis.db`

### "Celery worker not processing tasks"
- Ensure worker is running in separate terminal
- Check worker logs for errors
- Verify broker URL matches in config

### "Database locked" (SQLite)
- SQLite has limited concurrent write support
- For production, use PostgreSQL: Update `.env` DATABASE_URL

---

## Production Deployment

For production use:

1. **Use PostgreSQL instead of SQLite**
   ```bash
   pip install psycopg2-binary
   # Update DATABASE_URL in .env
   ```

2. **Use RabbitMQ instead of Redis** (for better reliability)
   ```bash
   # Docker: docker run -d -p 5672:5672 rabbitmq:latest
   CELERY_BROKER_URL=amqp://guest:guest@localhost//
   ```

3. **Use Gunicorn for FastAPI**
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -b 0.0.0.0:8000
   ```

4. **Run multiple Celery workers**
   ```bash
   # Terminal 2
   celery -A celery_app worker -n worker1@%h --loglevel=info
   # Terminal 3
   celery -A celery_app worker -n worker2@%h --loglevel=info
   ```

5. **Add task result cleanup** (prevent DB bloat)
   ```python
   # In celery_app.py, add:
   celery_app.conf.result_expires = 3600  # 1 hour
   ```

---

## Architecture Diagram

```
┌─────────────────────────────────────┐
│     FastAPI Web Server              │
│  (main.py) - listens on 8000        │
└──────────────────┬──────────────────┘
                   │ enqueues tasks
                   ▼
┌─────────────────────────────────────┐
│     Redis Broker                    │
│  (Queue Manager) - port 6379        │
└──────────────────┬──────────────────┘
                   │ jobs
                   ▼
┌─────────────────────────────────────┐
│     Celery Workers                  │
│  (worker.py) - process async jobs   │
└──────────────────┬──────────────────┘
                   │ writes results
                   ▼
┌─────────────────────────────────────┐
│     SQLite Database                 │
│  Stores results & history           │
└─────────────────────────────────────┘
```

---

## Files Added

- `config.py` - Configuration management
- `database.py` - Database setup & session management
- `models.py` - SQLAlchemy ORM models
- `celery_app.py` - Celery task definitions
- `worker.py` - Celery worker runner
- `migrations.py` - Database initialization
- `QUEUE_SETUP.md` - This documentation (setup guide)

---

## Next Steps

1. Install Redis and dependencies
2. Initialize database: `python migrations.py`
3. Start Redis, FastAPI server, and Celery worker (3 terminals)
4. Upload documents to `/analyze` endpoint
5. Check status with `/tasks/{task_id}`
6. Retrieve results with `/tasks/{task_id}/result`

Enjoy your scalable financial document analyzer! 🚀
