"""
TSA (Transportation Security Administration) API Integration.

Official MyTSA Wait Time Data:
- API: https://www.tsa.gov/data/apcp.xml
- Format: XML
- Update Frequency: ~5 minutes
- Coverage: Major US airports with TSA checkpoints

Note: TSA data quality varies by airport. Use as one signal among many.
"""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class TSAWaitTimeAPI:
    """Integration with TSA MyTSA wait time data."""

    def __init__(self):
        self.base_url = "https://www.tsa.gov/data/apcp.xml"
        self.cache: Dict[str, Dict] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_ttl_minutes = 5

        # Mapping of TSA checkpoint names to our internal IDs
        # This should be maintained as we add more airports
        self.checkpoint_mappings = {
            "JFK": {
                "Terminal 1 Security": "jfk-t1-tsa-1",
                "Terminal 1 PreCheck": "jfk-t1-tsa-pre",
                "Terminal 4 Security A": "jfk-t4-tsa-1",
                "Terminal 4 Security B": "jfk-t4-tsa-2",
                "Terminal 4 PreCheck": "jfk-t4-tsa-pre",
                "Terminal 5 Security": "jfk-t5-tsa-1",
                "Terminal 5 PreCheck": "jfk-t5-tsa-pre",
                "Terminal 7 Security": "jfk-t7-tsa-1",
                "Terminal 7 PreCheck": "jfk-t7-tsa-pre",
                "Terminal 8 Security": "jfk-t8-tsa-1",
                "Terminal 8 PreCheck": "jfk-t8-tsa-pre",
            },
            "LAX": {
                "Terminal 1 Security": "lax-t1-tsa",
                "Terminal 1 PreCheck": "lax-t1-tsa-pre",
                "Terminal 2 Security": "lax-t2-tsa",
                "Terminal 2 PreCheck": "lax-t2-tsa-pre",
                "Terminal 3 Security": "lax-t3-tsa",
                "Terminal 3 PreCheck": "lax-t3-tsa-pre",
                "Terminal 4 Security": "lax-t4-tsa",
                "Terminal 5 Security": "lax-t5-tsa",
                "Terminal 6 Security": "lax-t6-tsa",
                "Terminal 7 Security": "lax-t7-tsa",
                "Terminal 8 Security": "lax-t8-tsa",
                "TBIT Security": "lax-tbit-tsa",
                "TBIT PreCheck": "lax-tbit-tsa-pre",
            },
            "ORD": {
                "Terminal 1 Security L": "ord-t1-tsa-1",
                "Terminal 1 Security C": "ord-t1-tsa-2",
                "Terminal 1 PreCheck": "ord-t1-tsa-pre",
                "Terminal 2 Security": "ord-t2-tsa",
                "Terminal 2 PreCheck": "ord-t2-tsa-pre",
                "Terminal 3 Security H": "ord-t3-tsa-h",
                "Terminal 3 Security K": "ord-t3-tsa-k",
                "Terminal 3 PreCheck": "ord-t3-tsa-pre",
                "Terminal 5 Security": "ord-t5-tsa",
                "Terminal 5 PreCheck": "ord-t5-tsa-pre",
            },
            "ATL": {
                "North Security": "atl-north-tsa",
                "North PreCheck": "atl-north-tsa-pre",
                "South Security": "atl-south-tsa",
                "South PreCheck": "atl-south-tsa-pre",
                "International Security": "atl-intl-tsa",
                "International PreCheck": "atl-intl-tsa-pre",
            },
            "DFW": {
                "Terminal A Security": "dfw-a-tsa",
                "Terminal A PreCheck": "dfw-a-tsa-pre",
                "Terminal B Security": "dfw-b-tsa",
                "Terminal B PreCheck": "dfw-b-tsa-pre",
                "Terminal C Security": "dfw-c-tsa",
                "Terminal C PreCheck": "dfw-c-tsa-pre",
                "Terminal D Security": "dfw-d-tsa",
                "Terminal D PreCheck": "dfw-d-tsa-pre",
                "Terminal E Security": "dfw-e-tsa",
                "Terminal E PreCheck": "dfw-e-tsa-pre",
            },
            "SFO": {
                "Terminal 1 Security": "sfo-t1-tsa",
                "Terminal 1 PreCheck": "sfo-t1-tsa-pre",
                "Terminal 2 Security": "sfo-t2-tsa",
                "Terminal 2 PreCheck": "sfo-t2-tsa-pre",
                "Terminal 3 Security": "sfo-t3-tsa",
                "Terminal 3 PreCheck": "sfo-t3-tsa-pre",
                "International Security": "sfo-intl-tsa",
                "International PreCheck": "sfo-intl-tsa-pre",
            },
            "MIA": {
                "North Terminal Security": "mia-north-tsa",
                "North Terminal PreCheck": "mia-north-tsa-pre",
                "Central Terminal Security": "mia-central-tsa",
                "Central Terminal PreCheck": "mia-central-tsa-pre",
                "South Terminal Security": "mia-south-tsa",
                "South Terminal PreCheck": "mia-south-tsa-pre",
            },
            "DEN": {
                "North Security": "den-main-tsa-n",
                "South Security": "den-main-tsa-s",
                "TSA PreCheck": "den-main-tsa-pre",
                "Concourse A Security": "den-a-tsa",
            },
            "SEA": {
                "Checkpoint 1": "sea-main-tsa-1",
                "Checkpoint 2": "sea-main-tsa-2",
                "Checkpoint 3": "sea-main-tsa-3",
                "TSA PreCheck": "sea-main-tsa-pre",
            },
        }

    async def get_wait_times(self, airport_code: str) -> Optional[Dict[str, int]]:
        """
        Fetch current TSA wait times for an airport.

        Args:
            airport_code: IATA airport code (e.g., "JFK", "LAX")

        Returns:
            Dict mapping checkpoint_id to wait time in minutes, or None if unavailable
        """
        airport_code = airport_code.upper()

        # Check cache first
        if airport_code in self.cache:
            if datetime.utcnow() < self.cache_expiry[airport_code]:
                logger.debug(f"TSA cache hit for {airport_code}")
                return self.cache[airport_code]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"Fetching TSA data from {self.base_url}")
                response = await client.get(self.base_url)

                if response.status_code != 200:
                    logger.warning(f"TSA API returned status {response.status_code}")
                    return None

                # Parse XML
                try:
                    root = ET.fromstring(response.content)
                except ET.ParseError as e:
                    logger.error(f"Failed to parse TSA XML: {e}")
                    return None

                # Find airport data in XML
                wait_times = self._parse_airport_data(root, airport_code)

                # Cache result if we found data
                if wait_times:
                    self.cache[airport_code] = wait_times
                    self.cache_expiry[airport_code] = datetime.utcnow() + timedelta(
                        minutes=self.cache_ttl_minutes
                    )
                    logger.info(f"TSA data cached for {airport_code}: {len(wait_times)} checkpoints")

                return wait_times if wait_times else None

        except httpx.TimeoutException:
            logger.error("TSA API request timed out")
            return None
        except Exception as e:
            logger.error(f"TSA API error: {e}")
            return None

    def _parse_airport_data(self, root: ET.Element, airport_code: str) -> Dict[str, int]:
        """Parse XML to extract wait times for specific airport."""
        wait_times = {}

        # TSA XML structure: <Airports><Airport><AirportCode>JFK</AirportCode>...</Airport></Airports>
        for airport_elem in root.findall(".//Airport"):
            code_elem = airport_elem.find("AirportCode")
            if code_elem is None or code_elem.text != airport_code:
                continue

            # Found our airport, now parse checkpoints
            for checkpoint_elem in airport_elem.findall(".//Checkpoint"):
                name_elem = checkpoint_elem.find("Name")
                wait_elem = checkpoint_elem.find("WaitTime")

                if name_elem is None or wait_elem is None:
                    continue

                checkpoint_name = name_elem.text.strip()
                wait_time_str = wait_elem.text.strip()

                # Convert wait time to integer
                try:
                    wait_minutes = int(wait_time_str)
                except ValueError:
                    logger.warning(f"Invalid wait time for {checkpoint_name}: {wait_time_str}")
                    continue

                # Map TSA checkpoint name to our internal ID
                checkpoint_id = self._map_checkpoint_name(airport_code, checkpoint_name)
                if checkpoint_id:
                    wait_times[checkpoint_id] = wait_minutes
                else:
                    logger.debug(f"No mapping found for TSA checkpoint: {airport_code}/{checkpoint_name}")

        return wait_times

    def _map_checkpoint_name(self, airport_code: str, tsa_name: str) -> Optional[str]:
        """
        Map TSA checkpoint name to our internal checkpoint ID.

        Args:
            airport_code: Airport code
            tsa_name: Checkpoint name from TSA data

        Returns:
            Our internal checkpoint ID, or None if no mapping exists
        """
        airport_mappings = self.checkpoint_mappings.get(airport_code, {})

        # Try exact match first
        if tsa_name in airport_mappings:
            return airport_mappings[tsa_name]

        # Try fuzzy matching (case-insensitive, ignore extra spaces)
        tsa_name_normalized = " ".join(tsa_name.lower().split())
        for mapped_name, checkpoint_id in airport_mappings.items():
            mapped_name_normalized = " ".join(mapped_name.lower().split())
            if tsa_name_normalized == mapped_name_normalized:
                return checkpoint_id

        return None

    async def get_all_airports(self) -> List[str]:
        """
        Get list of all airports with TSA data available.

        Returns:
            List of IATA airport codes
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url)

                if response.status_code != 200:
                    return []

                root = ET.fromstring(response.content)
                airports = []

                for airport_elem in root.findall(".//Airport"):
                    code_elem = airport_elem.find("AirportCode")
                    if code_elem is not None:
                        airports.append(code_elem.text)

                return airports

        except Exception as e:
            logger.error(f"Failed to get TSA airport list: {e}")
            return []

    def clear_cache(self, airport_code: Optional[str] = None):
        """Clear cache for specific airport or all airports."""
        if airport_code:
            self.cache.pop(airport_code.upper(), None)
            self.cache_expiry.pop(airport_code.upper(), None)
        else:
            self.cache.clear()
            self.cache_expiry.clear()
