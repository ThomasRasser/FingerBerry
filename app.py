#!/usr/bin/python3
"""
Main entry point for the FastAPI Fingerprint Sensor web interface
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Import the API components
from api.routes import router
from api.websocket import websocket_router

# Create the FastAPI app
app = FastAPI(
    title="Fingerprint Sensor API",
    description="Web interface for R503 fingerprint sensor",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files - direct to the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount API routes
app.include_router(router, prefix="/api")
app.include_router(websocket_router)

# Environment variables for configuration
SENSOR_PORT = os.getenv("SENSOR_PORT", "/dev/ttyS0")
SENSOR_BAUDRATE = int(os.getenv("SENSOR_BAUDRATE", "57600"))

# Redirect root to index.html
@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="/static/index.html")

# Run the application
if __name__ == "__main__":
    print(f"Starting fingerprint API on port 8000")
    print(f"Sensor configured: Port={SENSOR_PORT}, Baudrate={SENSOR_BAUDRATE}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
