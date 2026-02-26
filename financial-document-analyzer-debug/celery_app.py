"""
Celery configuration and async tasks for financial document analysis
"""
from celery import Celery
from celery.utils.log import get_task_logger
from config import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    TASK_SERIALIZER,
    RESULT_SERIALIZER,
    ACCEPT_CONTENT,
    TIMEZONE,
    ENABLE_UTC,
)
from datetime import datetime
import traceback
import os

# Initialize Celery app
celery_app = Celery(
    "financial_analyzer",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer=TASK_SERIALIZER,
    result_serializer=RESULT_SERIALIZER,
    accept_content=ACCEPT_CONTENT,
    timezone=TIMEZONE,
    enable_utc=ENABLE_UTC,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="analyze_financial_document")
def analyze_financial_document_task(self, task_id: str, query: str, file_path: str):
    """
    Async task to analyze financial document using CrewAI
    
    Args:
        task_id: Database task ID for tracking
        query: Analysis query from user
        file_path: Path to the uploaded file
    
    Returns:
        Analysis result and updates database
    """
    from database import SessionLocal
    from models import AnalysisTask
    
    db = SessionLocal()
    task_record = None
    
    try:
        # Update task status to processing
        task_record = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task_record:
            logger.error(f"Task record not found: {task_id}")
            return {"error": "Task record not found"}
        
        task_record.status = "processing"
        task_record.started_at = datetime.utcnow()
        task_record.celery_task_id = self.request.id
        db.commit()
        
        logger.info(f"Starting analysis for task {task_id} with query: {query}")
        
        # Update progress
        self.update_state(state="PROCESSING", meta={"current": 0, "total": 100, "status": "Initializing crew..."})
        
        # Import here to avoid circular imports
        from main import run_crew
        
        # Run the crew analysis
        self.update_state(state="PROCESSING", meta={"current": 50, "total": 100, "status": "Running crew analysis..."})
        result = run_crew(query=query, file_path=file_path)
        
        # Store the result
        task_record.analysis_result = {"analysis": str(result)}
        task_record.status = "completed"
        task_record.completed_at = datetime.utcnow()
        
        # Calculate duration
        if task_record.started_at:
            duration = (datetime.utcnow() - task_record.started_at).total_seconds()
            task_record.duration_seconds = duration
        
        db.commit()
        
        logger.info(f"Task {task_id} completed successfully")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": str(result),
        }
        
    except Exception as e:
        logger.error(f"Error in analysis task {task_id}: {str(e)}\n{traceback.format_exc()}")
        
        if task_record:
            task_record.status = "failed"
            task_record.error_message = f"{str(e)}\n{traceback.format_exc()}"
            task_record.completed_at = datetime.utcnow()
            
            if task_record.started_at:
                duration = (datetime.utcnow() - task_record.started_at).total_seconds()
                task_record.duration_seconds = duration
            
            db.commit()
        
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }
    
    finally:
        db.close()


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files(file_path: str):
    """
    Clean up temporary uploaded files
    
    Args:
        file_path: Path to the file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")


@celery_app.task(name="health_check")
def health_check():
    """
    Simple health check task to ensure worker is running
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
