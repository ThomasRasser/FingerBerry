"""
Background task handlers for fingerprint operations
"""

import os
import json
import threading
import asyncio
import time

from api.websocket import broadcast_message
from api.models import add_fingerprint, remove_fingerprint, clear_all_fingerprints, get_fingerprint_by_position
from fingerprint.r503manager import R503Manager, FingerStatus
from smarthome.smarthome import control_smart_plug, control_smartphone_light

# Sensor configuration
SENSOR_PORT = os.getenv("SENSOR_PORT", "/dev/ttyS0")
SENSOR_BAUDRATE = int(os.getenv("SENSOR_BAUDRATE", "57600"))

# Global fingerprint manager instance
fingerprint_manager = None
_continuous_thread = None  # thread handle for continuous verify
_stop_event = threading.Event()  # event to stop continuous loop

def get_manager():
    """
    Get or create the fingerprint manager
    Returns a connected R503Manager instance
    """
    global fingerprint_manager
    if not fingerprint_manager:
        fingerprint_manager = R503Manager(SENSOR_PORT, SENSOR_BAUDRATE)
        fingerprint_manager.connect()
    return fingerprint_manager

async def enroll_fingerprint_task(name=None):
    """
    Background task for fingerprint enrollment

    Args:
        name (str, optional): Name for the fingerprint
    """
    try:
        manager = get_manager()
        await broadcast_message(json.dumps({
            "type": "status",
            "status": "enrolling",
            "message": "Place your finger on the sensor for enrollment (first scan)"
        }))

        # The actual enrollment happens in the R503Manager
        success, position = manager.enroll_finger()

        if success:
            # Save the fingerprint with name
            add_fingerprint(position, name)

            await broadcast_message(json.dumps({
                "type": "status",
                "status": "success",
                "position": position,
                "message": f"Fingerprint enrolled successfully at position {position}" +
                          (f" with name '{name}'" if name else "")
            }))
            return {"success": True, "position": position, "message": f"Enrollment complete at position {position}"}
        else:
            if position is not None:
                await broadcast_message(json.dumps({
                    "type": "status",
                    "status": "failed",
                    "position": position,
                    "message": f"Fingerprint already exists at position {position}"
                }))
                return {"success": False, "position": position, "message": "Fingerprint already exists"}
            else:
                await broadcast_message(json.dumps({
                    "type": "status",
                    "status": "failed",
                    "message": "Enrollment failed"
                }))
                return {"success": False, "position": None, "message": "Enrollment failed"}
    except Exception as e:
        await broadcast_message(json.dumps({
            "type": "error",
            "message": f"Error during enrollment: {str(e)}"
        }))
        return {"success": False, "position": None, "message": f"Error: {str(e)}"}

async def verify_fingerprint_task():
    """Background task for fingerprint verification"""
    try:
        manager = get_manager()
        await broadcast_message(json.dumps({
            "type": "status",
            "status": "verifying",
            "message": "Place your finger on the sensor for verification"
        }))

        # The actual verification happens in the R503Manager
        success, position, accuracy = manager.verify_finger()

        if success:
            # Get the fingerprint name if available
            fingerprint = get_fingerprint_by_position(position)
            name = fingerprint.name if fingerprint else None
            action = fingerprint.action if fingerprint else None

            message = f"Fingerprint verified at position {position} with accuracy {accuracy}"
            if name:
                message += f" (Name: {name})"

            if action and action != "na":
                control_smart_plug(action)
                control_smartphone_light(action)

            await broadcast_message(json.dumps({
                "type": "status",
                "status": "success",
                "position": position,
                "accuracy": accuracy,
                "name": name,
                "message": message
            }))
            return {"success": True, "position": position, "accuracy": accuracy, "name": name, "message": "Verification successful"}
        else:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "failed",
                "message": "Fingerprint not found in database"
            }))
            return {"success": False, "position": None, "accuracy": None, "name": None, "message": "Fingerprint not found"}
    except Exception as e:
        await broadcast_message(json.dumps({
            "type": "error",
            "message": f"Error during verification: {str(e)}"
        }))
        return {"success": False, "position": None, "accuracy": None, "name": None, "message": f"Error: {str(e)}"}

def _continuous_loop():
    manager = get_manager()
    while not _stop_event.is_set():
        try:
            has_image = manager.finger.readImage()
            if has_image:
                manager.finger.convertImage(0x01)
                pos, accuracy = manager.finger.searchTemplate()
                status = "success" if pos >= 0 else "failed"
                fp = get_fingerprint_by_position(pos) if pos >= 0 else None
                name = fp.name if fp else None
                action = fp.action if fp else None

                if pos >= 0 and action and action != "na":
                    control_smart_plug(action)
                    control_smartphone_light(action)

                # Assemble message
                msg = {
                    "type": "continuous_verify",
                    "status": status,
                    "position": pos if pos >= 0 else None,
                    "accuracy": accuracy if pos >= 0 else None,
                    "name": name,
                    "message": f"{'Match' if pos>=0 else 'No match'} at {pos}"
                }
                # Send via websocket
                asyncio.run(broadcast_message(json.dumps(msg)))

                manager.wait_finger_removed()
            else:
                time.sleep(0.1)
        except Exception as e:
            asyncio.run(broadcast_message(json.dumps({
                "type": "error",
                "message": f"Continuous verify error: {e}"
            })))
            break


def start_continuous():
    """
    Called from FastAPI to kick off continuous verification loop
    """
    global _continuous_thread, _stop_event
    if _continuous_thread and _continuous_thread.is_alive():
        return False

    _stop_event.clear()
    get_manager()
    _continuous_thread = threading.Thread(target=_continuous_loop, daemon=True)
    _continuous_thread.start()
    return True


def stop_continuous():
    """
    Called from FastAPI to halt the continuous verification loop
    """
    _stop_event.set()
    return True

async def delete_fingerprint_task(position=None):
    """
    Background task for fingerprint deletion

    Args:
        position (int, optional): Position to delete, if None will scan finger
    """
    try:
        manager = get_manager()

        if position is not None:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "deleting",
                "position": position,
                "message": f"Deleting fingerprint at position {position}"
            }))

            # Get name before deletion if available
            fingerprint = get_fingerprint_by_position(position)
            name = fingerprint.name if fingerprint else None

            # Delete by position
            success = manager.delete_finger(position)

            if success:
                # Remove from our name storage as well
                remove_fingerprint(position)
        else:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "deleting",
                "message": "Place finger to delete from database"
            }))

            # Use verify-then-delete approach
            success, position, _ = manager.verify_finger()

            if success and position is not None:
                # Get name before deletion if available
                fingerprint = get_fingerprint_by_position(position)
                name = fingerprint.name if fingerprint else None

                await broadcast_message(json.dumps({
                    "type": "status",
                    "status": "deleting",
                    "position": position,
                    "message": f"Fingerprint found, deleting from position {position}"
                }))

                success = manager.delete_finger(position)

                if success:
                    # Remove from our name storage as well
                    remove_fingerprint(position)
            else:
                await broadcast_message(json.dumps({
                    "type": "status",
                    "status": "failed",
                    "message": "Fingerprint not found for deletion"
                }))
                return {"success": False, "position": None, "message": "Fingerprint not found for deletion"}

        if success:
            name_msg = f" (Name: {name})" if name else ""
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "success",
                "position": position,
                "message": f"Fingerprint deleted successfully from position {position}{name_msg}"
            }))
            return {"success": True, "position": position, "message": f"Fingerprint deleted from position {position}"}
        else:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "failed",
                "position": position if position is not None else None,
                "message": "Failed to delete fingerprint"
            }))
            return {"success": False, "position": position if position is not None else None, "message": "Failed to delete fingerprint"}
    except Exception as e:
        await broadcast_message(json.dumps({
            "type": "error",
            "message": f"Error during deletion: {str(e)}"
        }))
        return {"success": False, "position": None, "message": f"Error: {str(e)}"}

async def clear_database_task():
    """Background task for clearing fingerprint database"""
    try:
        manager = get_manager()
        await broadcast_message(json.dumps({
            "type": "status",
            "status": "clearing",
            "message": "Clearing all fingerprints from database..."
        }))

        # The actual clearing happens in the R503Manager
        success = manager.clear_database()

        if success:
            # Also clear our fingerprint names database
            clear_all_fingerprints()

            await broadcast_message(json.dumps({
                "type": "status",
                "status": "success",
                "message": "Database cleared successfully"
            }))
            return {"success": True, "message": "Database cleared successfully"}
        else:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "failed",
                "message": "Failed to clear database"
            }))
            return {"success": False, "message": "Failed to clear database"}
    except Exception as e:
        await broadcast_message(json.dumps({
            "type": "error",
            "message": f"Error clearing database: {str(e)}"
        }))
        return {"success": False, "message": f"Error: {str(e)}"}
