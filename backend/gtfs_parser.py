"""
GTFS Parser for STM Metro Data
==============================
Loads and queries STM's static GTFS schedule data and real-time updates
to find upcoming metro departures for a specific station and direction.
"""

import os
import zipfile
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Path to data directory (relative to project root)
DATA_DIR = Path(__file__).parent.parent / "data"
GTFS_URL = "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip"


class GTFSParser:
    """Parses STM GTFS data to find metro departure times."""
    
    def __init__(self):
        self.stops_df: Optional[pd.DataFrame] = None
        self.stop_times_df: Optional[pd.DataFrame] = None
        self.trips_df: Optional[pd.DataFrame] = None
        self.routes_df: Optional[pd.DataFrame] = None
        self.calendar_df: Optional[pd.DataFrame] = None
        self.calendar_dates_df: Optional[pd.DataFrame] = None
        self._loaded = False
        
        # Real-time data cache
        self._realtime_updates: dict = {}
        self._realtime_last_fetch: Optional[datetime] = None
        self._realtime_cache_seconds = 30  # Refresh every 30 seconds
    
    def download_gtfs(self, force: bool = False) -> bool:
        """
        Download the STM GTFS data if not already present.
        
        Args:
            force: If True, re-download even if data exists
            
        Returns:
            True if download was successful or data already exists
        """
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = DATA_DIR / "gtfs_stm.zip"
        stops_path = DATA_DIR / "stops.txt"
        
        # Check if we already have the data
        if stops_path.exists() and not force:
            print("GTFS data already exists. Use force=True to re-download.")
            return True
        
        print(f"Downloading GTFS data from {GTFS_URL}...")
        try:
            response = requests.get(GTFS_URL, timeout=60)
            response.raise_for_status()
            
            with open(zip_path, "wb") as f:
                f.write(response.content)
            
            print("Extracting GTFS data...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(DATA_DIR)
            
            # Clean up zip file
            zip_path.unlink()
            print("GTFS data downloaded and extracted successfully!")
            return True
            
        except Exception as e:
            print(f"Error downloading GTFS data: {e}")
            return False
    
    def load_data(self) -> bool:
        """
        Load GTFS data files into memory.
        
        Returns:
            True if data was loaded successfully
        """
        if self._loaded:
            return True
            
        required_files = ["stops.txt", "stop_times.txt", "trips.txt", "routes.txt"]
        
        for filename in required_files:
            filepath = DATA_DIR / filename
            if not filepath.exists():
                print(f"Missing GTFS file: {filename}")
                print("Please run download_gtfs() first.")
                return False
        
        print("Loading GTFS data...")
        
        try:
            self.stops_df = pd.read_csv(DATA_DIR / "stops.txt", dtype=str)
            self.stop_times_df = pd.read_csv(DATA_DIR / "stop_times.txt", dtype=str)
            self.trips_df = pd.read_csv(DATA_DIR / "trips.txt", dtype=str)
            self.routes_df = pd.read_csv(DATA_DIR / "routes.txt", dtype=str)
            
            # Calendar files are optional
            calendar_path = DATA_DIR / "calendar.txt"
            if calendar_path.exists():
                self.calendar_df = pd.read_csv(calendar_path, dtype=str)
            
            calendar_dates_path = DATA_DIR / "calendar_dates.txt"
            if calendar_dates_path.exists():
                self.calendar_dates_df = pd.read_csv(calendar_dates_path, dtype=str)
            
            self._loaded = True
            print(f"Loaded {len(self.stops_df)} stops, {len(self.stop_times_df)} stop times")
            return True
            
        except Exception as e:
            print(f"Error loading GTFS data: {e}")
            return False
    
    def find_station_id(self, station_name: str) -> Optional[str]:
        """
        Find the stop_id for a given station name.
        
        Args:
            station_name: Name of the metro station (e.g., "Rosemont")
            
        Returns:
            The stop_id if found, None otherwise
        """
        if not self._loaded:
            return None
        
        # Metro stations in STM GTFS typically have location_type = 1 (station)
        # and their names contain the station name
        matches = self.stops_df[
            self.stops_df["stop_name"].str.contains(station_name, case=False, na=False)
        ]
        
        if matches.empty:
            print(f"No station found matching '{station_name}'")
            return None
        
        # Prefer metro stations (they usually have specific patterns)
        # STM metro stop_ids often start with specific prefixes
        for _, row in matches.iterrows():
            stop_id = row["stop_id"]
            stop_name = row["stop_name"]
            # Return the first match that looks like a metro station
            if station_name.lower() in stop_name.lower():
                return stop_id
        
        # Fallback to first match
        return matches.iloc[0]["stop_id"]
    
    def find_metro_route_id(self, line_color: str) -> Optional[str]:
        """
        Find the route_id for a metro line by color.
        
        Args:
            line_color: Color of the line ("orange", "green", "blue", "yellow")
            
        Returns:
            The route_id if found, None otherwise
        """
        if not self._loaded or self.routes_df is None:
            return None
        
        # STM metro lines are typically route_type = 1 (subway)
        metro_routes = self.routes_df[
            self.routes_df["route_type"] == "1"
        ]
        
        # Try to match by route name or short name
        color_lower = line_color.lower()
        for _, row in metro_routes.iterrows():
            route_name = str(row.get("route_long_name", "")).lower()
            route_short = str(row.get("route_short_name", "")).lower()
            
            if color_lower in route_name or color_lower in route_short:
                return row["route_id"]
        
        # If no color match, return first metro route as fallback
        if not metro_routes.empty:
            return metro_routes.iloc[0]["route_id"]
        
        return None
    
    def get_service_ids_for_today(self) -> list:
        """
        Get the service_ids that are active today.
        
        Returns:
            List of active service_ids
        """
        today = datetime.now()
        today_str = today.strftime("%Y%m%d")
        day_name = today.strftime("%A").lower()
        
        active_services = []
        
        # Check calendar.txt for regular service
        if self.calendar_df is not None:
            for _, row in self.calendar_df.iterrows():
                start_date = row.get("start_date", "")
                end_date = row.get("end_date", "")
                
                # Check if today is within the service period
                if start_date <= today_str <= end_date:
                    # Check if service runs on this day of week
                    if row.get(day_name, "0") == "1":
                        active_services.append(row["service_id"])
        
        # Check calendar_dates.txt for exceptions
        if self.calendar_dates_df is not None:
            exceptions = self.calendar_dates_df[
                self.calendar_dates_df["date"] == today_str
            ]
            for _, row in exceptions.iterrows():
                service_id = row["service_id"]
                exception_type = row.get("exception_type", "1")
                
                if exception_type == "1":  # Service added
                    if service_id not in active_services:
                        active_services.append(service_id)
                elif exception_type == "2":  # Service removed
                    if service_id in active_services:
                        active_services.remove(service_id)
        
        return active_services
    
    def fetch_realtime_updates(self, api_key: str, gtfs_rt_url: str) -> dict:
        """
        Fetch real-time trip updates from STM's GTFS-RT API.
        
        Args:
            api_key: STM API key
            gtfs_rt_url: Base URL for GTFS-RT API
            
        Returns:
            Dictionary mapping (trip_id, stop_id) to delay in seconds
        """
        # Check cache
        now = datetime.now()
        if (self._realtime_last_fetch and 
            (now - self._realtime_last_fetch).total_seconds() < self._realtime_cache_seconds):
            return self._realtime_updates
        
        try:
            from google.transit import gtfs_realtime_pb2
            
            # Fetch trip updates
            headers = {
                "apiKey": api_key,
                "Accept": "application/x-protobuf"
            }
            
            response = requests.get(
                f"{gtfs_rt_url}/tripUpdates",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            # Parse protobuf
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            updates = {}
            for entity in feed.entity:
                if entity.HasField("trip_update"):
                    trip_update = entity.trip_update
                    trip_id = trip_update.trip.trip_id
                    
                    for stop_time_update in trip_update.stop_time_update:
                        stop_id = stop_time_update.stop_id
                        
                        # Get arrival delay (or departure delay as fallback)
                        delay = 0
                        arrival_time = None
                        
                        if stop_time_update.HasField("arrival"):
                            delay = stop_time_update.arrival.delay
                            if stop_time_update.arrival.time:
                                arrival_time = stop_time_update.arrival.time
                        elif stop_time_update.HasField("departure"):
                            delay = stop_time_update.departure.delay
                            if stop_time_update.departure.time:
                                arrival_time = stop_time_update.departure.time
                        
                        updates[(trip_id, stop_id)] = {
                            "delay": delay,
                            "arrival_time": arrival_time
                        }
            
            self._realtime_updates = updates
            self._realtime_last_fetch = now
            print(f"Fetched {len(updates)} real-time updates")
            return updates
            
        except ImportError:
            print("gtfs-realtime-bindings not installed. Run: pip install gtfs-realtime-bindings")
            return {}
        except Exception as e:
            print(f"Error fetching real-time updates: {e}")
            return self._realtime_updates  # Return cached data on error
    
    def get_next_departures(
        self,
        station_name: str,
        line_color: str,
        direction: str,
        num_results: int = 3,
        api_key: str = None,
        gtfs_rt_url: str = None
    ) -> list[dict]:
        """
        Get the next departures for a station.
        
        Args:
            station_name: Name of the station
            line_color: Color of the metro line
            direction: Direction of travel (terminus name)
            num_results: Number of departures to return
            api_key: Optional STM API key for real-time data
            gtfs_rt_url: Optional GTFS-RT API URL
            
        Returns:
            List of departure dictionaries with 'time', 'minutes', and 'realtime' keys
        """
        if not self._loaded:
            if not self.load_data():
                return []
        
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        
        # Fetch real-time updates if API key provided
        realtime_updates = {}
        if api_key and gtfs_rt_url:
            realtime_updates = self.fetch_realtime_updates(api_key, gtfs_rt_url)
        
        # Find all stops that match the station name
        station_stops = self.stops_df[
            self.stops_df["stop_name"].str.contains(station_name, case=False, na=False)
        ]["stop_id"].tolist()
        
        if not station_stops:
            print(f"No stops found for station: {station_name}")
            return []
        
        # Find metro route
        route_id = self.find_metro_route_id(line_color)
        
        # Get active services for today
        active_services = self.get_service_ids_for_today()
        
        # If no calendar data, try to get all trips (some GTFS feeds work differently)
        if not active_services:
            active_services = self.trips_df["service_id"].unique().tolist()
        
        # Filter trips by route and direction
        trips_filtered = self.trips_df.copy()
        
        if route_id:
            trips_filtered = trips_filtered[trips_filtered["route_id"] == route_id]
        
        # Filter by service
        trips_filtered = trips_filtered[
            trips_filtered["service_id"].isin(active_services)
        ]
        
        # Filter by direction using trip_headsign
        if direction:
            trips_filtered = trips_filtered[
                trips_filtered["trip_headsign"].str.contains(direction, case=False, na=False)
            ]
        
        trip_ids = trips_filtered["trip_id"].tolist()
        
        if not trip_ids:
            print(f"No trips found for {line_color} line towards {direction}")
            # Fallback: try without direction filter
            trips_filtered = self.trips_df.copy()
            if route_id:
                trips_filtered = trips_filtered[trips_filtered["route_id"] == route_id]
            trip_ids = trips_filtered["trip_id"].tolist()
        
        # Get stop times for our station and trips
        stop_times = self.stop_times_df[
            (self.stop_times_df["stop_id"].isin(station_stops)) &
            (self.stop_times_df["trip_id"].isin(trip_ids))
        ].copy()
        
        if stop_times.empty:
            print(f"No stop times found for {station_name}")
            return []
        
        # Filter to future departures
        stop_times = stop_times[stop_times["departure_time"] >= current_time]
        
        # Sort by departure time
        stop_times = stop_times.sort_values("departure_time")
        
        # Get next N departures
        departures = []
        for _, row in stop_times.head(num_results * 2).iterrows():  # Get extra in case some are filtered
            if len(departures) >= num_results:
                break
                
            dep_time_str = row["departure_time"]
            trip_id = row["trip_id"]
            stop_id = row["stop_id"]
            
            # Parse departure time (handle times > 24:00 for overnight service)
            try:
                hours, minutes, seconds = map(int, dep_time_str.split(":"))
                if hours >= 24:
                    hours -= 24
                    dep_datetime = datetime.combine(
                        now.date() + timedelta(days=1),
                        datetime.strptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}", "%H:%M:%S").time()
                    )
                else:
                    dep_datetime = datetime.combine(
                        now.date(),
                        datetime.strptime(dep_time_str, "%H:%M:%S").time()
                    )
                
                # Apply real-time delay if available
                is_realtime = False
                rt_key = (trip_id, stop_id)
                if rt_key in realtime_updates:
                    rt_data = realtime_updates[rt_key]
                    delay_seconds = rt_data.get("delay", 0)
                    
                    # If we have an absolute arrival time, use it
                    if rt_data.get("arrival_time"):
                        dep_datetime = datetime.fromtimestamp(rt_data["arrival_time"])
                    else:
                        # Otherwise apply delay
                        dep_datetime += timedelta(seconds=delay_seconds)
                    
                    is_realtime = True
                
                # Calculate minutes until departure
                delta = dep_datetime - now
                minutes_until = int(delta.total_seconds() / 60)
                
                if minutes_until >= 0:
                    departures.append({
                        "time": dep_datetime.strftime("%H:%M"),
                        "minutes": minutes_until,
                        "realtime": is_realtime,
                        "trip_id": trip_id
                    })
            except Exception as e:
                print(f"Error parsing time {dep_time_str}: {e}")
                continue
        
        return departures[:num_results]


# Singleton instance for the application
_parser_instance: Optional[GTFSParser] = None


def get_parser() -> GTFSParser:
    """Get or create the singleton GTFSParser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = GTFSParser()
    return _parser_instance


if __name__ == "__main__":
    # Test the parser
    from config import STATION_NAME, LINE_COLOR, DIRECTION, STM_API_KEY, STM_GTFS_RT_URL
    
    parser = GTFSParser()
    parser.download_gtfs()
    parser.load_data()
    
    departures = parser.get_next_departures(
        station_name=STATION_NAME,
        line_color=LINE_COLOR,
        direction=DIRECTION,
        num_results=3,
        api_key=STM_API_KEY,
        gtfs_rt_url=STM_GTFS_RT_URL
    )
    
    print("\nNext departures:")
    for dep in departures:
        rt_indicator = " (LIVE)" if dep.get("realtime") else " (scheduled)"
        print(f"  {dep['time']} ({dep['minutes']} min){rt_indicator}")
