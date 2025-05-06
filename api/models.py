"""
Pydantic models for request and response data
"""

import os
import json
from typing import Optional, List
from pydantic import BaseModel

# Path to store fingerprint names
FINGERPRINT_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fingerprint_data.json')

class EnrollRequest(BaseModel):
    """Model for fingerprint enrollment request"""
    name: Optional[str] = None

class FingerprintData(BaseModel):
    """Model for fingerprint data"""
    position: int
    name: Optional[str] = None

class UpdateNameRequest(BaseModel):
    """Model for updating fingerprint name"""
    name: str

class EnrollResponse(BaseModel):
    """Model for fingerprint enrollment response"""
    success: bool
    position: Optional[int] = None
    message: str

class VerifyResponse(BaseModel):
    """Model for fingerprint verification response"""
    success: bool
    position: Optional[int] = None
    accuracy: Optional[int] = None
    message: str
    name: Optional[str] = None

class DeleteResponse(BaseModel):
    """Model for fingerprint deletion response"""
    success: bool
    position: Optional[int] = None
    message: str

class CountResponse(BaseModel):
    """Model for fingerprint count response"""
    count: int
    message: str

class StatusResponse(BaseModel):
    """Model for sensor status response"""
    connected: bool
    message: str

class FingerprintsResponse(BaseModel):
    """Model for getting all fingerprints"""
    fingerprints: List[FingerprintData]
    message: str

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    action: str
    data: Optional[dict] = None
    message: str

# Fingerprint data storage functions
def load_fingerprint_data() -> List[FingerprintData]:
    """Load fingerprint data from file"""
    try:
        if os.path.exists(FINGERPRINT_DATA_FILE):
            with open(FINGERPRINT_DATA_FILE, 'r') as f:
                data = json.load(f)
                return [FingerprintData(**item) for item in data]
        return []
    except Exception as e:
        print(f"Error loading fingerprint data: {e}")
        return []

def save_fingerprint_data(fingerprints: List[FingerprintData]) -> bool:
    """Save fingerprint data to file"""
    try:
        with open(FINGERPRINT_DATA_FILE, 'w') as f:
            json.dump([fp.dict() for fp in fingerprints], f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving fingerprint data: {e}")
        return False

def get_fingerprint_by_position(position: int) -> Optional[FingerprintData]:
    """Get fingerprint data by position"""
    fingerprints = load_fingerprint_data()
    for fp in fingerprints:
        if fp.position == position:
            return fp
    return None

def add_fingerprint(position: int, name: Optional[str] = None) -> bool:
    """Add or update a fingerprint"""
    fingerprints = load_fingerprint_data()

    # Check if fingerprint already exists
    for i, fp in enumerate(fingerprints):
        if fp.position == position:
            # Update existing fingerprint
            fingerprints[i].name = name
            return save_fingerprint_data(fingerprints)

    # Add new fingerprint
    fingerprints.append(FingerprintData(position=position, name=name))
    return save_fingerprint_data(fingerprints)

def update_fingerprint_name(position: int, name: str) -> bool:
    """Update fingerprint name"""
    fingerprints = load_fingerprint_data()

    # Find the fingerprint to update
    for i, fp in enumerate(fingerprints):
        if fp.position == position:
            # Update name
            fingerprints[i].name = name
            return save_fingerprint_data(fingerprints)

    # Fingerprint not found
    return False

def remove_fingerprint(position: int) -> bool:
    """Remove a fingerprint"""
    fingerprints = load_fingerprint_data()

    # Filter out the fingerprint to remove
    new_fingerprints = [fp for fp in fingerprints if fp.position != position]

    # Save if fingerprint was found and removed
    if len(new_fingerprints) < len(fingerprints):
        return save_fingerprint_data(new_fingerprints)

    # Fingerprint not found
    return False

def clear_all_fingerprints() -> bool:
    """Clear all fingerprints"""
    return save_fingerprint_data([])
