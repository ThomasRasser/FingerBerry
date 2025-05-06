"""
Pydantic models for request and response data
"""

from typing import Optional
from pydantic import BaseModel

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

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages"""
    action: str
    data: Optional[dict] = None
    message: str
