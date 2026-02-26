from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import uuid
import asyncio
from datetime import datetime

from crewai import Crew, Process
from agents import financial_analyst, investment_advisor, risk_assessor, verifier
from task import analyze_financial_document, investment_analysis, risk_assessment, verification

# Database and Celery imports
from database import init_db, get_db
from models import AnalysisTask, UserAnalysisHistory, AnalysisMetrics
from celery_app import analyze_financial_document_task, celery_app

app = FastAPI(title="Financial Document Analyzer")

def run_crew(query: str, file_path: str="data/sample.pdf"):
    """To run the whole crew"""
    financial_crew = Crew(
        agents=[financial_analyst, investment_advisor, risk_assessor, verifier],
        tasks=[analyze_financial_document, investment_analysis, risk_assessment, verification],
        process=Process.sequential,
    )
    
    result = financial_crew.kickoff({'query': query})
    return result


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✓ Database initialized")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}

@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db)
):
    """
    Analyze financial document asynchronously using Celery workers.
    Returns a task ID to track progress.
    """
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate query
        if query == "" or query is None:
            query = "Analyze this financial document for investment insights"
        
        # Create task record in database
        task_record = AnalysisTask(
            file_name=file.filename,
            file_path=file_path,
            query=query.strip(),
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(task_record)
        db.commit()
        db.refresh(task_record)
        
        # Enqueue the analysis task
        celery_task = analyze_financial_document_task.delay(
            task_id=task_record.id,
            query=query.strip(),
            file_path=file_path
        )
        
        # Update task with Celery ID
        task_record.celery_task_id = celery_task.id
        db.commit()
        
        # Track user history
        history = UserAnalysisHistory(
            user_id=None,  # Can be set if you have user auth
            analysis_task_id=task_record.id,
            document_name=file.filename,
            analysis_type="investment"
        )
        db.add(history)
        db.commit()
        
        return {
            "status": "queued",
            "task_id": task_record.id,
            "celery_task_id": celery_task.id,
            "message": "Analysis queued. Use task_id to check status",
            "file_processed": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Get the status of an analysis task"""
    
    task_record = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not task_record:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Get Celery task status if available
    celery_status = None
    if task_record.celery_task_id:
        celery_task = celery_app.AsyncResult(task_record.celery_task_id)
        celery_status = {
            "state": celery_task.state,
            "info": celery_task.info,
        }
    
    response = task_record.to_dict()
    response["celery_status"] = celery_status
    return response


@app.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str, db: Session = Depends(get_db)):
    """Get the analysis result of a completed task"""
    
    task_record = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not task_record:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if task_record.status == "pending" or task_record.status == "processing":
        return {
            "task_id": task_id,
            "status": task_record.status,
            "message": "Task is still processing. Please try again later."
        }
    
    if task_record.status == "failed":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": task_record.error_message
        }
    
    return {
        "task_id": task_id,
        "status": "completed",
        "file_name": task_record.file_name,
        "query": task_record.query,
        "result": task_record.analysis_result,
        "completed_at": task_record.completed_at.isoformat() if task_record.completed_at else None,
        "duration_seconds": task_record.duration_seconds
    }


@app.get("/tasks")
async def list_tasks(
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all analysis tasks with optional filtering"""
    
    query = db.query(AnalysisTask)
    
    if status:
        query = query.filter(AnalysisTask.status == status)
    
    tasks = query.order_by(AnalysisTask.created_at.desc()).limit(limit).all()
    
    return {
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
    }


@app.get("/celery/health")
async def celery_health():
    """Check Celery worker health"""
    try:
        from celery_app import health_check
        result = health_check.delay()
        return {
            "status": "ok",
            "celery_task_id": result.id
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Celery worker unavailable: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)