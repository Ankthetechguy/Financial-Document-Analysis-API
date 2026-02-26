"""
Database and integration test for the Financial Document Analyzer
Run this to verify everything is set up correctly before starting the API
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🔍 Testing imports...")
    
    required_modules = [
        "fastapi",
        "sqlalchemy",
        "celery",
        "redis",
        "crewai",
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {str(e)}")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing modules: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True


def test_database():
    """Test database initialization"""
    print("\n🔍 Testing database...")
    
    try:
        from database import SessionLocal, init_db, Base
        from models import AnalysisTask, UserAnalysisHistory, AnalysisMetrics
        
        # Initialize database
        init_db()
        print("  ✅ Database initialized")
        
        # Test session
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("  ✅ Database connection successful")
        
        # Test models
        assert hasattr(AnalysisTask, '__tablename__')
        assert hasattr(UserAnalysisHistory, '__tablename__')
        assert hasattr(AnalysisMetrics, '__tablename__')
        print("  ✅ All models loaded successfully")
        
        return True
    except Exception as e:
        print(f"  ❌ Database error: {str(e)}")
        return False


def test_celery():
    """Test Celery configuration"""
    print("\n🔍 Testing Celery...")
    
    try:
        from celery_app import celery_app, analyze_financial_document_task
        
        # Check app is configured
        assert celery_app.conf.broker_url
        print(f"  ✅ Celery broker configured: {celery_app.conf.broker_url}")
        
        # Check tasks are registered
        assert 'analyze_financial_document' in celery_app.tasks
        print("  ✅ Celery tasks registered")
        
        return True
    except Exception as e:
        print(f"  ❌ Celery error: {str(e)}")
        return False


def test_redis():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    
    try:
        import redis
        from config import CELERY_BROKER_URL
        
        # Parse Redis URL
        if "redis://" in CELERY_BROKER_URL:
            url_parts = CELERY_BROKER_URL.replace("redis://", "").split(":")
            host = url_parts[0]
            port = int(url_parts[1].split("/")[0])
        else:
            print(f"  ⚠️  Unexpected broker URL format: {CELERY_BROKER_URL}")
            return False
        
        # Try to connect
        r = redis.Redis(host=host, port=port, decode_responses=True)
        r.ping()
        print(f"  ✅ Redis connected: {host}:{port}")
        
        return True
    except Exception as e:
        print(f"  ❌ Redis error: {str(e)}")
        print("     Make sure Redis is running: redis-server")
        return False


def test_fastapi():
    """Test FastAPI app initialization"""
    print("\n🔍 Testing FastAPI...")
    
    try:
        from main import app
        
        # Check routes
        routes = [route.path for route in app.routes]
        required_routes = ["/", "/analyze", "/tasks", "/celery/health"]
        
        for route in required_routes:
            if route in routes:
                print(f"  ✅ Endpoint {route}")
            else:
                print(f"  ❌ Missing endpoint {route}")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ FastAPI error: {str(e)}")
        return False


def test_config():
    """Test configuration"""
    print("\n🔍 Testing configuration...")
    
    try:
        from config import DB_URL, CELERY_BROKER_URL, API_HOST, API_PORT
        
        print(f"  ✅ Database: {DB_URL}")
        print(f"  ✅ Broker: {CELERY_BROKER_URL}")
        print(f"  ✅ API: {API_HOST}:{API_PORT}")
        
        return True
    except Exception as e:
        print(f"  ❌ Config error: {str(e)}")
        return False


def test_files():
    """Test that all required files exist"""
    print("\n🔍 Testing required files...")
    
    required_files = [
        "main.py",
        "agents.py",
        "task.py",
        "tools.py",
        "database.py",
        "config.py",
        "models.py",
        "celery_app.py",
        "worker.py",
        "migrations.py",
        "client.py",
        "requirements.txt",
        "QUEUE_SETUP.md",
        "IMPLEMENTATION_SUMMARY.md",
    ]
    
    missing = []
    for filename in required_files:
        if Path(filename).exists():
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename}")
            missing.append(filename)
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Financial Document Analyzer - Integration Test")
    print("=" * 60)
    
    tests = [
        ("Files", test_files),
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Celery", test_celery),
        ("Redis", test_redis),
        ("FastAPI", test_fastapi),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {str(e)}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} - {name}")
    
    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to run the application:")
        print("\n  Terminal 1: redis-server")
        print("  Terminal 2: python main.py")
        print("  Terminal 3: python worker.py")
        print("\nThen test with:")
        print("  python client.py")
        print("  or visit: http://localhost:8000/docs\n")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
