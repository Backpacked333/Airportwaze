"""
CBP (Customs and Border Protection) API Integration.

Official CBP Airport Wait Times API:
- API: https://bwt.cbp.gov/api/airports
- Format: JSON REST API
- Update Frequency: ~15 minutes
- Coverage: International terminals with passport control

Documentation: https://bwt.cbp.gov/api/docs
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class CBPWaitTimeAPI:
    """Integration with CBP (Customs and Border Protection) wait times."""

    def __init__(self):
        self.base_url = "https://bwt.cbp.gov/api/airports"
        self.cache: Dict[str, Dict] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_ttl_minutes = 10

        # Mapping of CBP terminal names to our internal checkpoint IDs
        self.checkpoint_mappings = {
            "JFK": {
                "Terminal 1": "jfk-t1-passport",  # If exists
                "Terminal 4": "jfk-t4-passport",
                "Terminal 7": "jfk-t7-passport",  # If exists
            },
            "LAX": {
                "Tom Bradley International Terminal": "lax-tbit-passport",
                "TBIT": "lax-tbit-passport",
            },
            "ORD": {
                "Terminal 5": "ord-t5-passport",
            },
            "ATL": {
                "International Terminal": "atl-intl-passport",
                "Terminal F": "atl-intl-passport",
            },
            "DFW": {
                "Terminal D": "dfw-d-passport",
            },
            "SFO": {
                "International Terminal": "sfo-intl-passport",
                "Terminal G": "sfo-intl-passport",
            },
            "MIA": {
                "South Terminal": "mia-south-passport",
                "Terminal J": "mia-south-passport",
            },
            "DEN": {
                "Concourse A": "den-a-passport",
            },
            "SEA": {
                "South Satellite": "sea-south-passport",
            },
        }

    async def get_wait_times(self, airport_code: str) -> Optional[Dict[str, int]]:
        """
        Fetch current passport control/customs wait times.

        Args:
            airport_code: IATA airport code (e.g., "JFK", "LAX")

        Returns:
            Dict mapping checkpoint_id to wait time in minutes, or None if unavailable
        """
        airport_code = airport_code.upper()

        # Check cache first
        if airport_code in self.cache:
            if datetime.utcnow() < self.cache_expiry[airport_code]:
                logger.debug(f"CBP cache hit for {airport_code}")
                return self.cache[airport_code]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.base_url}/{airport_code}"
                logger.info(f"Fetching CBP data from {url}")
                response = await client.get(url)

                if response.status_code == 404:
                    logger.info(f"CBP data not available for {airport_code}")
                    return None

                if response.status_code != 200:
                    logger.warning(f"CBP API returned status {response.status_code}")
                    return None

                data = response.json()
                wait_times = self._parse_response_data(data, airport_code)

                # Cache result if we found data
                if wait_times:
                    self.cache[airport_code] = wait_times
                    self.cache_expiry[airport_code] = datetime.utcnow() + timedelta(
                        minutes=self.cache_ttl_minutes
                    )
                    logger.info(f"CBP data cached for {airport_code}: {len(wait_times)} checkpoints")

                return wait_times if wait_times else None

        except httpx.TimeoutException:
            logger.error("CBP API request timed out")
            return None
        except Exception as e:
            logger.error(f"CBP API error: {e}")
            return None

    def _parse_response_data(self, data: dict, airport_code: str) -> Dict[str, int]:
        """Parse CBP JSON response to extract wait times."""
        wait_times = {}

        # CBP API structure varies, try multiple formats
        # Format 1: Direct passport_control field
        if "passport_control" in data and isinstance(data["passport_control"], dict):
            wait_minutes = self._extract_wait_time(data["passport_control"])
            if wait_minutes is not None:
                # Use default mapping for airport
                checkpoint_id = self._get_default_checkpoint(airport_code)
                if checkpoint_id:
                    wait_times[checkpoint_id] = wait_minutes

        # Format 2: Terminals array
        if "terminals" in data and isinstance(data["terminals"], list):
            for terminal in data["terminals"]:
                terminal_name = terminal.get("name", "")

                # Check for passport control data
                if "passport_control" in terminal:
                    wait_minutes = self._extract_wait_time(terminal["passport_control"])
                    if wait_minutes is not None:
                        checkpoint_id = self._map_terminal_name(airport_code, terminal_name)
                        if checkpoint_id:
                            wait_times[checkpoint_id] = wait_minutes

                # Some airports have 'immigration' field instead
                if "immigration" in terminal:
                    wait_minutes = self._extract_wait_time(terminal["immigration"])
                    if wait_minutes is not None:
                        checkpoint_id = self._map_terminal_name(airport_code, terminal_name)
                        if checkpoint_id:
                            wait_times[checkpoint_id] = wait_minutes

        # Format 3: Array of wait time objects
        if "wait_times" in data and isinstance(data["wait_times"], list):
            for wt in data["wait_times"]:
                terminal_name = wt.get("terminal", "")
                wait_minutes = self._extract_wait_time(wt)

                if wait_minutes is not None:
                    checkpoint_id = self._map_terminal_name(airport_code, terminal_name)
                    if checkpoint_id:
                        wait_times[checkpoint_id] = wait_minutes

        return wait_times

    def _extract_wait_time(self, wait_obj: dict) -> Optional[int]:
        """
        Extract wait time from various CBP response formats.

        CBP provides multiple wait time fields:
        - wait_time: Current wait
        - average_wait_time: Average for time of day
        - maximum_wait_time: Maximum observed

        We prefer 'wait_time' or 'average_wait_time'.
        """
        # Try different field names
        for field in ["wait_time", "average_wait_time", "avg_wait_time", "current_wait"]:
            if field in wait_obj:
                try:
                    wait_val = wait_obj[field]
                    if isinstance(wait_val, (int, float)):
                        return int(wait_val)
                    elif isinstance(wait_val, str):
                        # Remove " min" or similar suffixes
                        wait_val = wait_val.replace("min", "").replace("minutes", "").strip()
                        return int(wait_val)
                except (ValueError, TypeError):
                    continue

        return None

    def _map_terminal_name(self, airport_code: str, terminal_name: str) -> Optional[str]:
        """Map CBP terminal name to our internal checkpoint ID."""
        airport_mappings = self.checkpoint_mappings.get(airport_code, {})

        # Try exact match
        if terminal_name in airport_mappings:
            return airport_mappings[terminal_name]

        # Try fuzzy matching
        terminal_normalized = " ".join(terminal_name.lower().split())
        for mapped_name, checkpoint_id in airport_mappings.items():
            mapped_normalized = " ".join(mapped_name.lower().split())
            if terminal_normalized in mapped_normalized or mapped_normalized in terminal_normalized:
                return checkpoint_id

        return None

    def _get_default_checkpoint(self, airport_code: str) -> Optional[str]:
        """Get default passport control checkpoint for airport."""
        mappings = self.checkpoint_mappings.get(airport_code, {})
        # Return first mapping as default
        return next(iter(mappings.values())) if mappings else None

    async def get_historical_data(
        self,
        airport_code: str,
        days_back: int = 7
    ) -> Optional[Dict]:
        """
        Fetch historical wait time data for analysis.

        Args:
            airport_code: IATA airport code
            days_back: Number of days of historical data

        Returns:
            Historical data dict with hourly patterns
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.base_url}/{airport_code}/history"
                params = {"days": days_back}
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    return None

                return response.json()

        except Exception as e:
            logger.error(f"CBP historical data error: {e}")
            return None

    def clear_cache(self, airport_code: Optional[str] = None):
        """Clear cache for specific airport or all airports."""
        if airport_code:
            self.cache.pop(airport_code.upper(), None)
            self.cache_expiry.pop(airport_code.upper(), None)
        else:
            self.cache.clear()
            self.cache_expiry.clear()
