"""
Quick start guide - Run this to see what commands you need to execute

Usage:
    python quickstart.py

This will show you the setup instructions for different operating systems
"""

import sys
import os

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def main():
    print_section("Financial Document Analyzer - QUICK START")
    
    print("✓ Follow these steps in order:\n")
    
    # Step 1: Install dependencies
    print("1️⃣  INSTALL DEPENDENCIES")
    print("-" * 40)
    print("Run in current directory:")
    print("  pip install -r requirements.txt\n")
    
    # Step 2: Setup Redis
    print("2️⃣  START REDIS SERVER")
    print("-" * 40)
    
    system = sys.platform
    if system == "win32":
        print("Windows - Choose ONE:")
        print("  a) Docker: docker run -d -p 6379:6379 redis:latest")
        print("  b) WSL: wsl apt-get install redis-server && wsl redis-server")
        print("  c) Download from: https://github.com/microsoftarchive/redis/releases\n")
    elif system == "darwin":
        print("macOS:")
        print("  brew install redis")
        print("  brew services start redis  # or just: redis-server\n")
    else:  # Linux
        print("Linux:")
        print("  sudo apt-get install redis-server")
        print("  redis-server\n")
    
    # Step 3: Initialize database
    print("3️⃣  INITIALIZE DATABASE")
    print("-" * 40)
    print("Run in current directory:")
    print("  python migrations.py\n")
    
    # Step 4: Start services
    print("4️⃣  START THREE SERVICES (open 3 terminals)")
    print("-" * 40)
    
    print("\nTerminal 1 - Redis (if not using Docker):")
    print("  redis-server  # or already running\n")
    
    print("Terminal 2 - FastAPI Server:")
    print("  python main.py")
    print("  Accessible at: http://localhost:8000")
    print("  API docs: http://localhost:8000/docs\n")
    
    print("Terminal 3 - Celery Worker:")
    print("  python worker.py")
    print("  # or: celery -A celery_app worker --loglevel=info\n")
    
    # Step 5: Test the API
    print("5️⃣  TEST THE API")
    print("-" * 40)
    print("Use curl or the Swagger UI at http://localhost:8000/docs\n")
    
    print("Example with curl:")
    print("  curl -X POST http://localhost:8000/analyze \\")
    print('    -F "file=@your_document.pdf" \\')
    print('    -F "query=Analyze this financial report"\n')
    
    print("Or in Python:")
    print("""
import requests

with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {"query": "Analyze this document"}
    response = requests.post("http://localhost:8000/analyze", files=files, data=data)
    task_id = response.json()["task_id"]
    print(f"Task created: {task_id}")

# Check status
import time
time.sleep(5)
status = requests.get(f"http://localhost:8000/tasks/{task_id}").json()
print(f"Status: {status['status']}")

# Get result
result = requests.get(f"http://localhost:8000/tasks/{task_id}/result").json()
print(result["result"])
    """)
    
    # Troubleshooting
    print_section("TROUBLESHOOTING")
    
    print("❌ 'redis.exceptions.ConnectionError'")
    print("  → Redis is not running. Start it in a separate terminal.\n")
    
    print("❌ 'Column not found' error")
    print("  → Database needs initialization: python migrations.py\n")
    
    print("❌ 'Celery worker not processing tasks'")
    print("  → Make sure celery worker terminal is showing no errors.\n")
    
    print("❌ 'Task not found in database'")
    print("  → Verify the task_id is correct and database is initialized.\n")
    
    # Optional features
    print_section("OPTIONAL FEATURES")
    
    print("📊 Monitor Celery Tasks with Flower:")
    print("  pip install flower")
    print("  celery -A celery_app flower")
    print("  Open: http://localhost:5555\n")
    
    print("🗄️  SQL Database Queries:")
    print("""
from database import SessionLocal
from models import AnalysisTask

db = SessionLocal()
tasks = db.query(AnalysisTask).all()
for task in tasks:
    print(f"{task.id}: {task.status} - {task.file_name}")
    """)
    
    print("🔍 Redis Commands:")
    print("  redis-cli")
    print("  > KEYS *              # See all keys")
    print("  > LLEN celery         # Pending tasks")
    print("  > GET celery-task-id  # Task details\n")
    
    # Final note
    print_section("IMPORTANT NOTES")
    
    print("📍 Default Configuration:")
    print("  - Database: SQLite (financial_analysis.db)")
    print("  - Redis: localhost:6379")
    print("  - API Port: 8000")
    print("  - Workers: 2 concurrent\n")
    
    print("To customize, create/edit .env file:")
    print("  DATABASE_URL=sqlite:///./financial_analysis.db")
    print("  CELERY_BROKER_URL=redis://localhost:6379/0")
    print("  CELERY_RESULT_BACKEND=redis://localhost:6379/0\n")
    
    print("For detailed setup info, see: QUEUE_SETUP.md\n")
    
    print_section("You're ready to go! 🚀")
    print("Follow the steps above, then check the docs at /docs\n")

if __name__ == "__main__":
    main()
