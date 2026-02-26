## 🚀 Queue Worker & Database Integration - Complete Implementation

This document serves as a quick reference for the new features. See **QUEUE_SETUP.md** for the detailed setup guide.

---

## What's New

Your financial-document-analyzer now has:

✅ **Async Task Processing** - Celery + Redis for background jobs  
✅ **Data Persistence** - SQLAlchemy ORM with SQLite/PostgreSQL support  
✅ **Task Tracking** - Monitor analysis progress in real-time  
✅ **Request Scalability** - Handle concurrent requests efficiently  
✅ **Production Ready** - Docker support, health checks, error handling  

---

## Quick Start (1-2-3)

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Start Services (3 terminals)

**Terminal 1 - Redis:**
```bash
redis-server
# or Docker: docker run -d -p 6379:6379 redis:latest
```

**Terminal 2 - FastAPI Server:**
```bash
python main.py
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

**Terminal 3 - Celery Worker:**
```bash
python worker.py
# or: celery -A celery_app worker --loglevel=info
```

### 3️⃣ Test It

```bash
# Method A: Interactive client
python client.py

# Method B: curl
curl -X POST http://localhost:8000/analyze \
  -F "file=@document.pdf" \
  -F "query=Analyze this financial report"

# Response:
# {"status": "queued", "task_id": "..."}

# Check status
curl http://localhost:8000/tasks/task-id-here

# Get result
curl http://localhost:8000/tasks/task-id-here/result
```

---

## Files Overview

### Core Implementation
| File | Purpose |
|------|---------|
| `config.py` | Configuration management |
| `database.py` | Database setup & sessions |
| `models.py` | SQLAlchemy models |
| `celery_app.py` | Celery task definitions |
| `worker.py` | Celery worker runner |
| `main.py` | FastAPI with async endpoints |

### Utilities
| File | Purpose |
|------|---------|
| `migrations.py` | Database initialization |
| `client.py` | Interactive API client |
| `test_setup.py` | Integration tests |
| `manage_db.py` | Database maintenance |
| `quickstart.py` | Setup instructions |

### Documentation
| File | Purpose |
|------|---------|
| `QUEUE_SETUP.md` | Complete setup guide |
| `IMPLEMENTATION_SUMMARY.md` | Technical details |
| `docker-compose.yml` | Docker configuration |

---

## API Endpoints

### Health Check
```http
GET /
```
Returns: `{"message": "Financial Document Analyzer API is running"}`

### Submit Analysis (Async)
```http
POST /analyze
Content-Type: multipart/form-data

file: <pdf file>
query: <optional analysis query>
```
Returns task_id for polling

### Get Task Status
```http
GET /tasks/{task_id}
```
Returns: status, timestamps, Celery state

### Get Result
```http
GET /tasks/{task_id}/result
```
Returns: analysis result (when completed)

### List All Tasks
```http
GET /tasks?status=completed&limit=50
```
Parameters: `status` (optional), `limit` (default: 50)

### Check Workers
```http
GET /celery/health
```
Verifies Celery workers are running

---

## Database Schema

### AnalysisTask
Tracks all analysis jobs
```
id (UUID)              - Primary key
file_name              - Original filename
file_path              - Stored file location
query                  - Analysis query
status                 - pending/processing/completed/failed
analysis_result        - JSON result
error_message          - Error details
created_at/started_at/ - Timestamps
completed_at
duration_seconds       - Processing time
celery_task_id         - Link to Celery task
```

### UserAnalysisHistory
Tracks user interactions
```
id                     - Primary key
user_id                - User identifier (optional)
analysis_task_id       - Link to AnalysisTask
document_name          - Filename
document_size          - File size in bytes
key_findings           - JSON findings
created_at             - Timestamp
```

### AnalysisMetrics
Performance tracking
```
id                     - Primary key
analysis_task_id       - Link to AnalysisTask
processing_time_ms     - Duration in ms
tokens_used            - LLM tokens consumed
model_used             - LLM model name
estimated_cost_usd     - API cost
```

---

## Configuration

Create `.env` to customize:
```env
# Database
DATABASE_URL=sqlite:///./financial_analysis.db
# or: postgresql://user:pass@localhost/db

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Common Tasks

### Initialize Database
```bash
python migrations.py
```

### Test Setup
```bash
python test_setup.py
```

### Manage Database
```bash
python manage_db.py
# Options: Show stats, cleanup old tasks, reset DB, export to JSON
```

### Interactive Client
```bash
python client.py
# Submit files, check status, get results
```

### Monitor Celery
```bash
pip install flower
celery -A celery_app flower
# Open: http://localhost:5555
```

---

## Production Deployment

### Use Docker
```bash
# Start Redis + API (optional: add PostgreSQL)
docker-compose up -d

# Run worker separately
docker run -v $(pwd):/app financial-analyzer celery -A celery_app worker
```

### Use PostgreSQL
```env
DATABASE_URL=postgresql://user:password@localhost/financial_analyzer
```

### Use systemd (Linux)
Create `/etc/systemd/system/financial-analyzer.service`:
```ini
[Unit]
Description=Financial Document Analyzer Worker
After=network.target redis.service

[Service]
Type=simple
User=analyzer
WorkingDirectory=/opt/financial-analyzer
ExecStart=/opt/financial-analyzer/venv/bin/celery -A celery_app worker
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `redis.exceptions.ConnectionError` | Start Redis: `redis-server` |
| `database.sqlite: database locked` | Use PostgreSQL for production |
| `Task 'analyze_financial_document' not in registry` | Restart Celery worker |
| `Task never completes` | Check worker terminal for errors |
| `405 Method Not Allowed` | Endpoint is POST/GET, check your request |

---

## Performance Tips

1. **Multiple Workers**: Run multiple `python worker.py` commands
2. **Concurrency**: Adjust `--concurrency=N` based on CPU cores
3. **Database**: PostgreSQL is 10x faster than SQLite for production
4. **Caching**: Add Redis caching for frequently analyzed documents
5. **Monitoring**: Use Flower to identify bottlenecks

---

## Example Usage (Python)

```python
import requests
import time

# 1. Submit document
with open("report.pdf", "rb") as f:
    resp = requests.post("http://localhost:8000/analyze", 
                        files={"file": f},
                        data={"query": "Analyze this quarterly report"})
    task_id = resp.json()["task_id"]

# 2. Poll for completion
while True:
    status = requests.get(f"http://localhost:8000/tasks/{task_id}").json()
    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        print("Analysis failed!")
        break
    print(f"Status: {status['status']}")
    time.sleep(5)

# 3. Get result
result = requests.get(f"http://localhost:8000/tasks/{task_id}/result").json()
print(result["result"]["analysis"])
```

---

## Architecture

```
┌──────────────────┐
│  FastAPI Server  │────────────────┐
│   (Port 8000)    │                │
└──────────────────┘                │
         │                          │
         │ enqueue                  │ store/query
         ▼                          ▼
    ┌─────────┐              ┌──────────────┐
    │  Redis  │              │  SQLite/     │
    │ (Queue) │              │  PostgreSQL  │
    └─────────┘              └──────────────┘
         │
         │ worker picks up jobs
         ▼
    ┌──────────────────┐
    │  Celery Worker   │
    │  (Processing)    │
    └──────────────────┘
         │
         └──→ Store results in DB
```

---

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Choose: Redis locally or Docker
3. ✅ Run: `python migrations.py`
4. ✅ Start 3 services (Redis, FastAPI, Celery)
5. ✅ Test: `python client.py` or visit http://localhost:8000/docs
6. 📊 Optional: `pip install flower && celery -A celery_app flower`
7. 🚀 Deploy: Use docker-compose or systemd

---

## Documentation

- **QUEUE_SETUP.md** - Complete setup guide (200+ lines)
- **IMPLEMENTATION_SUMMARY.md** - Technical details and examples
- **quickstart.py** - Interactive setup instructions
- **config.py** - Configuration options
- **models.py** - Database schema with comments

---

## Support

- 🐛 Errors in worker: Check terminal #3 (Celery worker)
- 🔧 Database issues: Run `python migrations.py`
- 📊 Monitor tasks: Use `python client.py` or Swagger UI at `/docs`
- 💾 Database query: Use `python manage_db.py`

---

**Ready to scale your financial document analysis! 🚀**
