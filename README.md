# LED Matrix Display - Montreal Metro

A real-time metro departure countdown display for the **Adafruit Matrix Portal** with 64×32 LED matrix. Shows the next metro departure time based on STM schedule data.

**No server required!** Schedule runs standalone on the Matrix Portal hardware.

![Matrix Portal Display](https://via.placeholder.com/640x320/000000/ff6b00?text=ROSEMONT+%E2%80%A2+5+MIN)

## 🎯 Features

- ✅ **64×32 LED Matrix** - Perfect for Adafruit Matrix Portal M4
- ✅ **Standalone Operation** - No server needed, runs completely on-device
- ✅ **Web Simulator** - Test your display in browser before deploying
- ✅ **Static GTFS Schedule** - Load once, runs for months
- ✅ **Line Color Coding** - Orange, Green, Blue, or Yellow metro lines
- ✅ **WiFi Time Sync** - Accurate countdown using network time
- ✅ **Simple Updates** - Regenerate schedule 2-4 times per year

## 🚀 Quick Start

### 1. Setup Your Computer

```bash
# Clone or download this project
cd metro

# Install Python dependencies (for schedule builder)
pip install -r requirements.txt
```

### 2. Download GTFS Data

STM (Montreal transit) publishes their schedule data in GTFS format:

1. Visit [STM Developers Portal](https://www.stm.info/en/about/developers)
2. Download the GTFS static data ZIP file
3. Extract all `.txt` files to the `data/` folder

The `data/` folder should contain:
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `calendar_dates.txt`

### 3. Configure Your Station

Edit `build_schedule.py` to set your station and line:

```python
STATION_NAME = "Rosemont"      # Your metro station
LINE_NUMBER = "2"              # 1=Green, 2=Orange, 4=Yellow, 5=Blue
DIRECTION = "Côte-Vertu"       # Direction of travel (terminus name)
```

**Direction options by line:**
- **Orange Line (2):** `Côte-Vertu` or `Montmorency`
- **Green Line (1):** `Angrignon` or `Honoré-Beaugrand`
- **Blue Line (5):** `Snowdon` or `Saint-Michel`
- **Yellow Line (4):** `Berri-UQAM` or `Longueuil–Université-de-Sherbrooke`

### 4. Build Your Schedule

```bash
python build_schedule.py
```

This creates `schedule.json` - a compact file with all departure times for your station.

**When to rebuild:**
- When STM updates their schedule (typically 2-4 times per year)
- After major service changes or holidays
- When switching to a different station

### 5. Test in Simulator

Open `simulator/index.html` in your browser:

1. Click "Choose File" and load your `schedule.json`
2. Adjust the test minutes to see different countdowns
3. Use the scale slider to zoom in/out

This shows **exactly** what will appear on your Matrix Portal!

### 6. Deploy to Matrix Portal

See [`circuitpython/README.md`](circuitpython/README.md) for complete hardware setup instructions.

**Quick version:**
1. Install CircuitPython on your Matrix Portal
2. Copy required libraries to `CIRCUITPY/lib/`
3. Copy `circuitpython/code.py` to `CIRCUITPY/`
4. Copy `circuitpython/secrets.py` to `CIRCUITPY/` (edit with your WiFi)
5. Copy `schedule.json` to `CIRCUITPY/`
6. Done! Display starts automatically

## 📁 Project Structure

```
metro/
├── build_schedule.py        # GTFS → JSON converter (run on computer)
├── schedule.json            # Generated schedule data (copy to Matrix Portal)
├── requirements.txt         # Python dependencies for build script
│
├── data/                    # GTFS data files (download from STM)
│   ├── stops.txt
│   ├── routes.txt
│   ├── trips.txt
│   ├── stop_times.txt
│   └── ...
│
├── simulator/               # Web-based display simulator
│   └── index.html          # Open in browser to test
│
├── circuitpython/          # Code for Matrix Portal hardware
│   ├── code.py            # Main program (copy to CIRCUITPY)
│   ├── secrets.py         # WiFi config (edit and copy)
│   └── README.md          # Hardware setup instructions
│
└── README.md               # This file
```

## 🔧 How It Works

### Architecture

```
┌──────────────────┐         ┌─────────────────┐
│   Your Computer  │         │  Matrix Portal  │
│                  │         │  (CircuitPython) │
│  1. Download     │         │                  │
│     GTFS data    │         │  1. Load JSON    │
│                  │   USB   │  2. Get WiFi time│
│  2. Run build    ├────────►│  3. Find next    │
│     script       │  Copy   │     departure    │
│                  │  Files  │  4. Display      │
│  3. Generate     │         │     countdown    │
│     schedule.json│         │  5. Repeat       │
└──────────────────┘         └─────────────────┘

   Run 2-4x/year              Runs 24/7
```

### Schedule File Format

The `schedule.json` file contains pre-computed departure times:

```json
{
  "station": "Rosemont",
  "line": "2",
  "direction": "Côte-Vertu",
  "generated": "2026-01-27T12:00:00",
  "schedule": {
    "monday": ["06:00", "06:05", "06:10", ..., "00:55"],
    "tuesday": ["06:00", "06:05", ...],
    ...
  }
}
```

The Matrix Portal:
1. Loads this file from storage
2. Gets current time via WiFi (NTP)
3. Finds next departure from the list
4. Calculates and displays countdown
5. No server or API calls needed!

## 🎨 Display Layout (64×32)

```
Row 0-7:   STATION NAME (centered, line color)
Row 9:     ═══════════ (line color separator)
Row 13-19: ## (large countdown number)
Row 24-30: MIN (dimmed label)
```

## 🔌 Hardware Requirements

- **Adafruit Matrix Portal M4** (~$25 USD)
- **64×32 RGB LED Matrix Panel** with HUB75 interface (~$30-50 USD)
- **5V 4A Power Supply** for the matrix (~$10 USD)
- **USB-C Cable** for programming

Total cost: ~$70-90 USD

**Where to buy:**
- [Adafruit](https://www.adafruit.com/product/4745) - Matrix Portal
- [Adafruit](https://www.adafruit.com/product/2278) - 64x32 Matrix

## 📊 Data Source

This project uses STM's official GTFS (General Transit Feed Specification) data:

- **Download:** [stm.info/en/about/developers](https://www.stm.info/en/about/developers)
- **Format:** GTFS Static (schedule data)
- **Updates:** Quarterly or as announced by STM
- **License:** Check STM's terms of use

## 🐛 Troubleshooting

### Schedule Builder Issues

**"Station not found"**
- Check spelling matches GTFS data exactly
- Try partial names (e.g., "Rose" instead of "Rosemont")
- Check `data/stops.txt` for exact station names

**"No trips found"**
- Verify LINE_NUMBER is correct (1, 2, 4, or 5)
- Check DIRECTION matches a terminus name
- Look in `data/routes.txt` and `data/trips.txt`

**"No departure times"**
- Ensure GTFS data is complete
- Check calendar.txt has service_ids
- Verify stop_times.txt is not empty

### Simulator Issues

**Blank display**
- Clear browser cache and reload
- Check browser console (F12) for errors
- Verify schedule.json is valid JSON

### Hardware Issues

See [`circuitpython/README.md`](circuitpython/README.md) for Matrix Portal troubleshooting.

## 🔄 Updating Schedule

When STM releases new GTFS data:

1. Download new GTFS files to `data/`
2. Run `python build_schedule.py`
3. Copy new `schedule.json` to Matrix Portal via USB
4. Reboot Matrix Portal (press reset button)

**That's it!** No code changes needed.

## ⚙️ Customization

### Change Station or Line

Edit `build_schedule.py` and rebuild:

```python
STATION_NAME = "Berri-UQAM"    # Your station
LINE_NUMBER = "2"               # Your line
DIRECTION = "Montmorency"       # Your direction
```

### Adjust Display Brightness

Edit `circuitpython/code.py`:

```python
BRIGHTNESS = 0.3  # 0.0 (off) to 1.0 (max)
```

### Change Line Colors

Edit `circuitpython/code.py`:

```python
LINE_COLORS = {
    "2": (217, 87, 0),  # Orange - change RGB values
    ...
}
```

### Change Update Frequency

Edit `circuitpython/code.py`:

```python
UPDATE_INTERVAL = 30  # Seconds between display updates
```

## 🌟 Why Standalone?

**Pros:**
✅ No server to maintain 24/7  
✅ No monthly hosting costs  
✅ Works offline (after WiFi time sync)  
✅ Simple to set up  
✅ Fast and reliable  
✅ Low power consumption

**Cons:**
❌ No real-time delay updates (schedule only)  
❌ Must manually update schedule periodically  
❌ No service alerts or disruptions

**Perfect for:** Home projects, personal use, metro stations with reliable schedules

## 🚧 Future Enhancements

- [ ] Scrolling text for long station names
- [ ] Show multiple upcoming departures
- [ ] Service alert icons (via optional API)
- [ ] Brightness auto-adjust (time of day)
- [ ] Sleep mode during off-hours
- [ ] Support for multiple stations
- [ ] Web interface for remote config

## 📝 License

MIT License - Free to use and modify for personal projects.

## 🙏 Acknowledgments

- [STM](https://www.stm.info/) for providing open GTFS data
- [Adafruit](https://www.adafruit.com/) for the Matrix Portal hardware
- [GTFS Specification](https://gtfs.org/) for the transit data standard
- Montreal metro riders 🚇

## 💡 Tips

- **Test first:** Always test in the simulator before deploying to hardware
- **Backup:** Keep a copy of your working `schedule.json`
- **Updates:** Set a reminder to check for GTFS updates quarterly
- **Power:** Use a quality 5V power supply - cheap ones cause flickering
- **WiFi:** Matrix Portal only supports 2.4GHz WiFi, not 5GHz

---

**Made with 🚇 for Montreal metro riders**

**Need help?** Check the detailed hardware guide in [`circuitpython/README.md`](circuitpython/README.md)
