# STM Metro Display Configuration
# ================================
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# =============================================================================
# Station Configuration
# Edit these values to match your station and preferred line/direction
# =============================================================================

# Your metro station name (must match GTFS data exactly)
STATION_NAME = "Rosemont"

# Metro line color: "orange", "green", "blue", "yellow"
LINE_COLOR = "orange"

# Direction of travel (terminus station name)
# Orange Line: "Côte-Vertu" or "Montmorency"
# Green Line: "Angrignon" or "Honoré-Beaugrand"
# Blue Line: "Snowdon" or "Saint-Michel"
# Yellow Line: "Berri-UQAM" or "Longueuil–Université-de-Sherbrooke"
DIRECTION = "Côte-Vertu"

# Number of upcoming departures to show
NUM_DEPARTURES = 3

# =============================================================================
# API Configuration (loaded from .env file)
# =============================================================================

# STM API Key (required for real-time data)
STM_API_KEY = os.getenv("STM_API_KEY", "")

# GTFS-Realtime endpoint for trip updates
STM_GTFS_RT_URL = os.getenv("STM_GTFS_RT_URL", "https://api.stm.info/pub/od/gtfs-rt/ic/v2")

# Service alerts endpoint
STM_SERVICE_ALERTS_URL = os.getenv("STM_SERVICE_ALERTS_URL", "https://api.stm.info/pub/od/i3/v2/messages")

# =============================================================================
# Server Configuration
# =============================================================================

HOST = "0.0.0.0"
PORT = 8000

# =============================================================================
# Feature Flags
# =============================================================================

# Use real-time data if API key is available, otherwise fall back to schedule
USE_REALTIME = bool(STM_API_KEY)

# Show service alerts on the display
SHOW_SERVICE_ALERTS = bool(STM_API_KEY)
