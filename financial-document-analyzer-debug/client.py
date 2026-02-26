"""
Client example for the Financial Document Analyzer API
Shows how to interact with the async analysis endpoints
"""

import requests
import time
import json
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"
POLL_INTERVAL = 5  # seconds between status checks
MAX_WAIT_TIME = 300  # maximum time to wait (5 minutes)


def submit_analysis(pdf_file_path: str, query: str = None) -> str:
    """
    Submit a document for analysis
    
    Returns:
        task_id: Unique identifier for tracking the analysis
    """
    if not Path(pdf_file_path).exists():
        print(f"❌ File not found: {pdf_file_path}")
        return None
    
    print(f"\n📄 Submitting analysis for: {pdf_file_path}")
    
    with open(pdf_file_path, "rb") as f:
        files = {"file": f}
        data = {}
        if query:
            data["query"] = query
        
        response = requests.post(f"{API_URL}/analyze", files=files, data=data)
    
    if response.status_code != 200:
        print(f"❌ Error submitting analysis: {response.text}")
        return None
    
    result = response.json()
    task_id = result["task_id"]
    print(f"✅ Analysis queued!")
    print(f"   Task ID: {task_id}")
    print(f"   Celery Task ID: {result['celery_task_id']}")
    
    return task_id


def check_status(task_id: str) -> dict:
    """
    Check the status of an analysis task
    
    Returns:
        Task status information
    """
    response = requests.get(f"{API_URL}/tasks/{task_id}")
    
    if response.status_code != 200:
        print(f"❌ Error checking status: {response.text}")
        return None
    
    return response.json()


def get_result(task_id: str) -> dict:
    """
    Get the analysis result
    
    Returns:
        Analysis result if completed, None if still processing
    """
    response = requests.get(f"{API_URL}/tasks/{task_id}/result")
    
    if response.status_code != 200:
        print(f"❌ Error getting result: {response.text}")
        return None
    
    return response.json()


def wait_for_completion(task_id: str, timeout: int = MAX_WAIT_TIME) -> bool:
    """
    Wait for an analysis to complete
    
    Returns:
        True if completed, False if timeout
    """
    print(f"\n⏳ Waiting for analysis to complete (timeout: {timeout}s)...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        status_info = check_status(task_id)
        if not status_info:
            return False
        
        status = status_info["status"]
        print(f"   Status: {status}")
        
        if status == "completed":
            print(f"✅ Analysis completed in {status_info.get('duration_seconds', 'N/A')} seconds")
            return True
        elif status == "failed":
            print(f"❌ Analysis failed: {status_info.get('error_message', 'Unknown error')}")
            return False
        
        time.sleep(POLL_INTERVAL)
    
    print(f"⏱️  Timeout reached after {timeout} seconds")
    return False


def list_all_tasks(status: str = None):
    """
    List all analysis tasks
    """
    params = {}
    if status:
        params["status"] = status
    
    response = requests.get(f"{API_URL}/tasks", params=params)
    
    if response.status_code != 200:
        print(f"❌ Error listing tasks: {response.text}")
        return
    
    result = response.json()
    print(f"\n📋 Found {result['count']} tasks:")
    
    for task in result["tasks"]:
        print(f"\n  ID: {task['id']}")
        print(f"  File: {task['file_name']}")
        print(f"  Status: {task['status']}")
        print(f"  Created: {task['created_at']}")


def check_api_health():
    """
    Check if API and Celery workers are running
    """
    try:
        # Check API
        response = requests.get(f"{API_URL}/")
        if response.status_code != 200:
            print("❌ API is not responding correctly")
            return False
        print("✅ API is running")
        
        # Check Celery
        response = requests.get(f"{API_URL}/celery/health")
        if response.status_code != 200:
            print("❌ Celery workers are not available")
            return False
        print("✅ Celery workers are running")
        
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API at http://localhost:8000")
        print("   Make sure the FastAPI server is running: python main.py")
        return False


def main():
    """
    Example usage of the API
    """
    print("=" * 60)
    print("Financial Document Analyzer - Client Example")
    print("=" * 60)
    
    # Check if services are running
    if not check_api_health():
        print("\n⚠️  Please make sure:")
        print("  1. Redis is running")
        print("  2. FastAPI server is running: python main.py")
        print("  3. Celery worker is running: python worker.py")
        return
    
    print("\n" + "=" * 60)
    
    # Interactive menu
    while True:
        print("\n🔧 Choose an action:")
        print("  1. Submit a document for analysis")
        print("  2. Check analysis status")
        print("  3. Get analysis result")
        print("  4. List all tasks")
        print("  5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            pdf_path = input("Enter PDF file path: ").strip()
            query = input("Enter analysis query (optional, press Enter to skip): ").strip()
            task_id = submit_analysis(pdf_path, query if query else None)
            if task_id:
                print(f"\n💾 Task ID saved. You can check status with: {task_id}")
        
        elif choice == "2":
            task_id = input("Enter Task ID: ").strip()
            status_info = check_status(task_id)
            if status_info:
                print("\n📊 Task Status:")
                print(json.dumps(status_info, indent=2, default=str))
        
        elif choice == "3":
            task_id = input("Enter Task ID: ").strip()
            wait_for_completion(task_id)
            result = get_result(task_id)
            if result:
                print("\n📋 Analysis Result:")
                print(json.dumps(result, indent=2, default=str))
        
        elif choice == "4":
            status_filter = input("Filter by status (pending/processing/completed/failed, or press Enter for all): ").strip()
            list_all_tasks(status_filter if status_filter else None)
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
