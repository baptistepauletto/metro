"""
Update Display Data Script for GitHub Actions
==============================================
Fetches stock prices, metro schedule, and current time,
then generates a JSON file for the Matrix Portal to consume.
"""

import json
import requests
from datetime import datetime
import pytz
from pathlib import Path

# Load configuration
CONFIG_FILE = Path(__file__).parent.parent.parent / "config.json"
SCHEDULE_FILE = Path(__file__).parent.parent.parent / "schedule.json"
OUTPUT_FILE = Path(__file__).parent.parent.parent / "data.json"

def load_config():
    """Load configuration from config.json"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def fetch_stock_price(symbol):
    """
    Fetch stock price from Yahoo Finance API.
    Returns dict with price, change, and change_percent, or None on error.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
        print(f"Fetching stock data for {symbol}...")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse Yahoo Finance response
        chart = data.get("chart", {})
        result_list = chart.get("result", [])
        
        if not result_list:
            print("Error: No result in Yahoo Finance response")
            return None
        
        meta = result_list[0].get("meta", {})
        
        # Extract price data
        current_price = (
            meta.get("regularMarketPrice") or
            meta.get("previousClose") or
            meta.get("chartPreviousClose")
        )
        
        previous_close = (
            meta.get("previousClose") or
            meta.get("chartPreviousClose")
        )
        
        # Fallback to historical data if needed
        if current_price is None:
            indicators = result_list[0].get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            close_prices = quote.get("close", [])
            
            if close_prices:
                for price in reversed(close_prices):
                    if price is not None:
                        current_price = price
                        break
        
        if current_price is None or previous_close is None:
            print("Error: Missing price data")
            return None
        
        # Calculate change
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100
        
        # Check if market is open (based on meta data)
        market_state = meta.get("marketState", "CLOSED")
        market_open = market_state == "REGULAR"
        
        result = {
            "symbol": symbol.replace(".TO", ""),  # Remove .TO suffix
            "price": round(current_price, 2),
            "change_percent": round(change_percent, 2),
            "market_open": market_open
        }
        
        print(f"Stock data: {result}")
        return result
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None

def get_next_metro(config):
    """
    Parse the metro schedule and find the next departure.
    Returns dict with next_departure time and minutes_until, or None.
    """
    try:
        # Load schedule
        with open(SCHEDULE_FILE, 'r') as f:
            schedule_data = json.load(f)
        
        # Get current time in Montreal timezone
        tz = pytz.timezone(config['timezone'])
        now = datetime.now(tz)
        
        # Get current day and time
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_day = days[now.weekday()]
        current_time_str = now.strftime("%H:%M")
        
        print(f"Current time: {current_time_str} on {current_day}")
        
        # Get today's schedule
        schedule = schedule_data.get('schedule', {})
        today_schedule = schedule.get(current_day, [])
        
        if not today_schedule:
            print(f"No schedule for {current_day}")
            return None
        
        # Find next departure
        next_departure = None
        for departure_time in today_schedule:
            if departure_time > current_time_str:
                next_departure = departure_time
                break
        
        # If no more departures today, get first one tomorrow
        if next_departure is None:
            tomorrow_idx = (now.weekday() + 1) % 7
            tomorrow_day = days[tomorrow_idx]
            tomorrow_schedule = schedule.get(tomorrow_day, [])
            if tomorrow_schedule:
                next_departure = tomorrow_schedule[0]
                # Calculate minutes until midnight + time
                current_minutes = now.hour * 60 + now.minute
                minutes_until_midnight = 24 * 60 - current_minutes
                departure_hour, departure_minute = map(int, next_departure.split(':'))
                minutes_until = minutes_until_midnight + departure_hour * 60 + departure_minute
            else:
                return None
        else:
            # Calculate minutes until departure
            departure_hour, departure_minute = map(int, next_departure.split(':'))
            departure_total_minutes = departure_hour * 60 + departure_minute
            current_total_minutes = now.hour * 60 + now.minute
            minutes_until = departure_total_minutes - current_total_minutes
        
        # Get line color from config
        line_colors = {
            "1": "#00B300",  # Green
            "2": "#D95700",  # Orange
            "4": "#FFD900",  # Yellow
            "5": "#0095E6",  # Blue
        }
        line_color = line_colors.get(config['metro_line'], "#FFFFFF")
        
        result = {
            "station": config['metro_station'],
            "next_departure": next_departure,
            "minutes_until": minutes_until,
            "line_color": line_color
        }
        
        print(f"Metro data: {result}")
        return result
        
    except Exception as e:
        print(f"Error getting metro data: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_current_time(timezone):
    """Get current time formatted for display."""
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        result = {
            "display": now.strftime("%H:%M"),
            "timezone": timezone,
            "date": now.strftime("%b %d").upper()  # e.g., "FEB 8"
        }
        
        print(f"Time data: {result}")
        return result
        
    except Exception as e:
        print(f"Error getting time: {e}")
        return None

def generate_data_json():
    """Main function to generate the data.json file."""
    print("=" * 60)
    print("Update Display Data Script")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    print(f"Config loaded: {config['stock_symbol']}, {config['metro_station']}")
    
    # Fetch all data
    stock_data = fetch_stock_price(config['stock_symbol'])
    metro_data = get_next_metro(config)
    time_data = get_current_time(config['timezone'])
    
    # Build output JSON
    output = {
        "updated": datetime.now(pytz.timezone("America/Montreal")).isoformat(),
        "metro": metro_data if metro_data else {
            "station": config['metro_station'],
            "next_departure": "N/A",
            "minutes_until": 0,
            "line_color": "#D95700"
        },
        "stock": stock_data if stock_data else {
            "symbol": config['stock_symbol'].replace(".TO", ""),
            "price": 0.0,
            "change_percent": 0.0,
            "market_open": False
        },
        "time": time_data if time_data else {
            "display": "00:00",
            "timezone": config['timezone'],
            "date": "N/A"
        }
    }
    
    # Write to file
    print(f"\nWriting to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("✓ Data file generated successfully!")
    print("=" * 60)
    
    # Print summary
    print("\nData Summary:")
    print(f"  Stock:  {output['stock']['symbol']} ${output['stock']['price']} ({output['stock']['change_percent']:+.1f}%)")
    print(f"  Metro:  {output['metro']['station']} in {output['metro']['minutes_until']} min")
    print(f"  Time:   {output['time']['display']} {output['time']['date']}")
    print()

if __name__ == "__main__":
    generate_data_json()
