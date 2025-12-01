"""
STM Metro Display - FastAPI Backend
====================================
Serves real-time metro departure information via REST API.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    STATION_NAME, LINE_COLOR, DIRECTION, NUM_DEPARTURES, HOST, PORT,
    STM_API_KEY, STM_GTFS_RT_URL, STM_SERVICE_ALERTS_URL,
    USE_REALTIME, SHOW_SERVICE_ALERTS
)
from gtfs_parser import get_parser
from service_alerts import get_service_alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize GTFS data on startup."""
    parser = get_parser()
    
    # Download GTFS data if not present
    if not parser.download_gtfs():
        print("Warning: Could not download GTFS data. API may not work correctly.")
    
    # Load data into memory
    if not parser.load_data():
        print("Warning: Could not load GTFS data. API may not work correctly.")
    
    # Log real-time status
    if USE_REALTIME:
        print("✓ Real-time data ENABLED (API key configured)")
    else:
        print("✗ Real-time data DISABLED (no API key - using schedule only)")
    
    if SHOW_SERVICE_ALERTS:
        print("✓ Service alerts ENABLED")
    else:
        print("✗ Service alerts DISABLED")
    
    yield
    
    # Cleanup (if needed)
    print("Shutting down...")


app = FastAPI(
    title="STM Metro Display",
    description="Real-time metro departure times for Montreal STM",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Serve the frontend HTML page."""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "STM Metro Display API", "docs": "/docs"}


@app.get("/api/config")
async def get_config():
    """Get the current configuration."""
    return {
        "station": STATION_NAME,
        "line": LINE_COLOR,
        "direction": DIRECTION,
        "num_departures": NUM_DEPARTURES,
        "realtime_enabled": USE_REALTIME,
        "alerts_enabled": SHOW_SERVICE_ALERTS
    }


@app.get("/api/next-departures")
async def get_next_departures(
    station: str = None,
    line: str = None,
    direction: str = None,
    count: int = None
):
    """
    Get the next metro departures for a station.
    
    Uses configuration defaults if parameters are not provided.
    Now includes real-time data if API key is configured.
    
    Returns:
        List of departures with time, minutes until arrival, and realtime flag
    """
    # Use config defaults if not specified
    station = station or STATION_NAME
    line = line or LINE_COLOR
    direction = direction or DIRECTION
    count = count or NUM_DEPARTURES
    
    parser = get_parser()
    
    if not parser._loaded:
        raise HTTPException(
            status_code=503,
            detail="GTFS data not loaded. Please wait or check server logs."
        )
    
    # Pass API credentials if real-time is enabled
    api_key = STM_API_KEY if USE_REALTIME else None
    gtfs_rt_url = STM_GTFS_RT_URL if USE_REALTIME else None
    
    departures = parser.get_next_departures(
        station_name=station,
        line_color=line,
        direction=direction,
        num_results=count,
        api_key=api_key,
        gtfs_rt_url=gtfs_rt_url
    )
    
    # Check if any departures have real-time data
    has_realtime = any(d.get("realtime", False) for d in departures)
    
    return {
        "station": station,
        "line": line,
        "direction": direction,
        "departures": departures,
        "count": len(departures),
        "realtime_active": has_realtime,
        "data_source": "realtime" if has_realtime else "schedule"
    }


@app.get("/api/alerts")
async def get_alerts(line: str = None):
    """
    Get service alerts for the metro.
    
    Args:
        line: Optional filter for specific line color
        
    Returns:
        List of service alerts affecting metro service
    """
    if not SHOW_SERVICE_ALERTS or not STM_API_KEY:
        return {
            "alerts": [],
            "count": 0,
            "enabled": False,
            "message": "Service alerts not enabled. Configure STM_API_KEY in .env"
        }
    
    line = line or LINE_COLOR
    
    alerts_service = get_service_alerts()
    alerts = alerts_service.get_metro_alerts(
        api_key=STM_API_KEY,
        alerts_url=STM_SERVICE_ALERTS_URL,
        line_color=line
    )
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "enabled": True,
        "line_filter": line
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    parser = get_parser()
    return {
        "status": "healthy",
        "gtfs_loaded": parser._loaded,
        "realtime_enabled": USE_REALTIME,
        "alerts_enabled": SHOW_SERVICE_ALERTS,
        "api_key_configured": bool(STM_API_KEY)
    }


# Mount static files for frontend assets (if any)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    
    realtime_status = "✓ ENABLED" if USE_REALTIME else "✗ DISABLED (no API key)"
    alerts_status = "✓ ENABLED" if SHOW_SERVICE_ALERTS else "✗ DISABLED"
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    STM Metro Display v2.0                    ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Station:    {STATION_NAME:<46} ║
    ║  Line:       {LINE_COLOR.capitalize():<46} ║
    ║  Direction:  {DIRECTION:<46} ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Real-time:  {realtime_status:<46} ║
    ║  Alerts:     {alerts_status:<46} ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Server:     http://{HOST}:{PORT:<38} ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)]
    )
