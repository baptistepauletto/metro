# Quick Deployment Guide - XEQT Stock Ticker

## Ready to Deploy!

Your stock ticker code is complete and ready to test on your Matrix Portal M4.

## Pre-Flight Checklist

✅ **Code Created**: `code_stock.py` with Yahoo Finance integration  
✅ **Logo Built**: 16x16 pixel art (X in dark gray circle)  
✅ **No API Key Needed**: Yahoo Finance is free and open  
✅ **Documentation**: `README_STOCK.md` with full instructions  

## Deployment Steps

### 1. Connect Your Matrix Portal

```bash
# Plug in your Matrix Portal M4 via USB
# It should mount as CIRCUITPY drive
```

### 2. Test the Code First (Optional but Recommended)

Before deploying, you can test with a different symbol first:

**Option A: Test with a US stock (simpler)**
Edit `code_stock.py` line 33:
```python
STOCK_SYMBOL = "AAPL"  # Apple stock (reliable for testing)
```

**Option B: Go straight to XEQT**
Keep it as:
```python
STOCK_SYMBOL = "XEQT.TO"  # Your original choice
```

### 3. Deploy to Matrix Portal

**Copy the file:**
```bash
# On Windows
copy code_stock.py X:\code.py

# On Mac/Linux
cp code_stock.py /Volumes/CIRCUITPY/code.py
```

**Or manually:**
1. Open the `CIRCUITPY` drive
2. Rename `code.py` to `code_metro.py` (backup your metro code)
3. Copy `code_stock.py` from `circuitpython/` folder
4. Rename it to `code.py` on the CIRCUITPY drive
5. The board will auto-restart!

### 4. Watch It Boot

**Serial console (optional but helpful):**
- Windows: Open Mu Editor
- Mac/Linux: `screen /dev/tty.usbmodem* 115200`

**You should see:**
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

### 5. Check the Display

**What you should see on the LED matrix:**

```
┌────────────────────────┐
│  ●●●●                  │
│  ●●●●   $37.83         │
│  ●XXX●                 │
│  ●●●●   +1.2%          │
└────────────────────────┘
```

## Troubleshooting

### Display shows "STARTING" forever

**Problem**: Can't connect to WiFi

**Fix:**
1. Check `secrets.py` has correct WiFi credentials
2. Make sure you're on 2.4GHz network (Matrix Portal doesn't support 5GHz)
3. Check serial console for error messages

### Display shows "NO DATA"

**Problem**: Can't fetch stock data

**Fixes to try:**
1. **Test with a different symbol**: Try `AAPL` to verify Yahoo Finance works
2. **Check internet connection**: Matrix Portal needs internet access
3. **Verify symbol format**: 
   - Canadian stocks: `XEQT.TO`
   - US stocks: `AAPL` (no suffix)
4. **Check serial console**: Will show detailed error messages

### Display shows "ERROR"

**Problem**: Unexpected error in main loop

**Fix:**
1. Check serial console for stack trace
2. Verify all libraries are installed
3. Try power cycling the board

### Logo looks weird

**Possible causes:**
- Pixel alignment might need adjustment
- Circle drawing might look different on actual hardware

**Quick fix** - Adjust logo position in code:
```python
# In update_display function, line ~215
logo_grid = displayio.TileGrid(
    logo_bitmap,
    pixel_shader=logo_palette,
    x=2,    # Try 0, 2, 4 to adjust horizontal
    y=8     # Try 6, 8, 10 to adjust vertical
)
```

### Text is too big/small

**Adjust text scaling:**
```python
# In update_display function
price_label = label.Label(
    terminalio.FONT,
    text=price_str,
    color=COLOR_WHITE,
    scale=2,  # Try 1, 2, or 3
    x=20,     # Adjust position
    y=10
)
```

## Testing Checklist

After deploying, verify:

- [ ] Matrix Portal boots and connects to WiFi
- [ ] Time syncs successfully  
- [ ] Logo displays in top-left corner
- [ ] Price shows on right side (white text)
- [ ] Change percentage shows below price (green or red)
- [ ] Updates every 5 minutes
- [ ] No memory errors in serial console

## Next Steps After Testing

Once you confirm it works:

1. **Leave it running** - it will automatically update during market hours
2. **Check after market close** - should display last known price
3. **Try different stocks** - edit `STOCK_SYMBOL` to track other tickers
4. **Customize colors** - adjust RGB values to your preference

## Quick Reference

**Toggle between projects:**
```bash
# Switch to metro
cp code_metro.py code.py

# Switch to stock
cp code_stock.py code.py
```

**View logs:**
```bash
# Mac/Linux
screen /dev/tty.usbmodem* 115200

# Windows
# Use Mu Editor's serial console
```

**Update frequency:**
```python
UPDATE_INTERVAL = 300  # 5 minutes (default)
UPDATE_INTERVAL = 60   # 1 minute (faster)
UPDATE_INTERVAL = 900  # 15 minutes (slower)
```

## Success!

If you see the logo and price on your display, congratulations! 🎉

Your XEQT stock ticker is now live and will update automatically during market hours.

---

**Questions or issues?** Check the serial console for detailed error messages.
