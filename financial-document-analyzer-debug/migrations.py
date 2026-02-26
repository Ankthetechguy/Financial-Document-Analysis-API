"""
Alembic initialization and migration helper
Run migrations to create/update database schema
"""

import os
import sys
from sqlalchemy import create_engine
from alembic.config import Config
from alembic.command import init, stamp
from config import DB_URL
from database import Base
from models import AnalysisTask, UserAnalysisHistory, AnalysisMetrics

def init_alembic():
    """Initialize Alembic migrations directory"""
    if not os.path.exists("alembic"):
        alembic_cfg = Config()
        alembic_cfg.set_main_option("sqlalchemy.url", DB_URL)
        alembic_cfg.set_main_option("script_location", "alembic")
        init(alembic_cfg, "alembic")
        print("✓ Alembic initialized. Migrations directory created.")
    else:
        print("Alembic already initialized.")

def create_all_tables():
    """Create all tables directly (alternative to Alembic for development)"""
    engine = create_engine(DB_URL)
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully")
    engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_alembic()
    else:
        create_all_tables()
