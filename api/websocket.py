"""
WebSocket connection manager for real-time updates
"""

import json
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Create router for WebSocket endpoints
websocket_router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        """Initialize the connection manager"""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client"""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Send a message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Remove failed connections
                self.disconnect(connection)

# Create a singleton instance of the connection manager
manager = ConnectionManager()

# Create a WebSocket endpoint
@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "message": "Connected to fingerprint sensor API"
            }),
            websocket
        )

        # Keep connection open and process incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                # Parse incoming JSON
                message = json.loads(data)
                # Echo back for now (can be expanded for custom commands)
                await manager.send_personal_message(
                    json.dumps({
                        "type": "echo",
                        "data": message,
                        "message": "Message received"
                    }),
                    websocket
                )
            except json.JSONDecodeError:
                # If not valid JSON, just echo as plain text
                await manager.send_personal_message(
                    json.dumps({
                        "type": "echo",
                        "data": data,
                        "message": "Received plain text message"
                    }),
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# Expose the broadcast method for use by other modules
async def broadcast_message(message: str):
    """Broadcast a message to all connected WebSocket clients"""
    await manager.broadcast(message)
