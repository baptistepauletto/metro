"""
LED Matrix Display - 3-Line Scrolling Display for Matrix Portal
================================================================
Displays metro countdown, stock price, and time in horizontally scrolling format.

Hardware:
- Adafruit Matrix Portal M4
- 64x32 RGB LED Matrix Panel

Setup:
1. Install CircuitPython on Matrix Portal
2. Copy this file to CIRCUITPY drive as code.py
3. Copy secrets.py with WiFi credentials
4. Install required libraries (see below)
5. Update DATA_URL with your GitHub username

Data source: GitHub Pages (updated by GitHub Actions every 5 minutes)

Required CircuitPython Libraries:
- adafruit_matrixportal
- adafruit_display_text
- adafruit_requests
- neopixel
"""

import time
import gc
import json
import board
import displayio
import terminalio
import random
from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_URL = "https://baptistepauletto.github.io/metro/data.json"

# Display settings
BRIGHTNESS = 0.3
UPDATE_INTERVAL = 900   # Fetch new data every 15 minutes (900 seconds)
COUNTDOWN_UPDATE = 30   # Update countdown every 30 seconds
SCROLL_SPEED = 0.05     # Seconds between scroll steps (lower = faster)
SCROLL_STEP = 1         # Pixels to move per step
ASSET_ROTATION_INTERVAL = 30  # Switch assets every 30 seconds

# Easter Eggs (10% chance per line per countdown update)
EASTER_EGGS = [
    "Thibault et guilhem sont en couple",
    "cherche appart 4 1/2 2000$ de loyer svp",
]
EASTER_EGG_CHANCE = 0.10  # 10% probability

# Colors (RGB)
COLOR_ORANGE = (217, 87, 0)    # Metro line
COLOR_WHITE = (255, 255, 255)  # Text
COLOR_GREEN = (0, 255, 0)      # Positive stock change
COLOR_RED = (255, 0, 0)        # Negative stock change
COLOR_YELLOW = (255, 200, 0)   # Time/clock
COLOR_DIM = (100, 100, 100)    # Dimmed text
COLOR_PINK = (255, 105, 180)   # Easter eggs

# Asset-specific colors
ASSET_COLORS = {
    "XEQT": (100, 150, 255),   # Blue
    "BTC": (255, 140, 0),       # Orange
    "GOLD": (255, 215, 0),      # Yellow/Gold
    "SPX": (147, 112, 219)      # Purple
}

# ============================================================================
# Initialize Hardware
# ============================================================================

matrix = Matrix(bit_depth=4)
display = matrix.display
display.brightness = BRIGHTNESS

# Initialize network
network = Network(status_neopixel=board.NEOPIXEL, debug=False)

# ============================================================================
# Data Fetching Functions
# ============================================================================

def fetch_data_from_github():
    """
    Fetch the combined data JSON from GitHub Pages.
    Returns dict with metro, stock, and time data, or None on error.
    """
    response = None
    try:
        gc.collect()
        print(f"Fetching data from GitHub Pages...")
        print(f"Free memory before request: {gc.mem_free()} bytes")
        
        response = network.requests.get(DATA_URL, timeout=10)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return None
        
        gc.collect()
        data = response.json()
        
        print(f"Data fetched successfully!")
        print(f"Updated: {data.get('updated', 'unknown')}")
        
        return data
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        import traceback
        traceback.print_exception(e)
        return None
    finally:
        if response:
            response.close()
        gc.collect()
        print(f"Free memory after request: {gc.mem_free()} bytes")


# ============================================================================
# Time Calculation Functions
# ============================================================================

def calculate_minutes_until(departure_time_str):
    """
    Calculate minutes until a given departure time (HH:MM format).
    Uses current local time from the Matrix Portal's clock.
    Returns minutes until departure, or None if time has passed.
    """
    try:
        # Parse departure time
        dep_hour, dep_min = map(int, departure_time_str.split(':'))
        dep_total_minutes = dep_hour * 60 + dep_min
        
        # Get current time
        current = time.localtime()
        curr_total_minutes = current.tm_hour * 60 + current.tm_min
        
        # Calculate difference
        minutes_until = dep_total_minutes - curr_total_minutes
        
        # Return None if departure has passed (caller will try next departure)
        if minutes_until < 0:
            return None
        
        return minutes_until
    except Exception as e:
        print(f"Error calculating minutes: {e}")
        return None

def get_all_valid_departures(departures_list):
    """
    From a list of departure times, calculate minutes until each one that hasn't passed.
    Returns list of minutes (e.g., [5, 12, 18]) or empty list if all have passed.
    """
    if not departures_list:
        return []
    
    valid_minutes = []
    for departure in departures_list:
        minutes = calculate_minutes_until(departure)
        if minutes is not None:  # Not passed yet
            valid_minutes.append(minutes)
    
    return valid_minutes

# ============================================================================
# Easter Egg Functions
# ============================================================================

def should_show_easter_egg():
    """
    Roll the dice to see if an easter egg should appear.
    Returns True 10% of the time.
    """
    return random.random() < EASTER_EGG_CHANCE


def get_random_easter_egg():
    """
    Get a random easter egg phrase.
    Returns the easter egg text.
    """
    if not EASTER_EGGS:
        return None
    return random.choice(EASTER_EGGS)


# ============================================================================
# Scrolling Text Classes
# ============================================================================

class ScrollingLine:
    """A single line of horizontally scrolling text with easter egg support."""
    
    def __init__(self, text, y_position, color, display_width=64):
        self.text = text
        self.y_position = y_position
        self.color = color
        self.display_width = display_width
        self.normal_text = text
        self.normal_color = color
        self.easter_egg_mode = False
        self.easter_egg_queue = []
        
        # Create label
        self.label = label.Label(
            terminalio.FONT,
            text=text,
            color=color,
            x=display_width,  # Start offscreen to the right
            y=y_position
        )
        
        # Calculate text width (approximate: 6 pixels per character for terminalio.FONT)
        self.text_width = len(text) * 6
        
        # Reset position
        self.reset_position()
    
    def reset_position(self):
        """Reset text to starting position (right edge of display)."""
        self.label.x = self.display_width
    
    def scroll(self, step=1):
        """
        Scroll the text left by 'step' pixels.
        Returns True if text is still visible, False if it has scrolled completely off.
        """
        self.label.x -= step
        
        # Check if text has completely scrolled off the left edge
        if self.label.x + self.text_width < 0:
            # Check if we should show an easter egg next
            if self.easter_egg_queue:
                # Switch to easter egg
                easter_egg_text = self.easter_egg_queue.pop(0)
                self.label.text = easter_egg_text
                self.label.color = COLOR_PINK
                self.text = easter_egg_text
                self.text_width = len(easter_egg_text) * 6
                self.easter_egg_mode = True
            elif self.easter_egg_mode:
                # Easter egg finished, return to normal
                self.label.text = self.normal_text
                self.label.color = self.normal_color
                self.text = self.normal_text
                self.text_width = len(self.normal_text) * 6
                self.easter_egg_mode = False
            
            self.reset_position()
            return False
        
        return True
    
    def update_text(self, new_text, new_color=None):
        """Update the text content and optionally the color."""
        self.normal_text = new_text
        if new_color:
            self.normal_color = new_color
        
        # Only update display if not in easter egg mode
        if not self.easter_egg_mode:
            if new_text != self.text:
                self.text = new_text
                self.label.text = new_text
                self.text_width = len(new_text) * 6
                
            if new_color and new_color != self.color:
                self.color = new_color
                self.label.color = new_color
    
    def queue_easter_egg(self, easter_egg_text):
        """Queue an easter egg to show after current scroll completes."""
        if easter_egg_text and easter_egg_text not in self.easter_egg_queue:
            self.easter_egg_queue.append(easter_egg_text)

# ============================================================================
# Display Functions
# ============================================================================

def get_asset_display_text(asset, market_open):
    """
    Create display text for a single asset.
    Returns tuple of (text, color)
    """
    symbol = asset.get('symbol', 'N/A')
    price = asset.get('price', 0.0)
    change_pct = asset.get('change_percent', 0.0)
    
    # Get asset-specific color, fall back to white
    asset_color = ASSET_COLORS.get(symbol, COLOR_WHITE)
    
    # Format price based on asset type
    if symbol == "BTC":
        # Bitcoin: show full price
        text = f"CRYPTO: {symbol} ${price:,.0f} "
    elif symbol == "GOLD":
        # Gold: show with one decimal
        text = f"METAL: {symbol} ${price:,.1f} "
    elif symbol == "SPX":
        # S&P500: show as index
        text = f"INDEX: {symbol} {price:,.0f} "
    else:
        # XEQT and others: show with 2 decimals
        text = f"STOCK: {symbol} ${price:.2f} "
    
    # Add change percentage
    if change_pct >= 0:
        text += f"+{change_pct:.1f}%"
    else:
        text += f"{change_pct:.1f}%"
    
    # Add market status
    status = "[OPEN]" if market_open else "[CLOSED]"
    text += f" {status}"
    
    return (text, asset_color)


def create_display_text(data, recalculate_countdown=False, asset_index=0):
    """
    Create the text strings for each line from the data.
    If recalculate_countdown=True, recalculates metro countdown from departure times.
    asset_index: which asset to display on line 2 (0=XEQT, 1=BTC, 2=GOLD, 3=SPX)
    Returns tuple of (line1_text, line1_color, line2_text, line2_color, line3_text, line3_color)
    """
    # Line 1: Metro
    metro = data.get('metro', {})
    station = metro.get('station', 'METRO')
    
    # Calculate minutes until departures
    if recalculate_countdown:
        # Use the list of next departures to show multiple countdowns
        departures = metro.get('next_departures', [])
        if departures:
            valid_minutes = get_all_valid_departures(departures)
            if valid_minutes:
                # Format multiple departures: "5, 12, 18 MINS"
                if len(valid_minutes) == 1:
                    minutes_str = f"{valid_minutes[0]} MINS"
                else:
                    # Show up to 3 departures
                    minutes_display = ", ".join(str(m) for m in valid_minutes[:3])
                    minutes_str = f"{minutes_display} MINS"
            else:
                # All departures passed
                minutes_str = "UPDATING"
        else:
            # Fallback to single departure
            departure_time = metro.get('next_departure')
            if departure_time:
                minutes = calculate_minutes_until(departure_time)
                if minutes is not None:
                    minutes_str = f"{minutes} MINS"
                else:
                    minutes_str = "UPDATING"
            else:
                minutes_str = "N/A"
    else:
        # Use the value from data (initial fetch)
        minutes = metro.get('minutes_until', 0)
        minutes_str = f"{minutes} MINS"
    
    line1_text = f"METRO: {station.upper()} • {minutes_str}"
    line1_color = COLOR_ORANGE
    
    # Line 2: Asset (rotating)
    assets = data.get('assets', [])
    market_open = data.get('market_open', False)
    
    if assets and 0 <= asset_index < len(assets):
        line2_text, line2_color = get_asset_display_text(assets[asset_index], market_open)
    else:
        # Fallback to legacy stock data
        stock = data.get('stock', {})
        symbol = stock.get('symbol', 'N/A')
        price = stock.get('price', 0.0)
        change_pct = stock.get('change_percent', 0.0)
        market_open = stock.get('market_open', False)
        
        if change_pct >= 0:
            line2_text = f"STOCK: {symbol} ${price:.2f} +{change_pct:.1f}%"
            line2_color = COLOR_GREEN
        else:
            line2_text = f"STOCK: {symbol} ${price:.2f} {change_pct:.1f}%"
            line2_color = COLOR_RED
        
        status = "[OPEN]" if market_open else "[CLOSED]"
        line2_text += f" {status}"
    
    # Line 3: Time (calculate locally for real-time updates)
    if recalculate_countdown:
        # Get current local time for real-time display
        current = time.localtime()
        time_str = f"{current.tm_hour:02d}:{current.tm_min:02d}"
        # Format date
        months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        date_str = f"{months[current.tm_mon - 1]} {current.tm_mday}"
    else:
        # Use the value from GitHub (initial fetch)
        time_data = data.get('time', {})
        time_str = time_data.get('display', '00:00')
        date_str = time_data.get('date', 'N/A')
    
    line3_text = f"TIME: {time_str} • {date_str}"
    line3_color = COLOR_YELLOW
    
    return (line1_text, line1_color, line2_text, line2_color, line3_text, line3_color)

def show_status(message, color=COLOR_WHITE):
    """Show a status message on the display (centered)."""
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
    """Main program loop with scrolling display."""
    print("=" * 60)
    print("3-Line Scrolling Display - Starting")
    print("=" * 60)
    
    # Force garbage collection at startup
    gc.collect()
    print(f"Free memory at startup: {gc.mem_free()} bytes")
    
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
    
    # Initial data fetch
    show_status("LOADING", COLOR_WHITE)
    data = fetch_data_from_github()
    
    if not data:
        show_status("NO DATA", COLOR_RED)
        print("Failed to fetch data from GitHub!")
        return
    
    # Create scrolling lines (use recalculate=True to show multiple departures from start)
    current_asset_index = 0  # Start with XEQT
    line1_text, line1_color, line2_text, line2_color, line3_text, line3_color = create_display_text(
        data, recalculate_countdown=True, asset_index=current_asset_index
    )
    
    line1 = ScrollingLine(line1_text, 5, line1_color)   # Top line
    line2 = ScrollingLine(line2_text, 16, line2_color)  # Middle line
    line3 = ScrollingLine(line3_text, 27, line3_color)  # Bottom line
    
    # Create display group
    group = displayio.Group()
    group.append(line1.label)
    group.append(line2.label)
    group.append(line3.label)
    display.root_group = group
    
    print("Display initialized!")
    print(f"Line 1: {line1_text}")
    print(f"Line 2: {line2_text}")
    print(f"Line 3: {line3_text}")
    
    # Main loop variables
    last_data_update = time.monotonic()
    last_countdown_update = time.monotonic()
    last_asset_rotation = time.monotonic()
    last_scroll = time.monotonic()
    
    # Main loop
    while True:
        try:
            current = time.monotonic()
            
            # Update data periodically (every 15 minutes)
            if current - last_data_update > UPDATE_INTERVAL:
                print("\nFetching updated data...")
                show_status("UPDATING", COLOR_DIM)
                time.sleep(0.5)  # Brief visual feedback
                
                new_data = fetch_data_from_github()
                
                if new_data:
                    data = new_data
                    print("Data updated successfully!")
                    
                    # Reset asset index to start from beginning
                    current_asset_index = 0
                    
                    # Update text content (recalculate for accurate real-time display)
                    line1_text, line1_color, line2_text, line2_color, line3_text, line3_color = create_display_text(
                        data, recalculate_countdown=True, asset_index=current_asset_index
                    )
                    line1.update_text(line1_text, line1_color)
                    line2.update_text(line2_text, line2_color)
                    line3.update_text(line3_text, line3_color)
                    
                    print(f"Line 1: {line1_text}")
                    print(f"Line 2: {line2_text}")
                    print(f"Line 3: {line3_text}")
                    
                    # Restore display group
                    display.root_group = group
                else:
                    print("Failed to fetch data, using cached version")
                
                last_data_update = current
                last_countdown_update = current  # Reset countdown timer too
                last_asset_rotation = current  # Reset asset rotation timer too
                gc.collect()
            
            # Update countdown periodically (every 30 seconds)
            elif current - last_countdown_update > COUNTDOWN_UPDATE:
                print("\nUpdating countdown and time...")
                
                # Recalculate metro countdown and time from current clock
                line1_text, line1_color, line2_text, line2_color, line3_text, line3_color = create_display_text(
                    data, recalculate_countdown=True, asset_index=current_asset_index
                )
                line1.update_text(line1_text, line1_color)
                line3.update_text(line3_text, line3_color)  # Update time too
                
                print(f"Metro: {line1_text}")
                print(f"Time: {line3_text}")
                
                # Roll for easter eggs (10% chance per line)
                if should_show_easter_egg():
                    egg = get_random_easter_egg()
                    if egg:
                        line1.queue_easter_egg(egg)
                        print(f"  Easter egg queued on Line 1: {egg}")
                
                if should_show_easter_egg():
                    egg = get_random_easter_egg()
                    if egg:
                        line2.queue_easter_egg(egg)
                        print(f"  Easter egg queued on Line 2: {egg}")
                
                if should_show_easter_egg():
                    egg = get_random_easter_egg()
                    if egg:
                        line3.queue_easter_egg(egg)
                        print(f"  Easter egg queued on Line 3: {egg}")
                
                last_countdown_update = current
            
            # Rotate assets periodically (every 30 seconds)
            elif current - last_asset_rotation > ASSET_ROTATION_INTERVAL:
                print("\nRotating asset...")
                
                # Get number of assets
                assets = data.get('assets', [])
                num_assets = len(assets) if assets else 1
                
                # Cycle to next asset
                current_asset_index = (current_asset_index + 1) % num_assets
                
                # Update line 2 with new asset
                line1_text, line1_color, line2_text, line2_color, line3_text, line3_color = create_display_text(
                    data, recalculate_countdown=True, asset_index=current_asset_index
                )
                line2.update_text(line2_text, line2_color)
                
                print(f"Asset: {line2_text}")
                
                last_asset_rotation = current
            
            # Scroll animation
            if current - last_scroll > SCROLL_SPEED:
                line1.scroll(SCROLL_STEP)
                line2.scroll(SCROLL_STEP)
                line3.scroll(SCROLL_STEP)
                last_scroll = current
            
            # Short sleep to prevent tight loop
            time.sleep(0.01)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exception(e)
            show_status("ERROR", COLOR_RED)
            time.sleep(10)
            
            # Try to recover by recreating display group
            try:
                display.root_group = group
            except:
                pass

# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    main()
