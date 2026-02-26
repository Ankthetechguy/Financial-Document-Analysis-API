"""
Configuration for Database and Celery
"""
import os
from pathlib import Path

# Database Configuration
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_analysis.db")
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Task Configuration
TASK_SERIALIZER = "json"
RESULT_SERIALIZER = "json"
ACCEPT_CONTENT = ["json"]
TIMEZONE = "UTC"
ENABLE_UTC = True

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# File Storage
DATA_DIR = "data"
OUTPUTS_DIR = "outputs"

# Ensure directories exist
Path(DATA_DIR).mkdir(exist_ok=True)
Path(OUTPUTS_DIR).mkdir(exist_ok=True)
