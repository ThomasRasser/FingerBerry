"""
API routes and handlers for the fingerprint sensor
"""
import traceback
from fastapi import APIRouter, BackgroundTasks, HTTPException, Body
from typing import Optional

from api.models import (
    StatusResponse,
    EnrollResponse,
    VerifyResponse,
    DeleteResponse,
    CountResponse,
    FingerprintsResponse,
    FingerprintData,
    EnrollRequest,
    UpdateNameRequest,
    UpdateActionRequest,
    load_fingerprint_data,
    save_fingerprint_data,
    get_fingerprint_by_position,
    add_fingerprint,
    update_fingerprint_name,
    update_fingerprint_action,
    remove_fingerprint,
    clear_all_fingerprints
)
from api.background import (
    get_manager,
    enroll_fingerprint_task,
    verify_fingerprint_task,
    delete_fingerprint_task,
    clear_database_task,
    start_continuous,
    stop_continuous
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
async def enroll_fingerprint(background_tasks: BackgroundTasks, request: EnrollRequest = Body(default=None)):
    """Enroll a new fingerprint"""
    try:
        # Start the enrollment process in the background
        name = request.name if request else None
        background_tasks.add_task(enroll_fingerprint_task, name)
        return {"success": True, "position": None, "message": "Enrollment process started"}
    except Exception as e:
        return {"success": False, "position": None, "message": f"Error starting enrollment: {str(e)}"}

@router.post("/verify", response_model=VerifyResponse)
async def verify_fingerprint(background_tasks: BackgroundTasks):
    """Verify a fingerprint"""
    try:
        # Start the verification process in the background
        background_tasks.add_task(verify_fingerprint_task)
        return {"success": True, "position": None, "accuracy": None, "name": None, "message": "Verification process started"}
    except Exception as e:
        return {"success": False, "position": None, "accuracy": None, "name": None, "message": f"Error starting verification: {str(e)}"}

@router.post("/verify/continuous/start")
async def start_continuous_verify(background_tasks: BackgroundTasks):
    """Begin blinking and verifying in a loop until stopped"""
    background_tasks.add_task(start_continuous)
    return {"started": True, "message": "Continuous verification started"}

@router.post("/verify/continuous/stop")
async def stop_continuous_verify():
    """Halt the running continuous-verify loop"""
    stop_continuous()
    return {"stopped": True, "message": "Continuous verification stopped"}


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

@router.get("/fingerprints", response_model=FingerprintsResponse)
async def get_all_fingerprints():
    """Get all stored fingerprints with names"""
    try:
        # Get all fingerprints with names
        fingerprints = load_fingerprint_data()

        # Get the template count to validate fingerprints actually exist in the sensor
        manager = get_manager()
        count = manager.get_template_count()

        if count is None:
            raise HTTPException(status_code=500, detail="Failed to retrieve template count")

        positions = manager.get_stored_positions()
        name_map = {fp.position: fp.name for fp in load_fingerprint_data()}
        fingerprints = [FingerprintData(position=pos, name=name_map.get(pos)) for pos in positions]

        # Save updated list to JSON (adds new, keeps known names)
        save_fingerprint_data(fingerprints)

        return {
            "fingerprints": fingerprints,
            "message": f"Retrieved {len(fingerprints)} fingerprints"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving fingerprints: {str(e)}")

@router.put("/fingerprints/{position}/name", response_model=EnrollResponse)
async def set_fingerprint_name(position: int, request: UpdateNameRequest):
    """Update the name of a fingerprint"""
    try:
        # Update name in the database
        if update_fingerprint_name(position, request.name):
            return {
                "success": True,
                "position": position,
                "message": f"Updated name for fingerprint at position {position}"
            }
        else:
            # If fingerprint not found, add it
            add_fingerprint(position, request.name)
            return {
                "success": True,
                "position": position,
                "message": f"Added fingerprint at position {position} with name"
            }
    except Exception as e:
        return {
            "success": False,
            "position": position,
            "message": f"Error updating fingerprint name: {str(e)}"
        }

@router.put("/fingerprints/{position}/action", response_model=EnrollResponse)
async def set_fingerprint_action(position: int, request: UpdateActionRequest):
    """Update the action of a fingerprint"""
    try:
        if update_fingerprint_action(position, request.action):
            return {
                "success": True,
                "position": position,
                "message": f"Updated action for fingerprint at position {position}"
            }
        else:
            # If fingerprint not found, add it
            add_fingerprint(position, action=request.action)
            return {
                "success": True,
                "position": position,
                "message": f"Added fingerprint at position {position} with action"
            }
    except Exception as e:
        return {
            "success": False,
            "position": position,
            "message": f"Error updating fingerprint action: {str(e)}"
        }
