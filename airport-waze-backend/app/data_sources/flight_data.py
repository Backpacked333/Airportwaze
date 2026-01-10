"""
Flight Data API Integration for Demand Forecasting.

Supported providers:
1. Aviation Edge (freemium) - https://aviation-edge.com/
2. FlightAware (paid) - https://flightaware.com/
3. AeroDataBox (freemium) - https://www.aerodatabox.com/

For MVP, we provide a generic interface that can work with any provider.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging
import os

logger = logging.getLogger(__name__)


class FlightDataAPI:
    """
    Generic flight data API client.
    Configure with environment variables:
    - FLIGHT_API_PROVIDER: 'aviation_edge', 'flightaware', 'aerodatabox', or 'none'
    - FLIGHT_API_KEY: API key for the provider
    """

    def __init__(self):
        self.provider = os.getenv("FLIGHT_API_PROVIDER", "none").lower()
        self.api_key = os.getenv("FLIGHT_API_KEY", "")

        self.cache: Dict[str, List[Dict]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_ttl_minutes = 30

        # Aircraft capacity estimates (for passenger load calculation)
        self.aircraft_capacities = {
            # Narrow-body
            "A320": 180, "A20N": 180, "A319": 156, "A321": 220, "A21N": 244,
            "B737": 189, "B738": 189, "B739": 215, "B37M": 178, "B38M": 178,
            "E170": 78, "E175": 88, "E190": 114, "E195": 124,
            # Wide-body
            "A330": 293, "A333": 293, "A339": 310, "A350": 366, "A359": 366,
            "B767": 269, "B763": 269, "B777": 396, "B77W": 396, "B788": 242, "B789": 296,
            "B747": 467, "B748": 467,
            "A380": 555,
            # Regional
            "CRJ": 76, "CRJ7": 76, "CRJ9": 90, "DH8D": 78,
        }

    async def get_departures(
        self,
        airport_code: str,
        hours_ahead: int = 4
    ) -> List[Dict]:
        """
        Get upcoming departures for demand forecasting.

        Args:
            airport_code: IATA airport code
            hours_ahead: How many hours ahead to fetch

        Returns:
            List of flight dicts with departure info and passenger estimates
        """
        if self.provider == "none":
            logger.warning("No flight data provider configured. Using empty flight list.")
            return []

        airport_code = airport_code.upper()

        # Check cache
        cache_key = f"{airport_code}_{hours_ahead}"
        if cache_key in self.cache:
            if datetime.utcnow() < self.cache_expiry[cache_key]:
                logger.debug(f"Flight data cache hit for {airport_code}")
                return self.cache[cache_key]

        try:
            if self.provider == "aviation_edge":
                flights = await self._fetch_aviation_edge(airport_code, hours_ahead)
            elif self.provider == "aerodatabox":
                flights = await self._fetch_aerodatabox(airport_code, hours_ahead)
            elif self.provider == "flightaware":
                flights = await self._fetch_flightaware(airport_code, hours_ahead)
            else:
                logger.warning(f"Unknown flight provider: {self.provider}")
                return []

            # Cache result
            if flights:
                self.cache[cache_key] = flights
                self.cache_expiry[cache_key] = datetime.utcnow() + timedelta(
                    minutes=self.cache_ttl_minutes
                )
                logger.info(f"Cached {len(flights)} flights for {airport_code}")

            return flights

        except Exception as e:
            logger.error(f"Flight data API error: {e}")
            return []

    async def _fetch_aviation_edge(
        self,
        airport_code: str,
        hours_ahead: int
    ) -> List[Dict]:
        """Fetch from Aviation Edge API."""
        if not self.api_key:
            logger.error("FLIGHT_API_KEY not configured for Aviation Edge")
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = "https://aviation-edge.com/v2/public/timetable"
                params = {
                    "key": self.api_key,
                    "iataCode": airport_code,
                    "type": "departure"
                }
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    logger.error(f"Aviation Edge API returned {response.status_code}")
                    return []

                data = response.json()

                # Parse and filter to next N hours
                now = datetime.utcnow()
                cutoff = now + timedelta(hours=hours_ahead)
                flights = []

                for flight in data:
                    try:
                        # Parse departure time
                        departure_str = flight.get("departure", {}).get("scheduledTime", "")
                        departure_time = datetime.fromisoformat(departure_str.replace("Z", "+00:00"))

                        if departure_time.tzinfo:
                            departure_time = departure_time.replace(tzinfo=None)

                        # Filter to time window
                        if not (now <= departure_time <= cutoff):
                            continue

                        aircraft_code = flight.get("aircraft", {}).get("iataCode", "")
                        estimated_passengers = self._estimate_passengers(aircraft_code)

                        flights.append({
                            "flight_number": flight.get("flight", {}).get("iataNumber", ""),
                            "airline": flight.get("airline", {}).get("iataCode", ""),
                            "departure_time": departure_time.isoformat(),
                            "terminal": flight.get("departure", {}).get("terminal"),
                            "gate": flight.get("departure", {}).get("gate"),
                            "aircraft_type": aircraft_code,
                            "estimated_passengers": estimated_passengers,
                            "status": flight.get("status", ""),
                        })

                    except Exception as e:
                        logger.warning(f"Error parsing flight: {e}")
                        continue

                return flights

        except Exception as e:
            logger.error(f"Aviation Edge fetch error: {e}")
            return []

    async def _fetch_aerodatabox(
        self,
        airport_code: str,
        hours_ahead: int
    ) -> List[Dict]:
        """Fetch from AeroDataBox API."""
        if not self.api_key:
            logger.error("FLIGHT_API_KEY not configured for AeroDataBox")
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                now = datetime.utcnow()
                from_time = now.isoformat()
                to_time = (now + timedelta(hours=hours_ahead)).isoformat()

                url = f"https://aerodatabox.p.rapidapi.com/flights/airports/iata/{airport_code}/{from_time}/{to_time}"
                headers = {
                    "X-RapidAPI-Key": self.api_key,
                    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
                }
                params = {
                    "withLeg": "true",
                    "direction": "Departure",
                    "withCancelled": "false"
                }

                response = await client.get(url, headers=headers, params=params)

                if response.status_code != 200:
                    logger.error(f"AeroDataBox API returned {response.status_code}")
                    return []

                data = response.json()
                flights = []

                for flight in data.get("departures", []):
                    try:
                        departure_str = flight.get("departure", {}).get("scheduledTime", {}).get("utc", "")
                        departure_time = datetime.fromisoformat(departure_str.replace("Z", ""))

                        aircraft_code = flight.get("aircraft", {}).get("model", {}).get("code", "")
                        estimated_passengers = self._estimate_passengers(aircraft_code)

                        flights.append({
                            "flight_number": flight.get("number", ""),
                            "airline": flight.get("airline", {}).get("iata", ""),
                            "departure_time": departure_time.isoformat(),
                            "terminal": flight.get("departure", {}).get("terminal"),
                            "gate": flight.get("departure", {}).get("gate"),
                            "aircraft_type": aircraft_code,
                            "estimated_passengers": estimated_passengers,
                            "status": flight.get("status", ""),
                        })

                    except Exception as e:
                        logger.warning(f"Error parsing flight: {e}")
                        continue

                return flights

        except Exception as e:
            logger.error(f"AeroDataBox fetch error: {e}")
            return []

    async def _fetch_flightaware(
        self,
        airport_code: str,
        hours_ahead: int
    ) -> List[Dict]:
        """Fetch from FlightAware API."""
        if not self.api_key:
            logger.error("FLIGHT_API_KEY not configured for FlightAware")
            return []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"https://aeroapi.flightaware.com/aeroapi/airports/{airport_code}/flights/departures"
                headers = {
                    "x-apikey": self.api_key
                }
                params = {
                    "type": "Scheduled",
                    "max_pages": 1
                }

                response = await client.get(url, headers=headers, params=params)

                if response.status_code != 200:
                    logger.error(f"FlightAware API returned {response.status_code}")
                    return []

                data = response.json()
                flights = []

                now = datetime.utcnow()
                cutoff = now + timedelta(hours=hours_ahead)

                for flight in data.get("scheduled_departures", []):
                    try:
                        departure_str = flight.get("scheduled_out", "")
                        departure_time = datetime.fromisoformat(departure_str.replace("Z", ""))

                        if not (now <= departure_time <= cutoff):
                            continue

                        aircraft_code = flight.get("aircraft_type", "")
                        estimated_passengers = self._estimate_passengers(aircraft_code)

                        flights.append({
                            "flight_number": flight.get("ident", ""),
                            "airline": flight.get("operator_iata", ""),
                            "departure_time": departure_time.isoformat(),
                            "terminal": flight.get("terminal", ""),
                            "gate": flight.get("gate_origin", ""),
                            "aircraft_type": aircraft_code,
                            "estimated_passengers": estimated_passengers,
                            "status": "",
                        })

                    except Exception as e:
                        logger.warning(f"Error parsing flight: {e}")
                        continue

                return flights

        except Exception as e:
            logger.error(f"FlightAware fetch error: {e}")
            return []

    def _estimate_passengers(self, aircraft_code: str, load_factor: float = 0.80) -> int:
        """
        Estimate number of passengers based on aircraft type and load factor.

        Args:
            aircraft_code: IATA or ICAO aircraft code
            load_factor: Expected load factor (0-1), default 80%

        Returns:
            Estimated number of passengers
        """
        # Normalize aircraft code (remove model suffixes)
        normalized_code = aircraft_code[:4].upper() if len(aircraft_code) >= 4 else aircraft_code.upper()

        # Try exact match
        capacity = self.aircraft_capacities.get(normalized_code)

        # Try prefix match
        if not capacity:
            for code, cap in self.aircraft_capacities.items():
                if normalized_code.startswith(code) or code.startswith(normalized_code):
                    capacity = cap
                    break

        # Default to average single-aisle capacity
        if not capacity:
            capacity = 180

        return int(capacity * load_factor)

    def clear_cache(self, airport_code: Optional[str] = None):
        """Clear flight data cache."""
        if airport_code:
            cache_keys = [k for k in self.cache.keys() if k.startswith(airport_code.upper())]
            for key in cache_keys:
                self.cache.pop(key, None)
                self.cache_expiry.pop(key, None)
        else:
            self.cache.clear()
            self.cache_expiry.clear()
