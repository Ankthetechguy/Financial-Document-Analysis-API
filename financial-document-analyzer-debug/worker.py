"""
Celery worker runner script
Run this in a separate terminal to start processing queued tasks

Usage:
    python worker.py

Or with Celery directly:
    celery -A celery_app worker --loglevel=info
"""

from celery_app import celery_app
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Celery worker...")
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2",
    ])
