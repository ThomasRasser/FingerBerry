"""
Background task handlers for fingerprint operations
"""

import os
import sys
import json
from api.websocket import broadcast_message

from fingerprint.r503manager import R503Manager, FingerStatus

# Sensor configuration
SENSOR_PORT = os.getenv("SENSOR_PORT", "/dev/ttyS0")
SENSOR_BAUDRATE = int(os.getenv("SENSOR_BAUDRATE", "57600"))

# Global fingerprint manager instance
fingerprint_manager = None

def get_manager():
    """
    Get or create the fingerprint manager
    Returns a connected R503Manager instance
    """
    global fingerprint_manager
    if not fingerprint_manager:
        fingerprint_manager = EnhancedR503Manager(SENSOR_PORT, SENSOR_BAUDRATE)
        fingerprint_manager.connect()
    return fingerprint_manager

class EnhancedR503Manager(R503Manager):
    """
    Enhanced version of R503Manager that integrates with WebSockets
    for real-time status updates
    """

    async def notify(self, status_type, status, message, **kwargs):
        """Send a notification to all connected WebSocket clients"""
        data = {
            "type": status_type,
            "status": status,
            "message": message,
            **kwargs
        }
        await broadcast_message(json.dumps(data))

    async def wait_for_finger_with_updates(self):
        """Wait for finger with WebSocket updates"""
        await self.notify("status", "waiting", "Waiting for finger placement...")
        result = self.wait_for_finger()
        return result

    async def wait_finger_removed_with_updates(self):
        """Wait for finger removal with WebSocket updates"""
        await self.notify("status", "waiting", "Please remove your finger...")
        result = self.wait_finger_removed()
        return result

async def enroll_fingerprint_task():
    """Background task for fingerprint enrollment"""
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
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "success",
                "position": position,
                "message": f"Fingerprint enrolled successfully at position {position}"
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
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "success",
                "position": position,
                "accuracy": accuracy,
                "message": f"Fingerprint verified at position {position} with accuracy {accuracy}"
            }))
            return {"success": True, "position": position, "accuracy": accuracy, "message": "Verification successful"}
        else:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "failed",
                "message": "Fingerprint not found in database"
            }))
            return {"success": False, "position": None, "accuracy": None, "message": "Fingerprint not found"}
    except Exception as e:
        await broadcast_message(json.dumps({
            "type": "error",
            "message": f"Error during verification: {str(e)}"
        }))
        return {"success": False, "position": None, "accuracy": None, "message": f"Error: {str(e)}"}

async def delete_fingerprint_task(position=None):
    """Background task for fingerprint deletion"""
    try:
        manager = get_manager()

        if position is not None:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "deleting",
                "position": position,
                "message": f"Deleting fingerprint at position {position}"
            }))

            # Delete by position
            success = manager.delete_finger(position)
        else:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "deleting",
                "message": "Place finger to delete from database"
            }))

            # Use verify-then-delete approach
            success, position, _ = manager.verify_finger()
            if success and position is not None:
                success = manager.delete_finger(position)
            else:
                await broadcast_message(json.dumps({
                    "type": "status",
                    "status": "failed",
                    "message": "Fingerprint not found for deletion"
                }))
                return {"success": False, "position": None, "message": "Fingerprint not found for deletion"}

        if success:
            await broadcast_message(json.dumps({
                "type": "status",
                "status": "success",
                "position": position,
                "message": f"Fingerprint deleted successfully from position {position}"
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
