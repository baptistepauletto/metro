"""
XEQT Stock Ticker - CircuitPython Code for Adafruit Matrix Portal M4
=====================================================================
Displays the XEQT stock price with a custom pixel art logo using Yahoo Finance API.

Hardware:
- Adafruit Matrix Portal M4
- 64x32 RGB LED Matrix Panel

Features:
- Custom 16x16 pixel art logo (bright pink X in white circle)
- Ticker symbol display next to logo
- Real-time stock price from Yahoo Finance (live during market hours)
- Shows last closing price when market is closed
- Daily change percentage with color coding (green/red)
- Moon icon + "CLOSED" or Sun icon + "OPEN" status indicators
- Clean 3-line display layout optimized for 64x32 LED matrix
- Updates every 5 minutes (even when closed)
- No API key required!

Setup:
1. Ensure WiFi credentials are in secrets.py
2. Copy this file to CIRCUITPY drive as code.py
3. Install required libraries (see below)

Required CircuitPython Libraries:
- adafruit_matrixportal (or individual components)
- adafruit_display_text
- adafruit_requests
- adafruit_esp32spi

Memory Optimizations:
- Uses gc.collect() before/after API requests
- Minimal Yahoo Finance response (1d range, 1d interval)
- Aggressive cleanup of parsed JSON data
- Displays free memory in serial console for monitoring
"""

import time
import gc  # Garbage collector for memory management
import board
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network

# ============================================================================
# CONFIGURATION
# ============================================================================

STOCK_SYMBOL = "XEQT.TO"  # iShares Core Equity ETF Portfolio (TSX)
UPDATE_INTERVAL = 300  # Update every 5 minutes (300 seconds) - fetches even when closed
BRIGHTNESS = 0.3  # Display brightness (0.0 to 1.0)

# Yahoo Finance API endpoint (simplified for memory efficiency)
# Using 1d range and 1d interval for minimal response size
YAHOO_API_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"

# Colors (RGB tuples)
COLOR_PINK = (255, 105, 180)      # Logo X letter (hot pink)
COLOR_WHITE = (255, 255, 255)     # Logo circle background and price text
COLOR_GREEN = (0, 255, 0)         # Positive change
COLOR_RED = (255, 0, 0)           # Negative change
COLOR_YELLOW = (255, 200, 0)      # Sun icon
COLOR_DIM_GRAY = (100, 100, 100)  # Moon icon and closed text
COLOR_BLACK = (0, 0, 0)           # Matrix background

# Market hours (Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# ============================================================================
# Initialize Hardware
# ============================================================================

matrix = Matrix(bit_depth=4)
display = matrix.display
display.brightness = BRIGHTNESS

# Initialize network for API calls and time sync
network = Network(status_neopixel=board.NEOPIXEL, debug=False)

# ============================================================================
# Logo Creation - 16x16 Pixel Art
# ============================================================================

def create_logo_bitmap():
    """
    Creates a 16x16 pixel art logo with a bright pink X in a white circle.
    Optimized for LED matrix visibility.
    """
    # Create bitmap with 3 colors: black (background), white (circle), pink (X)
    logo_bitmap = displayio.Bitmap(16, 16, 3)
    palette = displayio.Palette(3)
    palette[0] = COLOR_BLACK[0] << 16 | COLOR_BLACK[1] << 8 | COLOR_BLACK[2]
    palette[1] = COLOR_WHITE[0] << 16 | COLOR_WHITE[1] << 8 | COLOR_WHITE[2] 
    palette[2] = COLOR_PINK[0] << 16 | COLOR_PINK[1] << 8 | COLOR_PINK[2]  
    
    # First, mark which pixels will be the X (to skip them in circle)
    x_pixels = set()
    
    # Top-left to bottom-right diagonal
    for i in range(5, 11):
        x_pixels.add((i, i))
        x_pixels.add((i + 1, i))
    
    # Top-right to bottom-left diagonal
    for i in range(4, 12):
        x_pixels.add((15 - i, i))
        x_pixels.add((14 - i, i))
    
    # Draw filled circle (8 pixel radius, centered at 8,8)
    # Skip pixels that will be the X
    center_x, center_y = 8, 8
    radius = 7
    
    for y in range(1, 15):
        for x in range(1, 15):
            if (x, y) not in x_pixels:  # Skip X pixels
                dx = x - center_x
                dy = y - center_y
                distance = (dx * dx + dy * dy) ** 0.5
                if distance <= radius:
                    logo_bitmap[x, y] = 1  # White circle (but not where X will be)
    
    return logo_bitmap, palette


# ============================================================================
# Stock Data Functions
# ============================================================================

def fetch_stock_data(symbol):
    """
    Fetches stock data from Yahoo Finance API.
    Returns dict with price, change, and change_percent, or None on error.
    Memory-optimized: Forces garbage collection before/after request.
    """
    response = None
    try:
        # Force garbage collection before making request
        gc.collect()
        print(f"Free memory before request: {gc.mem_free()} bytes")
        
        url = YAHOO_API_URL.format(symbol=symbol)
        print(f"Fetching data from: {url}")
        
        response = network.requests.get(url)
        
        # Force garbage collection before parsing JSON
        gc.collect()
        
        data = response.json()
        
        # Parse Yahoo Finance response (memory-optimized)
        chart = data.get("chart", {})
        result_list = chart.get("result", [])
        
        if not result_list:
            print("Error: No result in Yahoo Finance response")
            return None
        
        meta = result_list[0].get("meta", {})
        
        # Extract price data with fallbacks for when market is closed
        # Try multiple fields that Yahoo Finance might use
        current_price = (
            meta.get("regularMarketPrice") or      # Live during market hours
            meta.get("previousClose") or           # When market just closed
            meta.get("chartPreviousClose")         # Alternative field
        )
        
        previous_close = (
            meta.get("previousClose") or
            meta.get("chartPreviousClose")
        )
        
        # Fallback: Try to get price from historical data arrays
        if current_price is None:
            try:
                # Get closing prices from indicators
                indicators = result_list[0].get("indicators", {})
                quote = indicators.get("quote", [{}])[0]
                close_prices = quote.get("close", [])
                
                if close_prices:
                    # Get the most recent non-null closing price
                    for price in reversed(close_prices):
                        if price is not None:
                            current_price = price
                            print(f"Using historical close price: ${price:.2f}")
                            break
            except Exception as e:
                print(f"Could not extract from historical data: {e}")
        
        # Debug: Print available fields if price is still missing
        if current_price is None:
            print(f"Available meta fields: {list(meta.keys())}")
            print("Error: Missing price data in all fields")
            return None
        
        if previous_close is None:
            # If we can't get previous close, use current as both (0% change)
            print("Warning: Using current price as previous close (no change data)")
            previous_close = current_price
        
        # Calculate change and percentage
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100
        
        result = {
            "price": current_price,
            "change": change,
            "change_percent": change_percent,
            "symbol": meta.get("symbol", symbol)
        }
        
        # Clean up large objects immediately
        del data
        del chart
        del result_list
        del meta
        
        return result
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        import traceback
        traceback.print_exception(e)
        return None
    finally:
        # Clean up response to free memory
        if response:
            response.close()
        # Force garbage collection after request
        gc.collect()
        print(f"Free memory after request: {gc.mem_free()} bytes")


def is_market_open():
    """
    Checks if the market is currently open (TSX hours: 9:30 AM - 4:00 PM ET, Mon-Fri).
    """
    current_time = time.localtime()
    weekday = current_time.tm_wday  # 0 = Monday, 6 = Sunday
    hour = current_time.tm_hour
    minute = current_time.tm_min
    
    # Check if it's a weekday (Monday to Friday)
    if weekday >= 5:  # Saturday or Sunday
        return False
    
    # Check if within market hours
    current_minutes = hour * 60 + minute
    open_minutes = MARKET_OPEN_HOUR * 60 + MARKET_OPEN_MINUTE
    close_minutes = MARKET_CLOSE_HOUR * 60 + MARKET_CLOSE_MINUTE
    
    return open_minutes <= current_minutes < close_minutes


# ============================================================================
# Display Functions
# ============================================================================

def clear_display():
    """Clear the display."""
    group = displayio.Group()
    display.root_group = group


def update_display(stock_data, logo_bitmap, logo_palette, market_closed=False):
    """
    Update the display with new layout:
    Line 1: [LOGO] XEQT
    Line 2: $37.83 +1.2%
    Line 3: CLOSED (or OPEN)
    """
    group = displayio.Group()
    
    # Line 1: Logo on left (x=0, y=4), ticker on right (x=22, y=12)
    logo_grid = displayio.TileGrid(
        logo_bitmap,
        pixel_shader=logo_palette,
        x=10,
        y=-1
    )
    group.append(logo_grid)
    
    if stock_data is None:
        # Show error message
        error_label = label.Label(
            terminalio.FONT,
            text="NO DATA",
            color=COLOR_RED,
            x=22,
            y=12
        )
        group.append(error_label)
        display.root_group = group
        return
    
    # Ticker symbol next to logo
    ticker_label = label.Label(
        terminalio.FONT,
        text=STOCK_SYMBOL.split('.')[0],  # Remove .TO suffix
        color=COLOR_WHITE,
        scale=1,
        x=28,
        y=8
    )
    group.append(ticker_label)
    
    # Line 2: Price (left side) and change % (right side) on same line
    price_str = f"${stock_data['price']:.2f}"
    
    # Format change percent
    change_pct = stock_data['change_percent']
    if change_pct >= 0:
        change_str = f"+{change_pct:.1f}%"
        change_color = COLOR_GREEN
    else:
        change_str = f"{change_pct:.1f}%"
        change_color = COLOR_RED
    
    # Price label (left side of line 2) - moved up
    price_label = label.Label(
        terminalio.FONT,
        text=price_str,
        color=COLOR_WHITE,
        scale=1,
        x=0,
        y=19  # Moved up from 22 to 19
    )
    group.append(price_label)
    
    # Change percentage label (right side of line 2) - moved up
    change_label = label.Label(
        terminalio.FONT,
        text=change_str,
        color=change_color,
        scale=1,
        x=36,
        y=19  # Moved up from 22 to 19
    )
    group.append(change_label)
    
    # Line 3: Market status with icon - moved up to prevent truncation
    if market_closed:
        status_label = label.Label(
            terminalio.FONT,
            text="CLOSED",
            color=COLOR_DIM_GRAY,
            scale=1,
            x=14,
            y=27  # Moved up from 29 to 27
        )
        group.append(status_label)
    else:
        status_label = label.Label(
            terminalio.FONT,
            text="OPEN",
            color=COLOR_GREEN,
            scale=1,
            x=10,
            y=27  # Moved up from 29 to 27
        )
        group.append(status_label)
    
    display.root_group = group


def show_status(message, color=COLOR_WHITE):
    """Show a status message on the display."""
    group = displayio.Group()
    
    status_label = label.Label(
        terminalio.FONT,
        text=message,
        color=color,
        x=2,
        y=16
    )
    group.append(status_label)
    
    display.root_group = group


# ============================================================================
# Main Loop
# ============================================================================

def main():
    """Main program loop."""
    print("=" * 60)
    print("XEQT Stock Ticker - Starting")
    print("=" * 60)
    
    # Force garbage collection at startup
    gc.collect()
    print(f"Free memory at startup: {gc.mem_free()} bytes")
    
    # Create logo and icons
    print("Creating logo and icons...")
    logo_bitmap, logo_palette = create_logo_bitmap()
    print("Graphics created!")
    gc.collect()  # Clean up after creation
    
    # Show startup message
    show_status("STARTING", COLOR_WHITE)
    time.sleep(1)
    
    # Sync time with NTP
    print("Syncing time...")
    show_status("SYNC TIME", COLOR_WHITE)
    try:
        network.get_local_time()
        print("Time synced successfully")
    except Exception as e:
        print(f"Warning: Could not sync time: {e}")
    
    # Cache for last known stock data
    last_stock_data = None
    last_update = 0
    
    # Main loop
    while True:
        try:
            current = time.monotonic()
            
            # Check if it's time to update
            if current - last_update > UPDATE_INTERVAL:
                market_open = is_market_open()
                print(f"\nMarket open: {market_open}")
                
                # Always fetch data (Yahoo Finance returns last close when market is closed)
                print(f"Fetching {STOCK_SYMBOL} data...")
                show_status("UPDATING", COLOR_WHITE)
                
                stock_data = fetch_stock_data(STOCK_SYMBOL)
                
                if stock_data:
                    last_stock_data = stock_data
                    if market_open:
                        print(f"Price: ${stock_data['price']:.2f} (LIVE)")
                    else:
                        print(f"Price: ${stock_data['price']:.2f} (LAST CLOSE)")
                    print(f"Change: {stock_data['change_percent']:+.2f}%")
                else:
                    print("Failed to fetch data, using cached data")
                    stock_data = last_stock_data
                
                update_display(stock_data, logo_bitmap, logo_palette, market_closed=not market_open)
                
                # Force garbage collection after display update
                gc.collect()
                
                last_update = current
            
            # Short sleep to prevent tight loop
            time.sleep(1)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            show_status("ERROR", COLOR_RED)
            time.sleep(10)


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    main()
