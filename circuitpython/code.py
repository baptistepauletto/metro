"""
LED Matrix Display - CircuitPython Code for Adafruit Matrix Portal
===================================================================
Copy this file and schedule.json to your Matrix Portal's CIRCUITPY drive.

Hardware:
- Adafruit Matrix Portal M4
- 64x32 RGB LED Matrix Panel

Setup:
1. Install CircuitPython on Matrix Portal
2. Copy code.py (this file) to CIRCUITPY drive
3. Copy schedule.json to CIRCUITPY drive
4. Copy secrets.py with WiFi credentials
5. Install required libraries (see below)

Required CircuitPython Libraries:
- adafruit_matrixportal
- adafruit_display_text
- neopixel
"""

import time
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

SCHEDULE_FILE = "/schedule.json"
UPDATE_INTERVAL = 30  # Update display every 30 seconds
BRIGHTNESS = 0.3      # Display brightness (0.0 to 1.0)

# Line colors (RGB for LED matrix)
LINE_COLORS = {
    "1": (0, 179, 0),      # Green
    "2": (217, 87, 0),     # Orange
    "4": (255, 217, 0),    # Yellow
    "5": (0, 149, 230),    # Blue
}

# ============================================================================
# Initialize Matrix
# ============================================================================

matrix = Matrix(bit_depth=4)
display = matrix.display
display.brightness = BRIGHTNESS

# Initialize network for time sync
network = Network(status_neopixel=board.NEOPIXEL, debug=False)

# ============================================================================
# Load Schedule
# ============================================================================

def load_schedule():
    """Load the schedule from JSON file."""
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            data = json.load(f)
        print(f"✓ Schedule loaded for {data['station']}")
        return data
    except Exception as e:
        print(f"❌ Error loading schedule: {e}")
        return None


def get_current_day():
    """Get current day of week (monday, tuesday, etc.)."""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    # Get current time from network
    current_time = time.localtime()
    weekday = current_time.tm_wday  # 0 = Monday
    return days[weekday]


def get_current_time_str():
    """Get current time as HH:MM string."""
    current_time = time.localtime()
    return f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}"


def find_next_departure(schedule_data):
    """Find the next departure from the schedule."""
    current_day = get_current_day()
    current_time = get_current_time_str()
    
    schedule = schedule_data.get('schedule', {})
    today_departures = schedule.get(current_day, [])
    
    if not today_departures:
        return None, 0
    
    # Find next departure
    for departure in today_departures:
        if departure > current_time:
            # Calculate minutes until departure
            curr_h, curr_m = map(int, current_time.split(':'))
            dep_h, dep_m = map(int, departure.split(':'))
            
            curr_minutes = curr_h * 60 + curr_m
            dep_minutes = dep_h * 60 + dep_m
            
            minutes_until = dep_minutes - curr_minutes
            return departure, minutes_until
    
    # No more departures today, show first departure tomorrow
    # Check tomorrow's schedule
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    tomorrow = days[(days.index(current_day) + 1) % 7]
    tomorrow_departures = schedule.get(tomorrow, [])
    
    if tomorrow_departures:
        # Calculate minutes until first departure tomorrow
        curr_h, curr_m = map(int, current_time.split(':'))
        dep_h, dep_m = map(int, tomorrow_departures[0].split(':'))
        
        curr_minutes = curr_h * 60 + curr_m
        dep_minutes = (24 * 60) - curr_minutes + (dep_h * 60 + dep_m)
        
        return tomorrow_departures[0], dep_minutes
    
    return None, 0


# ============================================================================
# Display Functions
# ============================================================================

def clear_display():
    """Clear the display."""
    group = displayio.Group()
    display.show(group)


def draw_countdown(minutes, station_name, line_color):
    """Draw the countdown display."""
    group = displayio.Group()
    
    # Get color for this line
    color = LINE_COLORS.get(line_color, (255, 107, 0))  # Default to orange
    
    # Station name at top (smaller font)
    station_label = label.Label(
        terminalio.FONT,
        text=station_name.upper(),
        color=color,
        x=2,
        y=4
    )
    group.append(station_label)
    
    # Line separator
    line = displayio.Bitmap(64, 1, 1)
    line_palette = displayio.Palette(1)
    line_palette[0] = color
    line_sprite = displayio.TileGrid(line, pixel_shader=line_palette, x=0, y=10)
    group.append(line_sprite)
    
    # Large countdown number
    if minutes < 99:
        minutes_str = str(minutes)
    else:
        minutes_str = "--"
    
    minutes_label = label.Label(
        terminalio.FONT,
        text=minutes_str,
        color=color,
        scale=3,
        x=16 if len(minutes_str) == 2 else 24,
        y=18
    )
    group.append(minutes_label)
    
    # "MIN" label
    min_label = label.Label(
        terminalio.FONT,
        text="MIN",
        color=(color[0]//3, color[1]//3, color[2]//3),  # Dimmer
        x=20,
        y=28
    )
    group.append(min_label)
    
    display.show(group)


def show_error(message):
    """Show error message on display."""
    group = displayio.Group()
    
    error_label = label.Label(
        terminalio.FONT,
        text=message,
        color=(255, 0, 0),
        x=2,
        y=16
    )
    group.append(error_label)
    
    display.show(group)


# ============================================================================
# Main Loop
# ============================================================================

def main():
    """Main program loop."""
    print("=" * 60)
    print("LED Matrix Display - Starting")
    print("=" * 60)
    
    # Load schedule
    schedule_data = load_schedule()
    if not schedule_data:
        show_error("NO DATA")
        return
    
    station_name = schedule_data.get('station', 'METRO')
    line_number = schedule_data.get('line', '2')
    
    print(f"Station: {station_name}")
    print(f"Line: {line_number}")
    
    # Sync time with NTP
    print("Syncing time...")
    try:
        network.get_local_time()
        print("✓ Time synced")
    except Exception as e:
        print(f"⚠ Warning: Could not sync time: {e}")
    
    # Main loop
    last_update = 0
    
    while True:
        try:
            current = time.monotonic()
            
            # Update display
            if current - last_update > UPDATE_INTERVAL:
                departure_time, minutes = find_next_departure(schedule_data)
                
                if departure_time:
                    print(f"Next: {departure_time} ({minutes} min)")
                    draw_countdown(minutes, station_name, line_number)
                else:
                    print("No departures found")
                    show_error("NO SERVICE")
                
                last_update = current
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            show_error("ERROR")
            time.sleep(5)


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    main()
