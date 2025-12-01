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

from config import STATION_NAME, LINE_COLOR, DIRECTION, NUM_DEPARTURES, HOST, PORT
from gtfs_parser import get_parser


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
    
    yield
    
    # Cleanup (if needed)
    print("Shutting down...")


app = FastAPI(
    title="STM Metro Display",
    description="Real-time metro departure times for Montreal STM",
    version="1.0.0",
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
        "num_departures": NUM_DEPARTURES
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
    
    Returns:
        List of departures with time and minutes until arrival
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
    
    departures = parser.get_next_departures(
        station_name=station,
        line_color=line,
        direction=direction,
        num_results=count
    )
    
    return {
        "station": station,
        "line": line,
        "direction": direction,
        "departures": departures,
        "count": len(departures)
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    parser = get_parser()
    return {
        "status": "healthy",
        "gtfs_loaded": parser._loaded
    }


# Mount static files for frontend assets (if any)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    STM Metro Display                         ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Station:   {STATION_NAME:<47} ║
    ║  Line:      {LINE_COLOR.capitalize():<47} ║
    ║  Direction: {DIRECTION:<47} ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Server starting at http://{HOST}:{PORT:<24} ║
    ║  Open in browser to see the display                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)]
    )

