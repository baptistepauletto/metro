# 3-Line Scrolling Display - Deployment Guide

Complete guide to deploying your 3-line scrolling display showing metro countdown, stock prices, and current time.

## Overview

Your display now shows three continuously scrolling lines:
- **Line 1**: Metro countdown (e.g., "METRO: ROSEMONT • 8 MIN")
- **Line 2**: Stock price (e.g., "STOCK: XEQT $37.83 +1.2% • CLOSED")
- **Line 3**: Current time (e.g., "TIME: 15:30 • FEB 8")

Data is automatically updated every 5 minutes via GitHub Actions.

## Architecture

```
GitHub Actions → GitHub Pages (data.json) → Matrix Portal → LED Display
   (every 5 min)      (HTTPS)               (fetches & scrolls)
```

## Prerequisites

- [x] Adafruit Matrix Portal M4 with 64x32 LED matrix
- [x] CircuitPython installed on Matrix Portal
- [x] GitHub repository with Actions enabled
- [x] Required CircuitPython libraries installed
- [x] WiFi credentials configured in `secrets.py`

## Step-by-Step Deployment

### Phase 1: GitHub Setup (30 minutes)

#### 1.1 Push Code to GitHub

```bash
cd metro

# Add all new files
git add .

# Commit
git commit -m "Add 3-line scrolling display with GitHub Actions"

# Push to GitHub
git push origin master
```

#### 1.2 Enable GitHub Pages

Follow the guide in [`GITHUB_PAGES_SETUP.md`](GITHUB_PAGES_SETUP.md):

1. Go to **Settings → Pages**
2. Select **Source**: `gh-pages` branch, `/ (root)` folder
3. Save

#### 1.3 Verify GitHub Actions

1. Go to **Actions** tab on GitHub
2. You should see "Update Display Data" workflow running
3. Wait for it to complete (green checkmark)
4. Click on the workflow run to view logs

#### 1.4 Test Data Endpoint

Visit: `https://YOUR_USERNAME.github.io/metro/data.json`

You should see JSON like:
```json
{
  "updated": "2026-02-08T20:30:00Z",
  "metro": { ... },
  "stock": { ... },
  "time": { ... }
}
```

**If you see 404**: Wait 2-3 minutes for GitHub Pages to deploy, then refresh.

### Phase 2: Matrix Portal Deployment (15 minutes)

#### 2.1 Install Required Libraries

If not already installed, copy these to `CIRCUITPY/lib/`:

- `adafruit_matrixportal/` (folder)
- `adafruit_display_text/` (folder)
- `adafruit_requests.mpy`
- `adafruit_esp32spi/` (folder)
- `neopixel.mpy`

Download from: [CircuitPython Library Bundle](https://circuitpython.org/libraries)

#### 2.2 Update GitHub Pages URL

Edit `circuitpython/code.py` line 35 with your GitHub username:

```python
DATA_URL = "https://YOUR_USERNAME.github.io/metro/data.json"
```

#### 2.3 Copy Files to Matrix Portal

Connect your Matrix Portal via USB. The `CIRCUITPY` drive should appear.

Copy these files:

```bash
# Required files
CIRCUITPY/
├── code.py           ← Copy from circuitpython/code.py (NEW version)
├── secrets.py        ← Your WiFi credentials (unchanged)
└── schedule.json     ← Fallback data (unchanged)
```

**Backup your old code**: The original metro code is saved as `code_metro.py`

#### 2.4 Verify WiFi Credentials

Check `CIRCUITPY/secrets.py`:

```python
secrets = {
    'ssid': 'YourWiFiName',
    'password': 'YourWiFiPassword',
    'timezone': "America/Montreal",
}
```

### Phase 3: Testing (30 minutes)

#### 3.1 Monitor Serial Console

Connect to serial console to watch startup:

**Windows (Mu Editor)**:
1. Open Mu Editor
2. Click "Serial" button
3. Watch for startup messages

**Mac/Linux**:
```bash
screen /dev/tty.usbmodem* 115200
```

**Expected output**:
```
============================================================
3-Line Scrolling Display - Starting
============================================================
Free memory at startup: 28340 bytes
Syncing time...
Time synced successfully
Fetching data from GitHub Pages...
Free memory before request: 27820 bytes
Data fetched successfully!
Updated: 2026-02-08T20:30:00Z
Free memory after request: 26940 bytes
Display initialized!
Line 1: METRO: ROSEMONT • 8 MIN
Line 2: STOCK: XEQT $37.83 +1.2% • CLOSED
Line 3: TIME: 15:30 • FEB 8
```

#### 3.2 Visual Verification

On the LED display, you should see:
- ✅ Three lines of text scrolling horizontally from right to left
- ✅ Orange/yellow text for metro (top line)
- ✅ Green or red text for stock (middle line) - green if up, red if down
- ✅ Yellow text for time (bottom line)
- ✅ Text continuously loops when it scrolls off the left edge

#### 3.3 Test Data Updates

Wait 5 minutes and check the serial console:

```
Fetching updated data...
Data updated successfully!
Line 1: METRO: ROSEMONT • 7 MIN
Line 2: STOCK: XEQT $37.85 +1.3% • CLOSED
Line 3: TIME: 15:35 • FEB 8
```

The text should update with new values.

#### 3.4 Memory Check

Check the serial console for memory info:

- **At startup**: Should be ~27-28KB free (out of ~32KB total)
- **After fetch**: Should be ~26-27KB free
- **Warning**: If free memory drops below 15KB, the device may become unstable

#### 3.5 Error Scenarios

Test fallback behavior:

**Scenario 1: Network Disconnected**
- Unplug router temporarily
- Display should show "OFFLINE" or cached data
- Plug router back in
- Should reconnect within 5 minutes

**Scenario 2: GitHub Pages Down**
- If GitHub Pages is unreachable
- Falls back to local `schedule.json` for metro data
- Shows "N/A" for stock if unavailable

## Troubleshooting

### Display Shows "STARTING" Forever

**Cause**: Can't connect to WiFi

**Solution**:
1. Check WiFi credentials in `secrets.py`
2. Verify WiFi is 2.4GHz (Matrix Portal doesn't support 5GHz)
3. Check serial console for error messages

### Display Shows "NO DATA"

**Cause**: Can't fetch from GitHub Pages and no local fallback

**Solution**:
1. Verify GitHub Pages URL in code.py (line 35)
2. Test URL in browser: `https://username.github.io/metro/data.json`
3. Check GitHub Actions completed successfully
4. Ensure `schedule.json` exists on CIRCUITPY drive

### Text Not Scrolling

**Cause**: Main loop frozen or error

**Solution**:
1. Check serial console for errors
2. Press RESET button on Matrix Portal
3. Check free memory (may be too low)

### Stock Price Shows 0.00

**Cause**: Yahoo Finance API error or invalid symbol

**Solution**:
1. Check GitHub Actions logs for errors
2. Try a different stock symbol (e.g., "AAPL")
3. Test data script locally: `python .github/scripts/update_data.py`

### Memory Allocation Errors

**Cause**: Not enough free RAM

**Solution**:
1. Check free memory in serial console
2. If < 15KB, reduce text length in update_data.py
3. Ensure no other code.py files in root directory
4. Try restarting Matrix Portal

### Scrolling Too Fast/Slow

**Cause**: SCROLL_SPEED setting

**Solution**:
Edit `code.py` line 40:
```python
SCROLL_SPEED = 0.08  # Slower (higher value = slower)
SCROLL_SPEED = 0.03  # Faster (lower value = faster)
```

## Performance Metrics

Typical performance on Matrix Portal M4:

- **Memory usage**: 4-6KB for code, 1-2KB for data
- **Free RAM**: 26-28KB average, 24KB minimum
- **Scroll FPS**: ~30 FPS (smooth animation)
- **Network request**: 2-3 seconds
- **Boot time**: 8-10 seconds
- **Data update**: Every 5 minutes (300 seconds)

## Customization

### Change Stock Symbol

Edit `config.json`:
```json
{
  "stock_symbol": "AAPL",  // Apple
  "stock_symbol": "TSLA",  // Tesla
  "stock_symbol": "GOOGL", // Google
  ...
}
```

Commit and push. Next workflow run uses new symbol.

### Change Metro Station

1. Edit `config.json`:
   ```json
   {
     "metro_station": "Berri-UQAM",
     "metro_line": "2",
     "metro_direction": "Montmorency",
     ...
   }
   ```

2. Regenerate schedule:
   ```bash
   python build_schedule.py
   ```

3. Commit and push both files

### Change Line 3 Content

Instead of time, show cryptocurrency, weather, or custom data:

1. Edit `.github/scripts/update_data.py`
2. Add new data source function
3. Update output JSON
4. Edit `code.py` to parse new data format

Example: Replace time with Bitcoin price:
```python
# In update_data.py
def get_bitcoin_price():
    response = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot")
    data = response.json()
    return {"btc_price": data['data']['amount']}

# In code.py create_display_text()
btc = data.get('btc', {})
price = btc.get('btc_price', '0')
line3_text = f"BITCOIN: ${price}"
```

### Adjust Colors

Edit `code.py` lines 46-51:
```python
COLOR_ORANGE = (255, 150, 0)   # Brighter orange
COLOR_GREEN = (0, 200, 0)      # Darker green
COLOR_RED = (200, 0, 0)        # Darker red
```

### Adjust Brightness

Edit `code.py` line 39:
```python
BRIGHTNESS = 0.5  # Brighter (max: 1.0)
BRIGHTNESS = 0.2  # Dimmer (min: 0.0)
```

## Maintenance

### Weekly

- Check GitHub Actions still running (Actions tab)
- Verify data.json updates (check timestamp)

### Monthly

- Check free memory hasn't degraded
- Update GTFS data if STM published new schedule
- Review GitHub Actions usage (Settings → Billing)

### Quarterly

- Update CircuitPython libraries
- Regenerate metro schedule (STM updates)
- Check for code improvements

## Advanced: Local Testing

Test the scrolling display before deploying:

### Simulator

The existing `simulator/index.html` works for static display. For scrolling:

1. Create a mock data.json:
   ```bash
   python .github/scripts/update_data.py
   ```

2. Modify simulator to load from data.json
3. Add CSS animation for scrolling effect

### Python Test Script

Test the data fetch locally:

```bash
# Install dependencies
pip install requests pytz

# Run script
python .github/scripts/update_data.py

# Check output
cat data.json | python -m json.tool
```

Expected output: Formatted JSON with current data

## Support & Resources

- **Hardware Guide**: [`circuitpython/README.md`](circuitpython/README.md)
- **GitHub Pages Setup**: [`GITHUB_PAGES_SETUP.md`](GITHUB_PAGES_SETUP.md)
- **Original Metro Code**: `circuitpython/code_metro.py`
- **Stock Ticker Code**: `circuitpython/code_stock.py`
- **Adafruit Learn**: https://learn.adafruit.com/adafruit-matrixportal-m4
- **CircuitPython Docs**: https://docs.circuitpython.org/

## Success Checklist

After deployment, verify:

- [ ] GitHub Actions workflow running every 5 minutes
- [ ] GitHub Pages serving data.json
- [ ] Matrix Portal connects to WiFi
- [ ] Display shows all 3 scrolling lines
- [ ] Text updates every 5 minutes
- [ ] Metro countdown accurate
- [ ] Stock price matches market
- [ ] No memory errors after 1 hour
- [ ] Smooth scrolling animation
- [ ] Proper colors for each line

**Congratulations! Your 3-line scrolling display is live!** 🎉
