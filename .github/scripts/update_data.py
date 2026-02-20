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

def fetch_asset_price(symbol, display_name, max_retries=3):
    """
    Fetch asset price from Yahoo Finance API.
    Returns dict with symbol, price, change_percent, or None on error.
    Includes retry logic for rate limiting.
    
    Args:
        symbol: Yahoo Finance symbol (e.g., "XEQT.TO", "BTC-USD", "GC=F", "^GSPC")
        display_name: Short display name (e.g., "XEQT", "BTC", "GOLD", "SPX")
    """
    for attempt in range(max_retries):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
            print(f"Fetching {display_name} ({symbol})... (attempt {attempt + 1}/{max_retries})")
            
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
                print(f"Error: No result in Yahoo Finance response for {display_name}")
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
                print(f"Error: Missing price data for {display_name}")
                return None
            
            # Calculate change
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            result = {
                "symbol": display_name,
                "price": round(current_price, 2),
                "change_percent": round(change_percent, 2)
            }
            
            print(f"{display_name} data: ${result['price']} ({result['change_percent']:+.2f}%)")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                if attempt < max_retries - 1:  # Don't wait on last attempt
                    time.sleep(wait_time)
                continue
            else:
                print(f"HTTP Error fetching {display_name}: {e}")
                return None
        except Exception as e:
            print(f"Error fetching {display_name}: {e}")
            return None
    
    print(f"Failed to fetch {display_name} after {max_retries} attempts")
    return None


def check_market_open(symbol="XEQT.TO"):
    """
    Check if the market is currently open for a given symbol.
    Returns True if open, False otherwise.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
        current_trading_period = meta.get("currentTradingPeriod", {})
        regular_period = current_trading_period.get("regular", {})
        
        if regular_period:
            current_timestamp = int(time.time())
            market_start = regular_period.get("start")
            market_end = regular_period.get("end")
            
            if market_start and market_end:
                market_open = market_start <= current_timestamp < market_end
                print(f"Market open: {market_open}")
                return market_open
    except Exception as e:
        print(f"Error checking market hours: {e}")
    
    return False

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
        
        # Find next 30 departures (GitHub Actions cron is unreliable, can run every 2+ hours)
        next_departures = []
        for departure_time in today_schedule:
            if departure_time > current_time_str:
                next_departures.append(departure_time)
                if len(next_departures) >= 30:
                    break
        
        # If not enough departures today, add from tomorrow
        if len(next_departures) < 30:
            tomorrow_idx = (now.weekday() + 1) % 7
            tomorrow_day = days[tomorrow_idx]
            tomorrow_schedule = schedule.get(tomorrow_day, [])
            # Add as many as needed to get to 30 total
            needed = 30 - len(next_departures)
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
    
    # Define all assets to fetch
    assets_config = [
        {"symbol": config['stock_symbol'], "display_name": "XEQT", "color": "blue"},
        {"symbol": "BTC-USD", "display_name": "BTC", "color": "orange"},
        {"symbol": "GC=F", "display_name": "GOLD", "color": "yellow"},
        {"symbol": "^GSPC", "display_name": "SPX", "color": "purple"}
    ]
    
    # Fetch all assets
    print("\nFetching all assets...")
    assets_data = []
    for asset_config in assets_config:
        asset_data = fetch_asset_price(asset_config["symbol"], asset_config["display_name"])
        if asset_data:
            asset_data["color"] = asset_config["color"]
            assets_data.append(asset_data)
        else:
            # Use cached data if available
            if cached_data and 'assets' in cached_data:
                for cached_asset in cached_data['assets']:
                    if cached_asset['symbol'] == asset_config["display_name"]:
                        print(f"Using cached data for {asset_config['display_name']}")
                        assets_data.append(cached_asset)
                        break
                else:
                    # No cached data, use placeholder
                    assets_data.append({
                        "symbol": asset_config["display_name"],
                        "price": 0.0,
                        "change_percent": 0.0,
                        "color": asset_config["color"]
                    })
            else:
                # No cached data available
                assets_data.append({
                    "symbol": asset_config["display_name"],
                    "price": 0.0,
                    "change_percent": 0.0,
                    "color": asset_config["color"]
                })
    
    # Check market status (using XEQT as reference)
    market_open = check_market_open(config['stock_symbol'])
    
    # Fetch metro and time data
    metro_data = get_next_metro(config)
    time_data = get_current_time(config['timezone'])
    
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
        "assets": assets_data,
        "market_open": market_open,
        # Keep legacy "stock" field for backward compatibility
        "stock": {
            "symbol": assets_data[0]["symbol"] if assets_data else "XEQT",
            "price": assets_data[0]["price"] if assets_data else 0.0,
            "change_percent": assets_data[0]["change_percent"] if assets_data else 0.0,
            "market_open": market_open
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
    
    print("[OK] Data file generated successfully!")
    print("=" * 60)
    
    # Print summary
    print("\nData Summary:")
    for asset in assets_data:
        print(f"  {asset['symbol']:6} ${asset['price']:>8.2f} ({asset['change_percent']:+.1f}%)")
    print(f"  Market: {'OPEN' if market_open else 'CLOSED'}")
    print(f"  Metro:  {output['metro']['station']} in {output['metro']['minutes_until']} min")
    print(f"  Time:   {output['time']['display']} {output['time']['date']}")
    print()

if __name__ == "__main__":
    generate_data_json()
