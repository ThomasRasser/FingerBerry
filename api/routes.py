"""
API routes and handlers for the fingerprint sensor
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional

from api.models import (
    StatusResponse,
    EnrollResponse,
    VerifyResponse,
    DeleteResponse,
    CountResponse
)
from api.background import (
    get_manager,
    enroll_fingerprint_task,
    verify_fingerprint_task,
    delete_fingerprint_task,
    clear_database_task
)

# Create API router
router = APIRouter()

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Check if sensor is connected and working"""
    try:
        manager = get_manager()
        count = manager.get_template_count()
        if count is not None:
            return {"connected": True, "message": f"Sensor connected. {count} fingerprints stored."}
        else:
            return {"connected": False, "message": "Sensor is not responding correctly"}
    except Exception as e:
        return {"connected": False, "message": f"Error connecting to sensor: {str(e)}"}

@router.post("/enroll", response_model=EnrollResponse)
async def enroll_fingerprint(background_tasks: BackgroundTasks):
    """Enroll a new fingerprint"""
    try:
        # Start the enrollment process in the background
        background_tasks.add_task(enroll_fingerprint_task)
        return {"success": True, "position": None, "message": "Enrollment process started"}
    except Exception as e:
        return {"success": False, "position": None, "message": f"Error starting enrollment: {str(e)}"}

@router.post("/verify", response_model=VerifyResponse)
async def verify_fingerprint(background_tasks: BackgroundTasks):
    """Verify a fingerprint"""
    try:
        # Start the verification process in the background
        background_tasks.add_task(verify_fingerprint_task)
        return {"success": True, "position": None, "accuracy": None, "message": "Verification process started"}
    except Exception as e:
        return {"success": False, "position": None, "accuracy": None, "message": f"Error starting verification: {str(e)}"}

@router.post("/delete/{position}", response_model=DeleteResponse)
async def delete_fingerprint(position: int, background_tasks: BackgroundTasks):
    """Delete a fingerprint by position"""
    try:
        # Start the deletion process in the background
        background_tasks.add_task(delete_fingerprint_task, position)
        return {"success": True, "position": position, "message": f"Deletion process started for position {position}"}
    except Exception as e:
        return {"success": False, "position": position, "message": f"Error starting deletion: {str(e)}"}

@router.post("/delete", response_model=DeleteResponse)
async def delete_fingerprint_by_scan(background_tasks: BackgroundTasks):
    """Delete a fingerprint by scanning it first"""
    try:
        # Start the deletion process in the background
        background_tasks.add_task(delete_fingerprint_task)
        return {"success": True, "position": None, "message": "Deletion process started - scan finger to delete"}
    except Exception as e:
        return {"success": False, "position": None, "message": f"Error starting deletion: {str(e)}"}

@router.get("/count", response_model=CountResponse)
async def get_count():
    """Get number of stored fingerprints"""
    try:
        manager = get_manager()
        count = manager.get_template_count()
        if count is not None:
            return {"count": count, "message": f"Number of stored fingerprints: {count}"}
        else:
            return {"count": 0, "message": "Failed to retrieve template count"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/clear", response_model=DeleteResponse)
async def clear_database(background_tasks: BackgroundTasks):
    """Clear all fingerprints from the database"""
    try:
        # Start the clear process in the background
        background_tasks.add_task(clear_database_task)
        return {"success": True, "message": "Database clearing process started"}
    except Exception as e:
        return {"success": False, "message": f"Error starting database clear: {str(e)}"}
