"""
Build Schedule - GTFS to JSON Converter
========================================
Lightweight script to extract metro departure times for a specific station.
Run this 2-4 times per year when STM updates their GTFS data.

Usage:
    python build_schedule.py
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ============================================================================
# CONFIGURATION - Edit these values for your station
# ============================================================================

STATION_NAME = "Rosemont"           # Your metro station
LINE_NUMBER = "2"                    # Line number: 1=Green, 2=Orange, 4=Yellow, 5=Blue
DIRECTION = "Côte-Vertu"            # Direction of travel (terminus name)

# ============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = Path(__file__).parent / "schedule.json"


def load_csv(filename):
    """Load a CSV file into a list of dictionaries."""
    filepath = DATA_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def find_station_stops(station_name):
    """Find all stop IDs for a station (metro stations have multiple stop points)."""
    stops = load_csv("stops.txt")
    station_stops = []
    
    for stop in stops:
        if station_name.lower() in stop['stop_name'].lower():
            # Only get actual stop points (location_type = 0)
            if stop.get('location_type') == '0':
                station_stops.append(stop['stop_id'])
    
    return station_stops


def get_trips_for_line_and_direction(line_number, direction):
    """Get all trip IDs for a specific line and direction."""
    trips = load_csv("trips.txt")
    trip_ids = []
    
    for trip in trips:
        if trip['route_id'] == line_number:
            # Check if this trip goes in our direction
            headsign = trip.get('trip_headsign', '')
            if direction.lower() in headsign.lower():
                trip_ids.append(trip['trip_id'])
    
    return trip_ids


def get_service_patterns():
    """Get service patterns from calendar.txt (which days each service runs)."""
    calendar = load_csv("calendar.txt")
    service_patterns = {}
    
    for service in calendar:
        service_id = service['service_id']
        # Map service_id to which days it runs
        days = []
        if service.get('monday') == '1': days.append('monday')
        if service.get('tuesday') == '1': days.append('tuesday')
        if service.get('wednesday') == '1': days.append('wednesday')
        if service.get('thursday') == '1': days.append('thursday')
        if service.get('friday') == '1': days.append('friday')
        if service.get('saturday') == '1': days.append('saturday')
        if service.get('sunday') == '1': days.append('sunday')
        
        service_patterns[service_id] = days
    
    return service_patterns


def extract_departures(station_stops, trip_ids):
    """Extract all departure times for the station from the relevant trips."""
    stop_times = load_csv("stop_times.txt")
    trips = load_csv("trips.txt")
    
    # Create a mapping of trip_id to service_id
    trip_to_service = {trip['trip_id']: trip['service_id'] for trip in trips}
    
    # Get service patterns
    service_patterns = get_service_patterns()
    
    # Group departures by day of week
    departures_by_day = defaultdict(set)  # Use set to avoid duplicates
    
    for stop_time in stop_times:
        trip_id = stop_time['trip_id']
        stop_id = stop_time['stop_id']
        
        # Check if this is our station and one of our trips
        if stop_id in station_stops and trip_id in trip_ids:
            departure_time = stop_time['departure_time']
            
            # Get the service_id for this trip
            service_id = trip_to_service.get(trip_id)
            if not service_id:
                continue
            
            # Get which days this service runs
            days = service_patterns.get(service_id, [])
            
            # Add this departure time to all applicable days
            for day in days:
                # Handle times > 24:00 (next day service)
                hours, minutes, seconds = departure_time.split(':')
                hours = int(hours)
                if hours >= 24:
                    hours -= 24
                    departure_time = f"{hours:02d}:{minutes}:{seconds}"
                
                # Store as HH:MM (drop seconds)
                time_str = departure_time[:5]
                departures_by_day[day].add(time_str)
    
    # Convert sets to sorted lists
    schedule = {}
    for day, times in departures_by_day.items():
        schedule[day] = sorted(list(times))
    
    return schedule


def build_schedule():
    """Main function to build the schedule JSON."""
    print("=" * 60)
    print("LED Matrix Display - Schedule Builder")
    print("=" * 60)
    print(f"\nStation:   {STATION_NAME}")
    print(f"Line:      {LINE_NUMBER}")
    print(f"Direction: {DIRECTION}")
    print()
    
    # Step 1: Find station stops
    print("Finding station stops...")
    station_stops = find_station_stops(STATION_NAME)
    if not station_stops:
        print(f"❌ Error: Station '{STATION_NAME}' not found in GTFS data")
        return
    print(f"✓ Found {len(station_stops)} stop points: {', '.join(station_stops)}")
    
    # Step 2: Get trips for line and direction
    print(f"\nFinding trips for line {LINE_NUMBER} towards {DIRECTION}...")
    trip_ids = get_trips_for_line_and_direction(LINE_NUMBER, DIRECTION)
    if not trip_ids:
        print(f"❌ Error: No trips found for line {LINE_NUMBER} towards {DIRECTION}")
        return
    print(f"✓ Found {len(trip_ids)} trips")
    
    # Step 3: Extract all departure times
    print("\nExtracting departure times...")
    schedule = extract_departures(station_stops, trip_ids)
    
    if not schedule:
        print("❌ Error: No departure times found")
        return
    
    # Display summary
    print("\n✓ Schedule extracted successfully!")
    print("\nDepartures per day:")
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        if day in schedule:
            count = len(schedule[day])
            first = schedule[day][0] if schedule[day] else "N/A"
            last = schedule[day][-1] if schedule[day] else "N/A"
            print(f"  {day.capitalize():10} {count:3} departures  ({first} - {last})")
    
    # Step 4: Save to JSON
    output_data = {
        "station": STATION_NAME,
        "line": LINE_NUMBER,
        "direction": DIRECTION,
        "generated": datetime.now().isoformat(),
        "schedule": schedule
    }
    
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Schedule saved to {OUTPUT_FILE.name}")
    print(f"\nFile size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print("\n" + "=" * 60)
    print("Ready to deploy to Matrix Portal!")
    print("=" * 60)


if __name__ == "__main__":
    # Check if GTFS data exists
    if not DATA_DIR.exists() or not (DATA_DIR / "stops.txt").exists():
        print("❌ Error: GTFS data not found in data/ folder")
        print("\nPlease download STM GTFS data:")
        print("1. Visit: https://www.stm.info/en/about/developers")
        print("2. Download gtfs_stm.zip")
        print("3. Extract to the data/ folder")
        exit(1)
    
    build_schedule()
