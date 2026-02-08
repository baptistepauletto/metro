# Testing Checklist for 3-Line Scrolling Display

Use this checklist to verify your deployment is working correctly.

## Pre-Deployment Tests

### ☐ GitHub Actions Setup

- [ ] Workflow file exists: `.github/workflows/update-display-data.yml`
- [ ] Python script exists: `.github/scripts/update_data.py`
- [ ] Config file exists and is valid: `config.json`
- [ ] Schedule file exists: `schedule.json`
- [ ] Requirements updated: `requirements.txt`

### ☐ Local Script Testing

```bash
# Install dependencies
pip install requests pytz

# Run the data update script
python .github/scripts/update_data.py

# Verify output file created
ls -la data.json

# Check JSON is valid
cat data.json | python -m json.tool
```

**Expected output**:
```json
{
  "updated": "2026-02-08T...",
  "metro": {
    "station": "Rosemont",
    "next_departure": "14:43",
    "minutes_until": 8,
    "line_color": "#D95700"
  },
  "stock": {
    "symbol": "XEQT",
    "price": 37.83,
    "change_percent": 1.2,
    "market_open": false
  },
  "time": {
    "display": "09:35",
    "timezone": "America/Montreal",
    "date": "FEB 8"
  }
}
```

### ☐ Code Review

- [ ] GitHub username updated in `code.py` (line 35)
- [ ] WiFi credentials in `secrets.py`
- [ ] Required libraries downloaded
- [ ] Backup created: `code_metro.py` and `code_stock.py`

## GitHub Tests

### ☐ Repository Setup

- [ ] Code committed and pushed to `master` branch
- [ ] GitHub Actions enabled (Settings → Actions)
- [ ] Workflow appears in Actions tab
- [ ] First workflow run completed successfully

### ☐ GitHub Pages Setup

- [ ] GitHub Pages enabled (Settings → Pages)
- [ ] Source set to `gh-pages` branch, `/ (root)` folder
- [ ] `gh-pages` branch exists (check branches dropdown)
- [ ] `data.json` file exists on `gh-pages` branch

### ☐ Data Endpoint Test

Visit: `https://YOUR_USERNAME.github.io/metro/data.json`

- [ ] URL returns 200 OK (not 404)
- [ ] Content-Type is `application/json`
- [ ] JSON is valid and complete
- [ ] Timestamp is recent (within last 5 minutes)

**Troubleshooting**: If 404, wait 2-3 minutes for GitHub Pages to deploy after first commit.

## Matrix Portal Tests

### ☐ Hardware Setup

- [ ] CircuitPython installed (version 8.0+)
- [ ] Libraries copied to `CIRCUITPY/lib/`:
  - [ ] `adafruit_matrixportal/`
  - [ ] `adafruit_display_text/`
  - [ ] `adafruit_requests.mpy`
  - [ ] `adafruit_esp32spi/`
  - [ ] `neopixel.mpy`

### ☐ File Deployment

Files on `CIRCUITPY` drive:

- [ ] `code.py` (new scrolling version)
- [ ] `secrets.py` (with WiFi credentials)
- [ ] `schedule.json` (fallback data)

### ☐ Serial Console Checks

Connect to serial console and verify:

- [ ] Device boots without errors
- [ ] Free memory at startup > 25KB
- [ ] WiFi connects successfully
- [ ] Time synced via NTP
- [ ] Data fetched from GitHub Pages
- [ ] Three lines of text displayed
- [ ] No Python exceptions

**Expected output**:
```
============================================================
3-Line Scrolling Display - Starting
============================================================
Free memory at startup: 28340 bytes
Syncing time...
Time synced successfully
Fetching data from GitHub Pages...
Data fetched successfully!
Updated: 2026-02-08T20:30:00Z
Display initialized!
Line 1: METRO: ROSEMONT • 8 MIN
Line 2: STOCK: XEQT $37.83 +1.2% • CLOSED
Line 3: TIME: 15:30 • FEB 8
```

### ☐ Visual Display Checks

On the LED matrix:

- [ ] Three lines of text visible
- [ ] Text scrolling horizontally from right to left
- [ ] Top line (metro) is orange/yellow color
- [ ] Middle line (stock) is green (up) or red (down)
- [ ] Bottom line (time) is yellow
- [ ] Text loops continuously when it scrolls off
- [ ] No flickering or glitches
- [ ] Brightness is comfortable

### ☐ Data Accuracy

Verify displayed data:

- [ ] Metro countdown matches expected schedule
- [ ] Stock price matches Yahoo Finance (check: finance.yahoo.com)
- [ ] Time matches current time (±1 minute)
- [ ] Date is correct

### ☐ Update Behavior

Wait 5 minutes and verify:

- [ ] Serial console shows "Fetching updated data..."
- [ ] New data fetched successfully
- [ ] Text content updates on display
- [ ] Metro countdown decrements
- [ ] No memory leaks (free memory stable)

## Stress Tests

### ☐ Network Resilience

**Test 1: WiFi Disconnect**

1. [ ] Unplug router or disable WiFi
2. [ ] Wait 5+ minutes
3. [ ] Display shows cached data or "OFFLINE"
4. [ ] No crashes or freezes
5. [ ] Reconnect WiFi
6. [ ] Display recovers and fetches new data

**Test 2: GitHub Pages Down**

1. [ ] Temporarily break GitHub Pages URL in code.py
2. [ ] Restart Matrix Portal
3. [ ] Display falls back to local schedule.json
4. [ ] Stock shows "N/A" or cached value
5. [ ] No crashes

### ☐ Memory Stability

Run for 1 hour, check every 10 minutes:

- [ ] T+10min: Free memory _______ KB
- [ ] T+20min: Free memory _______ KB
- [ ] T+30min: Free memory _______ KB
- [ ] T+40min: Free memory _______ KB
- [ ] T+50min: Free memory _______ KB
- [ ] T+60min: Free memory _______ KB

**Pass criteria**: Free memory should remain > 24KB and not continuously decrease.

### ☐ Edge Cases

**Midnight Rollover**

- [ ] Display works correctly around midnight
- [ ] Date updates to next day
- [ ] Metro schedule switches to next day

**Market Open/Close**

- [ ] Stock display changes from "OPEN" to "CLOSED"
- [ ] Color changes appropriately
- [ ] Price still updates with last closing price

**Long Text**

- [ ] If station name > 10 chars, still displays correctly
- [ ] Long stock symbols don't cause layout issues
- [ ] Text doesn't overflow display boundaries

## Performance Metrics

Record typical values:

- **Startup time**: _______ seconds
- **Boot to WiFi connect**: _______ seconds
- **Data fetch time**: _______ seconds
- **Free memory (idle)**: _______ KB
- **Free memory (after fetch)**: _______ KB
- **Scroll FPS** (estimate): _______ FPS

## Issues Log

Document any issues encountered:

| Issue | Severity | Resolution | Date |
|-------|----------|------------|------|
|       |          |            |      |
|       |          |            |      |
|       |          |            |      |

## Sign-Off

- **Tested by**: _________________
- **Date**: _________________
- **Overall Status**: ☐ Pass  ☐ Fail  ☐ Pass with issues

**Notes**:
_______________________________________________
_______________________________________________
_______________________________________________

## Next Steps

If all tests pass:
- [ ] Document any configuration changes
- [ ] Take a photo/video of working display
- [ ] Set calendar reminder to check monthly
- [ ] Consider additional customizations

If issues found:
- [ ] Review troubleshooting section in DEPLOYMENT_GUIDE.md
- [ ] Check serial console for error details
- [ ] Verify all configuration files
- [ ] Test with minimal setup (stock ticker only)
- [ ] Ask for help on Adafruit forums if needed

---

**Testing complete!** Your 3-line scrolling display is ready for daily use. 🎉
