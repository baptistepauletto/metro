"""
Service Alerts for STM Metro
============================
Fetches service alerts from STM's État du Service API.
"""

import requests
from datetime import datetime
from typing import Optional


class ServiceAlerts:
    """Fetches and parses STM service alerts."""
    
    def __init__(self):
        self._alerts_cache: list = []
        self._last_fetch: Optional[datetime] = None
        self._cache_seconds = 60  # Refresh every 60 seconds
    
    def fetch_alerts(self, api_key: str, alerts_url: str) -> list[dict]:
        """
        Fetch service alerts from STM API.
        
        Args:
            api_key: STM API key
            alerts_url: Service alerts API URL
            
        Returns:
            List of alert dictionaries
        """
        # Check cache
        now = datetime.now()
        if (self._last_fetch and 
            (now - self._last_fetch).total_seconds() < self._cache_seconds):
            return self._alerts_cache
        
        try:
            headers = {
                "apiKey": api_key,
                "Accept": "application/json"
            }
            
            response = requests.get(
                alerts_url,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            alerts = self._parse_alerts(data)
            
            self._alerts_cache = alerts
            self._last_fetch = now
            print(f"Fetched {len(alerts)} service alerts")
            return alerts
            
        except Exception as e:
            print(f"Error fetching service alerts: {e}")
            return self._alerts_cache  # Return cached data on error
    
    def _parse_alerts(self, data: dict) -> list[dict]:
        """
        Parse the raw API response into structured alerts.
        
        Args:
            data: Raw JSON response from API
            
        Returns:
            List of parsed alert dictionaries
        """
        alerts = []
        
        # The STM i3 API returns messages in a specific format
        # Adjust parsing based on actual API response structure
        messages = data if isinstance(data, list) else data.get("messages", data.get("result", []))
        
        if not isinstance(messages, list):
            messages = [messages] if messages else []
        
        for msg in messages:
            if not isinstance(msg, dict):
                continue
                
            alert = {
                "id": msg.get("id", ""),
                "title": "",
                "description": "",
                "severity": "info",  # info, warning, critical
                "affected_lines": [],
                "affected_stations": [],
                "start_time": None,
                "end_time": None,
                "is_metro": False
            }
            
            # Extract title and description (handle multiple language formats)
            title = msg.get("title", msg.get("titre", ""))
            if isinstance(title, dict):
                title = title.get("fr", title.get("en", str(title)))
            alert["title"] = str(title)
            
            description = msg.get("description", msg.get("body", msg.get("message", "")))
            if isinstance(description, dict):
                description = description.get("fr", description.get("en", str(description)))
            alert["description"] = str(description)
            
            # Determine severity
            severity = msg.get("severity", msg.get("priority", "")).lower()
            if "critical" in severity or "urgent" in severity or "major" in severity:
                alert["severity"] = "critical"
            elif "warning" in severity or "moderate" in severity:
                alert["severity"] = "warning"
            else:
                alert["severity"] = "info"
            
            # Check if it affects metro
            affected = msg.get("affected_lines", msg.get("lignes", msg.get("routes", [])))
            if isinstance(affected, str):
                affected = [affected]
            
            metro_lines = ["orange", "green", "blue", "yellow", "verte", "bleue", "jaune"]
            for line in affected:
                line_lower = str(line).lower()
                if any(metro in line_lower for metro in metro_lines) or "metro" in line_lower:
                    alert["is_metro"] = True
                    alert["affected_lines"].append(line)
            
            # Also check title/description for metro mentions
            combined_text = (alert["title"] + " " + alert["description"]).lower()
            if "métro" in combined_text or "metro" in combined_text:
                alert["is_metro"] = True
                # Try to identify specific lines
                if "orange" in combined_text:
                    alert["affected_lines"].append("orange")
                if "vert" in combined_text or "green" in combined_text:
                    alert["affected_lines"].append("green")
                if "bleu" in combined_text or "blue" in combined_text:
                    alert["affected_lines"].append("blue")
                if "jaune" in combined_text or "yellow" in combined_text:
                    alert["affected_lines"].append("yellow")
            
            # Parse times if available
            start = msg.get("start_time", msg.get("debut", msg.get("startDate")))
            end = msg.get("end_time", msg.get("fin", msg.get("endDate")))
            
            if start:
                try:
                    alert["start_time"] = str(start)
                except:
                    pass
            
            if end:
                try:
                    alert["end_time"] = str(end)
                except:
                    pass
            
            # Only include alerts with actual content
            if alert["title"] or alert["description"]:
                alerts.append(alert)
        
        return alerts
    
    def get_metro_alerts(self, api_key: str, alerts_url: str, line_color: str = None) -> list[dict]:
        """
        Get alerts specifically for metro service.
        
        Args:
            api_key: STM API key
            alerts_url: Service alerts API URL
            line_color: Optional filter for specific line (orange, green, blue, yellow)
            
        Returns:
            List of metro-related alerts
        """
        all_alerts = self.fetch_alerts(api_key, alerts_url)
        
        # Filter to metro alerts
        metro_alerts = [a for a in all_alerts if a.get("is_metro", False)]
        
        # Optionally filter by line
        if line_color:
            color_lower = line_color.lower()
            metro_alerts = [
                a for a in metro_alerts 
                if not a["affected_lines"] or  # Include if no specific line mentioned
                any(color_lower in line.lower() for line in a["affected_lines"])
            ]
        
        # Sort by severity (critical first)
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        metro_alerts.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 2))
        
        return metro_alerts


# Singleton instance
_alerts_instance: Optional[ServiceAlerts] = None


def get_service_alerts() -> ServiceAlerts:
    """Get or create the singleton ServiceAlerts instance."""
    global _alerts_instance
    if _alerts_instance is None:
        _alerts_instance = ServiceAlerts()
    return _alerts_instance


if __name__ == "__main__":
    from config import STM_API_KEY, STM_SERVICE_ALERTS_URL, LINE_COLOR
    
    if not STM_API_KEY:
        print("No API key configured. Set STM_API_KEY in .env file.")
    else:
        alerts = ServiceAlerts()
        metro_alerts = alerts.get_metro_alerts(STM_API_KEY, STM_SERVICE_ALERTS_URL, LINE_COLOR)
        
        print(f"\nFound {len(metro_alerts)} metro alerts:")
        for alert in metro_alerts:
            print(f"\n[{alert['severity'].upper()}] {alert['title']}")
            if alert['description']:
                print(f"  {alert['description'][:100]}...")
            if alert['affected_lines']:
                print(f"  Lines: {', '.join(alert['affected_lines'])}")

