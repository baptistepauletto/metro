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
from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_URL = "https://baptistepauletto.github.io/metro/data.json"

# Fallback to local schedule if network fails
FALLBACK_SCHEDULE = "/schedule.json"

# Display settings
BRIGHTNESS = 0.3
UPDATE_INTERVAL = 300  # Fetch new data every 5 minutes (300 seconds)
COUNTDOWN_UPDATE = 30   # Update countdown every 30 seconds
SCROLL_SPEED = 0.05     # Seconds between scroll steps (lower = faster)
SCROLL_STEP = 1         # Pixels to move per step

# Colors (RGB)
COLOR_ORANGE = (217, 87, 0)    # Metro line
COLOR_WHITE = (255, 255, 255)  # Text
COLOR_GREEN = (0, 255, 0)      # Positive stock change
COLOR_RED = (255, 0, 0)        # Negative stock change
COLOR_YELLOW = (255, 200, 0)   # Time/clock
COLOR_DIM = (100, 100, 100)    # Dimmed text

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

def load_fallback_schedule():
    """Load local schedule as fallback if network fails."""
    try:
        with open(FALLBACK_SCHEDULE, 'r') as f:
            schedule_data = json.load(f)
        
        # Calculate next metro from local schedule
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_time = time.localtime()
        current_day = days[current_time.tm_wday]
        current_time_str = f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"
        
        schedule = schedule_data.get('schedule', {})
        today_departures = schedule.get(current_day, [])
        
        minutes_until = 0
        next_departure = "N/A"
        
        for departure in today_departures:
            if departure > current_time_str:
                curr_h, curr_m = current_time.tm_hour, current_time.tm_min
                dep_h, dep_m = map(int, departure.split(':'))
                minutes_until = (dep_h * 60 + dep_m) - (curr_h * 60 + curr_m)
                next_departure = departure
                break
        
        return {
            "metro": {
                "station": schedule_data.get('station', 'METRO'),
                "next_departure": next_departure,
                "minutes_until": minutes_until,
                "line_color": "#D95700"
            }
        }
    except Exception as e:
        print(f"Error loading fallback: {e}")
        return None

# ============================================================================
# Time Calculation Functions
# ============================================================================

def calculate_minutes_until(departure_time_str):
    """
    Calculate minutes until a given departure time (HH:MM format).
    Uses current local time from the Matrix Portal's clock.
    Returns minutes until departure, or 0 if time has passed.
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
        
        # Handle next-day departures (departure is past midnight)
        if minutes_until < 0:
            minutes_until += 24 * 60  # Add 24 hours
        
        return max(0, minutes_until)
    except Exception as e:
        print(f"Error calculating minutes: {e}")
        return 0

# ============================================================================
# Scrolling Text Classes
# ============================================================================

class ScrollingLine:
    """A single line of horizontally scrolling text."""
    
    def __init__(self, text, y_position, color, display_width=64):
        self.text = text
        self.y_position = y_position
        self.color = color
        self.display_width = display_width
        
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
            self.reset_position()
            return False
        
        return True
    
    def update_text(self, new_text, new_color=None):
        """Update the text content and optionally the color."""
        if new_text != self.text:
            self.text = new_text
            self.label.text = new_text
            self.text_width = len(new_text) * 6
            
        if new_color and new_color != self.color:
            self.color = new_color
            self.label.color = new_color

# ============================================================================
# Display Functions
# ============================================================================

def create_display_text(data, recalculate_countdown=False):
    """
    Create the text strings for each line from the data.
    If recalculate_countdown=True, recalculates metro countdown from departure time.
    Returns tuple of (line1_text, line1_color, line2_text, line2_color, line3_text, line3_color)
    """
    # Line 1: Metro
    metro = data.get('metro', {})
    station = metro.get('station', 'METRO')
    
    # Calculate minutes until departure
    if recalculate_countdown and metro.get('next_departure'):
        # Recalculate based on current time
        minutes = calculate_minutes_until(metro['next_departure'])
    else:
        # Use the value from data (initial fetch or fallback)
        minutes = metro.get('minutes_until', 0)
    
    line1_text = f"METRO: {station.upper()} • {minutes} MIN"
    line1_color = COLOR_ORANGE
    
    # Line 2: Stock
    stock = data.get('stock', {})
    symbol = stock.get('symbol', 'N/A')
    price = stock.get('price', 0.0)
    change_pct = stock.get('change_percent', 0.0)
    market_open = stock.get('market_open', False)
    status = "OPEN" if market_open else "CLOSED"
    
    if change_pct >= 0:
        line2_text = f"STOCK: {symbol} ${price:.2f} +{change_pct:.1f}% • {status}"
        line2_color = COLOR_GREEN
    else:
        line2_text = f"STOCK: {symbol} ${price:.2f} {change_pct:.1f}% • {status}"
        line2_color = COLOR_RED
    
    # Line 3: Time
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
        print("Failed to fetch from GitHub, trying fallback...")
        data = load_fallback_schedule()
        
        if not data:
            show_status("NO DATA", COLOR_RED)
            print("No data available!")
            return
    
    # Create scrolling lines
    line1_text, line1_color, line2_text, line2_color, line3_text, line3_color = create_display_text(data)
    
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
    last_scroll = time.monotonic()
    
    # Main loop
    while True:
        try:
            current = time.monotonic()
            
            # Update data periodically (every 5 minutes)
            if current - last_data_update > UPDATE_INTERVAL:
                print("\nFetching updated data...")
                show_status("UPDATING", COLOR_DIM)
                time.sleep(0.5)  # Brief visual feedback
                
                new_data = fetch_data_from_github()
                
                if new_data:
                    data = new_data
                    print("Data updated successfully!")
                    
                    # Update text content
                    line1_text, line1_color, line2_text, line2_color, line3_text, line3_color = create_display_text(data)
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
                gc.collect()
            
            # Update countdown periodically (every 30 seconds)
            elif current - last_countdown_update > COUNTDOWN_UPDATE:
                print("\nUpdating countdown...")
                
                # Recalculate metro countdown from departure time
                line1_text, line1_color, line2_text, line2_color, line3_text, line3_color = create_display_text(data, recalculate_countdown=True)
                line1.update_text(line1_text, line1_color)
                
                print(f"Countdown updated: {line1_text}")
                
                last_countdown_update = current
            
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
