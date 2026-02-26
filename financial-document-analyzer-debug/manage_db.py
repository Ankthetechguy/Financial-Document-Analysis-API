"""
Database and cache management utilities
Clean up old tasks, reset database, manage data
"""

import sys
from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import AnalysisTask, UserAnalysisHistory, AnalysisMetrics
import os

def reset_database():
    """Drop and recreate all database tables"""
    print("\n⚠️  WARNING: This will delete ALL data from the database!")
    confirm = input("Are you sure? (type 'yes' to confirm): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset complete")


def cleanup_old_tasks(days: int = 30):
    """Delete completed tasks older than N days"""
    db = SessionLocal()
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Find old completed tasks
    old_tasks = db.query(AnalysisTask).filter(
        AnalysisTask.status == "completed",
        AnalysisTask.completed_at < cutoff_date
    ).all()
    
    if not old_tasks:
        print(f"No tasks found older than {days} days")
        return
    
    count = len(old_tasks)
    print(f"Found {count} tasks older than {days} days")
    
    for task in old_tasks:
        # Clean up file if it exists
        if task.file_path and os.path.exists(task.file_path):
            try:
                os.remove(task.file_path)
                print(f"  Deleted file: {task.file_path}")
            except Exception as e:
                print(f"  Failed to delete {task.file_path}: {e}")
        
        # Delete related records
        history = db.query(UserAnalysisHistory).filter(
            UserAnalysisHistory.analysis_task_id == task.id
        ).all()
        for h in history:
            db.delete(h)
        
        metrics = db.query(AnalysisMetrics).filter(
            AnalysisMetrics.analysis_task_id == task.id
        ).all()
        for m in metrics:
            db.delete(m)
        
        # Delete task
        db.delete(task)
    
    db.commit()
    db.close()
    
    print(f"✅ Deleted {count} old tasks and related records")


def cleanup_failed_tasks():
    """Delete all failed tasks"""
    db = SessionLocal()
    
    failed_tasks = db.query(AnalysisTask).filter(
        AnalysisTask.status == "failed"
    ).all()
    
    if not failed_tasks:
        print("No failed tasks found")
        return
    
    count = len(failed_tasks)
    print(f"Found {count} failed tasks")
    
    for task in failed_tasks:
        # Clean up file
        if task.file_path and os.path.exists(task.file_path):
            try:
                os.remove(task.file_path)
            except:
                pass
        db.delete(task)
    
    db.commit()
    db.close()
    
    print(f"✅ Deleted {count} failed tasks")


def show_task_stats():
    """Display database statistics"""
    db = SessionLocal()
    
    total_tasks = db.query(AnalysisTask).count()
    pending_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == "pending").count()
    processing_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == "processing").count()
    completed_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == "completed").count()
    failed_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == "failed").count()
    
    # Get average processing time
    completed = db.query(AnalysisTask).filter(
        AnalysisTask.status == "completed",
        AnalysisTask.duration_seconds != None
    ).all()
    
    avg_duration = sum(t.duration_seconds for t in completed) / len(completed) if completed else 0
    
    print("\n📊 Database Statistics")
    print("-" * 40)
    print(f"Total tasks:     {total_tasks}")
    print(f"  Pending:       {pending_tasks}")
    print(f"  Processing:    {processing_tasks}")
    print(f"  Completed:     {completed_tasks}")
    print(f"  Failed:        {failed_tasks}")
    print(f"Avg duration:    {avg_duration:.2f}s")
    
    # User history stats
    history_count = db.query(UserAnalysisHistory).count()
    print(f"\nUser analyses:   {history_count}")
    
    # Metrics stats
    metrics_count = db.query(AnalysisMetrics).count()
    total_tokens = sum(m.tokens_used for m in db.query(AnalysisMetrics).all() if m.tokens_used)
    print(f"Metrics entries: {metrics_count}")
    print(f"Total tokens:    {total_tokens}")
    
    db.close()


def cleanup_redis():
    """Clear Redis cache"""
    try:
        import redis
        from config import CELERY_BROKER_URL
        
        # Parse Redis URL
        if "redis://" in CELERY_BROKER_URL:
            url_parts = CELERY_BROKER_URL.replace("redis://", "").split(":")
            host = url_parts[0]
            port = int(url_parts[1].split("/")[0])
            db_num = int(url_parts[1].split("/")[1]) if "/" in url_parts[1] else 0
        else:
            print("Could not parse Redis URL")
            return
        
        r = redis.Redis(host=host, port=port, db=db_num)
        
        # Get queue stats
        queue_size = r.llen('celery')
        print(f"\nRedis Queue: {queue_size} pending tasks")
        
        confirm = input("Clear Redis queue? (yes/no): ").strip().lower()
        if confirm == 'yes':
            r.flushdb()
            print("✅ Redis cache cleared")
        else:
            print("Cancelled")
    
    except Exception as e:
        print(f"❌ Error accessing Redis: {e}")


def export_data():
    """Export database to JSON"""
    import json
    
    db = SessionLocal()
    
    tasks = db.query(AnalysisTask).all()
    history = db.query(UserAnalysisHistory).all()
    
    data = {
        "tasks": [t.to_dict() for t in tasks],
        "history": [h.to_dict() for h in history],
    }
    
    # Convert datetime to string for JSON serialization
    def datetime_handler(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    filename = f"financial_analyzer_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=datetime_handler)
    
    print(f"✅ Data exported to {filename}")
    db.close()


def main():
    """Main menu"""
    print("\n" + "=" * 50)
    print("Financial Document Analyzer - Database Management")
    print("=" * 50)
    
    while True:
        print("\n🔧 Choose an action:")
        print("  1. Show task statistics")
        print("  2. Clean up old tasks (30+ days)")
        print("  3. Clean up failed tasks")
        print("  4. Clear Redis queue")
        print("  5. Export database to JSON")
        print("  6. Reset entire database (⚠️  DESTRUCTIVE)")
        print("  7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == "1":
            show_task_stats()
        elif choice == "2":
            days = input("Delete tasks older than (default 30) days: ").strip()
            cleanup_old_tasks(int(days) if days else 30)
        elif choice == "3":
            cleanup_failed_tasks()
        elif choice == "4":
            cleanup_redis()
        elif choice == "5":
            export_data()
        elif choice == "6":
            reset_database()
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
