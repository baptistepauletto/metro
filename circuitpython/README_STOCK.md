# XEQT Stock Ticker for Matrix Portal M4

Display real-time XEQT stock prices on your 64x32 LED matrix with a custom pixel art logo!

## Features

✨ **Custom Pixel Art Logo** - 16x16 X logo in dark gray circle (matches reference style)  
📈 **Real-Time Price** - Current XEQT price from Yahoo Finance  
📊 **Daily Change** - Percentage change with color coding (green/red)  
⏰ **Smart Updates** - Updates every 5 minutes during TSX market hours  
🔓 **No API Key** - Uses Yahoo Finance's free API (no signup required)

## Display Layout

```
┌──────────────────────────────────┐
│  ●●●●                             │
│  ●●●●   $37.83                    │
│  ●XXX●                            │
│  ●●●●   +1.2%                     │
└──────────────────────────────────┘
```

- **Left**: Custom logo (X in dark gray circle)
- **Right Top**: Current price (large, white)
- **Right Bottom**: Change % (green if up, red if down)

## Installation

### 1. Prerequisites

Ensure you have already:
- Installed CircuitPython on your Matrix Portal M4
- Installed required libraries (from your metro project setup)
- Configured WiFi credentials in `secrets.py`

### 2. Copy Files

```bash
# Copy the stock ticker code to your Matrix Portal
cp code_stock.py /Volumes/CIRCUITPY/code.py
```

Or manually:
1. Connect Matrix Portal via USB
2. Rename `code_stock.py` to `code.py`
3. Copy to the `CIRCUITPY` drive

### 3. That's it!

No API key needed! The board will:
- Connect to WiFi automatically
- Sync time via NTP
- Start displaying XEQT stock price

## Configuration

Edit these constants in `code_stock.py` to customize:

```python
STOCK_SYMBOL = "XEQT.TO"       # Change to any Yahoo Finance symbol
UPDATE_INTERVAL = 300           # Update frequency (seconds)
BRIGHTNESS = 0.3                # LED brightness (0.0 to 1.0)
```

### Supported Symbols

Any symbol on Yahoo Finance works:
- **Canadian stocks**: Add `.TO` suffix (e.g., `SHOP.TO`, `TD.TO`)
- **US stocks**: No suffix needed (e.g., `AAPL`, `MSFT`, `TSLA`)
- **ETFs**: Works great! (e.g., `XEQT.TO`, `VEQT.TO`, `SPY`)

## Market Hours

The ticker automatically detects TSX market hours:
- **Open**: Monday-Friday, 9:30 AM - 4:00 PM ET
- **Closed**: Weekends and outside trading hours

During closed hours, it displays the last known price without making API calls.

## Troubleshooting

### "NO DATA" appears on screen

**Possible causes:**
1. **No WiFi connection** - Check `secrets.py` credentials
2. **Invalid symbol** - Verify symbol exists on Yahoo Finance
3. **Network timeout** - Check internet connection

**Solution:**
- Check serial console for detailed error messages
- Test with a known symbol like `AAPL` first
- Verify WiFi is working

### Display is too bright/dim

Adjust the `BRIGHTNESS` constant:
```python
BRIGHTNESS = 0.3  # Try values between 0.1 and 1.0
```

### Updates too slow/fast

Adjust the `UPDATE_INTERVAL` constant:
```python
UPDATE_INTERVAL = 300  # In seconds (300 = 5 minutes)
```

Recommended values:
- **Fast**: 60 seconds (1 minute)
- **Normal**: 300 seconds (5 minutes)
- **Slow**: 900 seconds (15 minutes)

### Logo doesn't look right

The logo is programmatically generated. You can adjust:
- **Size**: Change the bitmap dimensions in `create_logo_bitmap()`
- **Colors**: Modify `COLOR_DARK_GRAY` and `COLOR_WHITE`
- **Position**: Adjust `x` and `y` in `logo_grid` creation

## Memory Usage

This code is very memory-efficient:
- Yahoo Finance response: ~2-3 KB
- Logo bitmap: 256 bytes
- Total RAM usage: < 5 KB (plenty of room on Matrix Portal M4)

Much smaller than the metro schedule project!

## Serial Console Output

To see debug output:
- **Windows**: Use Mu Editor or PuTTY
- **Mac/Linux**: `screen /dev/tty.usbmodem* 115200`

You'll see:
```
============================================================
XEQT Stock Ticker - Starting
============================================================
Creating logo...
Logo created!
Syncing time...
Time synced successfully

Market open: True
Fetching XEQT.TO data...
Price: $37.83
Change: +1.20%
```

## Switching Between Projects

### To Metro Schedule:
```bash
cp code.py code_stock.py  # Backup stock ticker
cp code_metro.py code.py  # Switch to metro
```

### To Stock Ticker:
```bash
cp code.py code_metro.py  # Backup metro
cp code_stock.py code.py  # Switch to stock
```

## Customization Ideas

### Multiple Stocks
Cycle through multiple stocks by creating a list:
```python
SYMBOLS = ["XEQT.TO", "VEQT.TO", "VFV.TO"]
```

### Different Colors
Change the color scheme:
```python
COLOR_GREEN = (0, 200, 0)    # Darker green
COLOR_RED = (200, 0, 0)      # Darker red
```

### Larger Logo
Make the logo bigger (20x20):
```python
logo_bitmap = displayio.Bitmap(20, 20, 3)
radius = 9
```

### Add Volume
Display trading volume:
```python
volume_str = f"{volume/1000000:.1f}M"
```

## Technical Details

### Yahoo Finance API

- **Endpoint**: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`
- **Response**: JSON with market data
- **Rate Limit**: Very generous (no practical limit)
- **Data Delay**: 15-20 minutes (free tier)

### Dependencies

All libraries from the metro project work:
- `adafruit_matrixportal/`
- `adafruit_display_text/`
- `adafruit_requests.mpy`
- `adafruit_esp32spi/`

## Support

- **CircuitPython Docs**: https://circuitpython.org
- **Adafruit Matrix Portal Guide**: https://learn.adafruit.com/adafruit-matrixportal-m4
- **Yahoo Finance**: https://finance.yahoo.com/quote/XEQT.TO

## License

Free to use and modify! Based on Adafruit example code.

---

**Enjoy your stock ticker!** 📈✨
