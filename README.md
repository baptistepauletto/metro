# STM Metro Display

A proof-of-concept web application that displays real-time metro departure times for Montreal's STM network. Designed for a kiosk-style display on a Raspberry Pi.

![Preview](https://via.placeholder.com/800x400/050505/f58220?text=ROSEMONT+•+3+min)

## Features

- **Real-time countdown** to the next metro departure
- **Dark mode kiosk UI** optimized for distant viewing
- **Auto-refresh** every 30 seconds
- **Configurable** station, line, and direction
- **Fullscreen mode** for dedicated displays
- **Responsive design** works on any screen size

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to project directory
cd metro

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Station

Edit `backend/config.py` to set your station:

```python
STATION_NAME = "Rosemont"      # Your metro station
LINE_COLOR = "orange"          # orange, green, blue, or yellow
DIRECTION = "Côte-Vertu"       # Terminus station name
```

**Direction options by line:**
- **Orange Line:** `Côte-Vertu` or `Montmorency`
- **Green Line:** `Angrignon` or `Honoré-Beaugrand`
- **Blue Line:** `Snowdon` or `Saint-Michel`
- **Yellow Line:** `Berri-UQAM` or `Longueuil–Université-de-Sherbrooke`

### 3. Run the Server

```bash
cd backend
python main.py
```

The server will:
1. Download STM GTFS data automatically (first run only, ~15MB)
2. Load the schedule data into memory
3. Start the web server at `http://localhost:8000`

### 4. View the Display

Open your browser to: **http://localhost:8000**

Click the "Fullscreen" button for the best kiosk experience.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Serves the frontend display |
| `GET /api/config` | Returns current configuration |
| `GET /api/next-departures` | Returns upcoming departures |
| `GET /api/health` | Health check endpoint |

### Query Parameters for `/api/next-departures`

You can override the config with query parameters:

```
GET /api/next-departures?station=Berri-UQAM&line=green&direction=Angrignon&count=5
```

## Project Structure

```
metro/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── gtfs_parser.py    # GTFS data loading and querying
│   └── config.py         # Station/line configuration
├── frontend/
│   └── index.html        # Kiosk-style display
├── data/                  # GTFS data (auto-downloaded)
├── requirements.txt
└── README.md
```

## Deploying on Raspberry Pi

### Hardware Requirements
- Raspberry Pi 3B+ or newer
- MicroSD card (8GB+)
- HDMI display
- Power supply

### Setup Steps

1. Install Raspberry Pi OS (Lite or Desktop)
2. Clone this repository
3. Install Python dependencies
4. Set up auto-start on boot:

```bash
# Create systemd service
sudo nano /etc/systemd/system/metro-display.service
```

```ini
[Unit]
Description=STM Metro Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/metro/backend
ExecStart=/home/pi/metro/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable metro-display
sudo systemctl start metro-display
```

5. Open Chromium in kiosk mode:

```bash
chromium-browser --kiosk --noerrdialogs http://localhost:8000
```

## Upgrading to Real-Time Data

This POC uses STM's static GTFS schedule. For real-time updates:

1. Register at [STM Developer Portal](https://www.stm.info/fr/a-propos/developpeurs)
2. Get API access for GTFS-Realtime feed
3. Update `gtfs_parser.py` to fetch real-time trip updates

## Troubleshooting

### "No upcoming departures"
- Check if the station name matches exactly (case-insensitive)
- Verify the line color and direction are correct
- Metro service may have ended for the day

### GTFS data download fails
- Check your internet connection
- Try running `python gtfs_parser.py` directly to see error details

### Display not updating
- Check browser console for errors
- Verify the server is running (`/api/health` endpoint)

## License

MIT License - Feel free to use and modify for your own projects!

## Acknowledgments

- [STM](https://www.stm.info/) for providing open GTFS data
- [GTFS Specification](https://gtfs.org/) for the transit data standard

