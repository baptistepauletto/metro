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
import time
from pathlib import Path

# Load configuration
CONFIG_FILE = Path(__file__).parent.parent.parent / "config.json"
SCHEDULE_FILE = Path(__file__).parent.parent.parent / "schedule.json"
OUTPUT_FILE = Path(__file__).parent.parent.parent / "data.json"

def load_config():
    """Load configuration from config.json"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def fetch_stock_price(symbol, max_retries=3):
    """
    Fetch stock price from Yahoo Finance API.
    Returns dict with price, change, and change_percent, or None on error.
    Includes retry logic for rate limiting.
    """
    for attempt in range(max_retries):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
            print(f"Fetching stock data for {symbol}... (attempt {attempt + 1}/{max_retries})")
            
            # Add headers to avoid rate limiting
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
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
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                if attempt < max_retries - 1:  # Don't wait on last attempt
                    time.sleep(wait_time)
                continue
            else:
                print(f"HTTP Error fetching stock data: {e}")
                return None
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            return None
    
    print(f"Failed to fetch stock data after {max_retries} attempts")
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
        
        # Find next 5 departures (since GitHub Actions runs every 15 min)
        next_departures = []
        for departure_time in today_schedule:
            if departure_time > current_time_str:
                next_departures.append(departure_time)
                if len(next_departures) >= 5:
                    break
        
        # If not enough departures today, add from tomorrow
        if len(next_departures) < 5:
            tomorrow_idx = (now.weekday() + 1) % 7
            tomorrow_day = days[tomorrow_idx]
            tomorrow_schedule = schedule.get(tomorrow_day, [])
            # Add as many as needed to get to 5 total
            needed = 5 - len(next_departures)
            next_departures.extend(tomorrow_schedule[:needed])
        
        if not next_departures:
            return None
        
        # Calculate minutes until first departure
        first_departure = next_departures[0]
        departure_hour, departure_minute = map(int, first_departure.split(':'))
        departure_total_minutes = departure_hour * 60 + departure_minute
        current_total_minutes = now.hour * 60 + now.minute
        minutes_until = departure_total_minutes - current_total_minutes
        
        # Handle next-day departures
        if minutes_until < 0:
            minutes_until += 24 * 60
        
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
            "next_departures": next_departures,  # Array of next 5 times
            "next_departure": next_departures[0],  # Keep for backward compatibility
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

def load_cached_data():
    """Load cached data from previous data.json if it exists."""
    try:
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Could not load cached data: {e}")
    return None

def generate_data_json():
    """Main function to generate the data.json file."""
    print("=" * 60)
    print("Update Display Data Script")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    print(f"Config loaded: {config['stock_symbol']}, {config['metro_station']}")
    
    # Try to load cached data for fallback
    cached_data = load_cached_data()
    
    # Fetch all data
    stock_data = fetch_stock_price(config['stock_symbol'])
    metro_data = get_next_metro(config)
    time_data = get_current_time(config['timezone'])
    
    # Use cached stock data if fetch fails
    if not stock_data and cached_data and 'stock' in cached_data:
        print("Using cached stock data")
        stock_data = cached_data['stock']
    
    # Build output JSON
    output = {
        "updated": datetime.now(pytz.timezone("America/Montreal")).isoformat() + "Z",
        "metro": metro_data if metro_data else {
            "station": config['metro_station'],
            "next_departures": [],
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
