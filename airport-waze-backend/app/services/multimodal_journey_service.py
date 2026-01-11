"""Multi-modal journey planning service for AirportWaze."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TransportMode(Enum):
    """Transportation modes."""
    DRIVE = "drive"
    RIDESHARE = "rideshare"
    TAXI = "taxi"
    PUBLIC_TRANSIT = "public_transit"
    AIRPORT_SHUTTLE = "airport_shuttle"
    WALK = "walk"


@dataclass
class ParkingOption:
    """Airport parking option."""
    id: int
    name: str
    type: str  # economy, standard, premium, valet
    distance_to_terminal: int  # meters
    shuttle_frequency: Optional[int]  # minutes
    rate_per_hour: float
    rate_per_day: float
    available_spots: int
    total_spots: int
    amenities: List[str]
    is_covered: bool
    has_ev_charging: bool
    location: Dict[str, float]


@dataclass
class RideshareOption:
    """Rideshare service option."""
    service: str  # uber, lyft, etc.
    vehicle_type: str  # economy, comfort, xl, etc.
    estimated_price: float
    estimated_time: int  # minutes
    surge_multiplier: float
    available_now: bool
    drivers_nearby: int


@dataclass
class TransitRoute:
    """Public transit route to airport."""
    route_id: str
    service_name: str
    type: str  # train, bus, light_rail
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    transfers: int
    cost: float
    stops: List[Dict[str, Any]]
    real_time_updates: bool
    current_delay: int  # minutes


@dataclass
class MultiModalJourney:
    """Complete door-to-gate journey."""
    journey_id: str
    total_duration: int  # minutes
    total_cost: float
    recommended: bool
    carbon_footprint: float  # kg CO2
    segments: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]


class MultiModalJourneyService:
    """Service for complete door-to-gate journey planning across transport modes."""

    # Mock parking facilities
    PARKING_OPTIONS = [
        {
            "id": 1,
            "name": "Economy Lot A",
            "type": "economy",
            "distance": 1200,
            "shuttle_frequency": 10,
            "hourly_rate": 3.0,
            "daily_rate": 12.0,
            "available": 45,
            "total": 200,
            "amenities": ["shuttle", "security"],
            "covered": False,
            "ev_charging": False,
            "lat": 37.618313,
            "lng": -122.391264
        },
        {
            "id": 2,
            "name": "Premium Parking",
            "type": "premium",
            "distance": 300,
            "shuttle_frequency": None,
            "hourly_rate": 8.0,
            "daily_rate": 40.0,
            "available": 12,
            "total": 50,
            "amenities": ["covered", "security", "car_wash"],
            "covered": True,
            "ev_charging": True,
            "lat": 37.620313,
            "lng": -122.389264
        },
        {
            "id": 3,
            "name": "Valet Parking",
            "type": "valet",
            "distance": 50,
            "shuttle_frequency": None,
            "hourly_rate": 12.0,
            "daily_rate": 60.0,
            "available": 5,
            "total": 20,
            "amenities": ["valet", "covered", "security", "detailing"],
            "covered": True,
            "ev_charging": True,
            "lat": 37.621313,
            "lng": -122.390264
        }
    ]

    @staticmethod
    def find_parking(
        airport_code: str,
        arrival_time: datetime,
        departure_time: datetime,
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[ParkingOption]:
        """
        Find and recommend airport parking options.

        Args:
            airport_code: Airport code
            arrival_time: When user arrives at airport
            departure_time: When user departs
            preferences: User preferences (covered, ev_charging, max_cost, etc.)

        Returns:
            List of parking options sorted by recommendation score
        """
        logger.info(f"Finding parking at {airport_code}")

        preferences = preferences or {}
        duration_hours = (departure_time - arrival_time).total_seconds() / 3600

        results = []

        for parking in MultiModalJourneyService.PARKING_OPTIONS:
            # Calculate cost
            if duration_hours <= 24:
                cost = parking["hourly_rate"] * duration_hours
            else:
                days = int(duration_hours / 24)
                remaining_hours = duration_hours % 24
                cost = (parking["daily_rate"] * days) + (parking["hourly_rate"] * remaining_hours)

            # Apply filters
            if preferences.get("max_cost") and cost > preferences["max_cost"]:
                continue

            if preferences.get("covered") and not parking["covered"]:
                continue

            if preferences.get("ev_charging") and not parking["ev_charging"]:
                continue

            # Calculate recommendation score
            score = 100.0

            # Availability factor
            availability_ratio = parking["available"] / parking["total"]
            if availability_ratio < 0.1:
                score -= 30
            elif availability_ratio < 0.25:
                score -= 15

            # Cost factor
            if parking["type"] == "economy":
                score += 20
            elif parking["type"] == "premium":
                score += 10

            # Distance factor
            if parking["distance"] < 200:
                score += 15
            elif parking["distance"] < 500:
                score += 10
            elif parking["distance"] > 1000:
                score -= 10

            results.append(ParkingOption(
                id=parking["id"],
                name=parking["name"],
                type=parking["type"],
                distance_to_terminal=parking["distance"],
                shuttle_frequency=parking["shuttle_frequency"],
                rate_per_hour=parking["hourly_rate"],
                rate_per_day=parking["daily_rate"],
                available_spots=parking["available"],
                total_spots=parking["total"],
                amenities=parking["amenities"],
                is_covered=parking["covered"],
                has_ev_charging=parking["ev_charging"],
                location={"lat": parking["lat"], "lng": parking["lng"]}
            ))

        # Sort by recommendation score and availability
        results.sort(key=lambda x: (x.available_spots > 0, -x.distance_to_terminal))

        logger.info(f"Found {len(results)} parking options")
        return results

    @staticmethod
    def get_rideshare_options(
        pickup_location: Dict[str, float],
        airport_code: str,
        passengers: int = 1,
        luggage: int = 1
    ) -> List[RideshareOption]:
        """
        Get rideshare options to airport.

        Args:
            pickup_location: Pickup lat/lng
            airport_code: Destination airport
            passengers: Number of passengers
            luggage: Number of luggage items

        Returns:
            List of rideshare options with pricing and availability
        """
        logger.info(f"Finding rideshare to {airport_code}")

        # Mock data - would integrate with Uber/Lyft APIs
        current_hour = datetime.now().hour

        # Surge pricing during rush hours
        if 7 <= current_hour <= 9 or 16 <= current_hour <= 19:
            surge = 1.5
        else:
            surge = 1.0

        options = [
            RideshareOption(
                service="Uber",
                vehicle_type="UberX",
                estimated_price=35.0 * surge,
                estimated_time=25,
                surge_multiplier=surge,
                available_now=True,
                drivers_nearby=8
            ),
            RideshareOption(
                service="Uber",
                vehicle_type="Comfort",
                estimated_price=45.0 * surge,
                estimated_time=22,
                surge_multiplier=surge,
                available_now=True,
                drivers_nearby=5
            ),
            RideshareOption(
                service="Lyft",
                vehicle_type="Lyft",
                estimated_price=33.0 * surge,
                estimated_time=24,
                surge_multiplier=surge,
                available_now=True,
                drivers_nearby=6
            )
        ]

        # Add XL option if needed
        if passengers > 4 or luggage > 3:
            options.extend([
                RideshareOption(
                    service="Uber",
                    vehicle_type="UberXL",
                    estimated_price=55.0 * surge,
                    estimated_time=28,
                    surge_multiplier=surge,
                    available_now=True,
                    drivers_nearby=3
                ),
                RideshareOption(
                    service="Lyft",
                    vehicle_type="Lyft XL",
                    estimated_price=53.0 * surge,
                    estimated_time=27,
                    surge_multiplier=surge,
                    available_now=True,
                    drivers_nearby=2
                )
            ])

        # Sort by price
        options.sort(key=lambda x: x.estimated_price)

        return options

    @staticmethod
    def get_public_transit_options(
        origin_location: Dict[str, float],
        airport_code: str,
        desired_arrival: datetime
    ) -> List[TransitRoute]:
        """
        Get public transit routes to airport.

        Args:
            origin_location: Origin lat/lng
            airport_code: Destination airport
            desired_arrival: Desired arrival time at airport

        Returns:
            List of transit routes with schedules
        """
        logger.info(f"Finding transit to {airport_code}")

        # Mock data - would integrate with transit APIs (GTFS, etc.)
        routes = []

        # Generate some sample routes
        for i in range(3):
            departure = desired_arrival - timedelta(minutes=60 + (i * 15))
            arrival = desired_arrival - timedelta(minutes=10 + (i * 5))
            duration = int((arrival - departure).total_seconds() / 60)

            routes.append(TransitRoute(
                route_id=f"ROUTE_{i+1}",
                service_name="BART" if i == 0 else "Airport Express",
                type="train" if i == 0 else "bus",
                departure_time=departure,
                arrival_time=arrival,
                duration_minutes=duration,
                transfers=0 if i == 0 else 1,
                cost=10.0 if i == 0 else 8.0,
                stops=[
                    {
                        "name": "Origin Station",
                        "time": departure.isoformat(),
                        "lat": origin_location["lat"],
                        "lng": origin_location["lng"]
                    },
                    {
                        "name": f"{airport_code} Airport",
                        "time": arrival.isoformat(),
                        "lat": 37.621313,
                        "lng": -122.390264
                    }
                ],
                real_time_updates=True,
                current_delay=0
            ))

        return routes

    @staticmethod
    def plan_complete_journey(
        origin: Dict[str, float],
        airport_code: str,
        terminal: str,
        gate: str,
        flight_time: datetime,
        preferences: Optional[Dict[str, Any]] = None
    ) -> MultiModalJourney:
        """
        Plan complete door-to-gate journey with all segments.

        Args:
            origin: Origin location (home/office)
            airport_code: Destination airport
            terminal: Flight terminal
            gate: Flight gate
            flight_time: Flight departure time
            preferences: User preferences

        Returns:
            Complete multi-modal journey plan
        """
        logger.info(f"Planning complete journey to {airport_code} {terminal} {gate}")

        preferences = preferences or {}
        journey_id = f"journey_{datetime.now().timestamp()}"

        # Calculate required airport arrival time (2 hours before flight)
        required_airport_arrival = flight_time - timedelta(hours=2)

        # Get transport options to airport
        transport_mode = preferences.get("transport_mode", "drive")

        segments = []
        total_cost = 0.0
        total_duration = 0

        # Segment 1: Home to Airport
        if transport_mode == "drive":
            # Driving + parking
            drive_time = 30  # mock
            parking_cost = 40.0  # daily rate

            segments.append({
                "segment_number": 1,
                "type": "drive",
                "from": "Home",
                "to": f"{airport_code} Airport Parking",
                "mode": "car",
                "duration_minutes": drive_time,
                "cost": parking_cost,
                "instructions": [
                    "Drive to airport economy parking lot",
                    "Park in Lot A",
                    "Take shuttle to terminal"
                ],
                "departure_time": (required_airport_arrival - timedelta(minutes=drive_time + 15)).isoformat(),
                "arrival_time": (required_airport_arrival - timedelta(minutes=15)).isoformat()
            })

            # Shuttle to terminal
            segments.append({
                "segment_number": 2,
                "type": "shuttle",
                "from": "Parking Lot A",
                "to": f"Terminal {terminal}",
                "mode": "shuttle",
                "duration_minutes": 10,
                "cost": 0,
                "instructions": ["Board parking shuttle", "Get off at terminal"],
                "departure_time": (required_airport_arrival - timedelta(minutes=10)).isoformat(),
                "arrival_time": required_airport_arrival.isoformat()
            })

            total_cost += parking_cost
            total_duration += drive_time + 10

        elif transport_mode == "rideshare":
            # Rideshare
            ride_time = 25
            ride_cost = 35.0

            segments.append({
                "segment_number": 1,
                "type": "rideshare",
                "from": "Home",
                "to": f"Terminal {terminal}",
                "mode": "uber",
                "duration_minutes": ride_time,
                "cost": ride_cost,
                "instructions": [
                    "Request Uber to airport",
                    "Meet driver at pickup location",
                    "Direct drop-off at terminal"
                ],
                "departure_time": (required_airport_arrival - timedelta(minutes=ride_time)).isoformat(),
                "arrival_time": required_airport_arrival.isoformat()
            })

            total_cost += ride_cost
            total_duration += ride_time

        elif transport_mode == "public_transit":
            # Public transit
            transit_time = 50
            transit_cost = 10.0

            segments.append({
                "segment_number": 1,
                "type": "public_transit",
                "from": "Home",
                "to": f"{airport_code} Airport Station",
                "mode": "train",
                "duration_minutes": transit_time,
                "cost": transit_cost,
                "instructions": [
                    "Walk to nearest station",
                    "Take BART to airport",
                    "Follow signs to terminal"
                ],
                "departure_time": (required_airport_arrival - timedelta(minutes=transit_time)).isoformat(),
                "arrival_time": required_airport_arrival.isoformat()
            })

            total_cost += transit_cost
            total_duration += transit_time

        # Segment 3: Terminal to Gate (from existing journey service)
        terminal_navigation_time = 30  # security + walk to gate
        segments.append({
            "segment_number": len(segments) + 1,
            "type": "airport_navigation",
            "from": f"Terminal {terminal} Entrance",
            "to": f"Gate {gate}",
            "mode": "walk",
            "duration_minutes": terminal_navigation_time,
            "cost": 0,
            "instructions": [
                "Proceed through security checkpoint",
                "Walk to gate area",
                "Arrive at gate"
            ],
            "departure_time": required_airport_arrival.isoformat(),
            "arrival_time": (required_airport_arrival + timedelta(minutes=terminal_navigation_time)).isoformat()
        })

        total_duration += terminal_navigation_time

        # Calculate carbon footprint (simplified)
        carbon_by_mode = {
            "drive": 0.2 * 30,  # kg CO2 per km
            "rideshare": 0.15 * 30,
            "public_transit": 0.05 * 30
        }
        carbon_footprint = carbon_by_mode.get(transport_mode, 0.15 * 30)

        # Generate alternatives
        alternatives = [
            {
                "mode": "public_transit",
                "duration_minutes": 80,
                "cost": 10.0,
                "carbon_kg": 1.5,
                "pros": ["Eco-friendly", "Predictable timing", "Low cost"],
                "cons": ["Longer duration", "Less flexible"]
            },
            {
                "mode": "rideshare",
                "duration_minutes": 55,
                "cost": 35.0,
                "carbon_kg": 4.5,
                "pros": ["Door-to-door", "Comfortable", "Flexible"],
                "cons": ["Higher cost", "Surge pricing possible"]
            }
        ]

        return MultiModalJourney(
            journey_id=journey_id,
            total_duration=total_duration,
            total_cost=total_cost,
            recommended=True,
            carbon_footprint=carbon_footprint,
            segments=segments,
            alternatives=alternatives
        )

    @staticmethod
    def save_parking_location(
        user_id: int,
        airport_code: str,
        parking_lot: str,
        spot_number: str,
        photo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save parking location to help user find their car on return.

        Args:
            user_id: User ID
            airport_code: Airport code
            parking_lot: Parking lot name
            spot_number: Parking spot number
            photo_url: Optional photo of parking location

        Returns:
            Saved parking details with navigation info
        """
        logger.info(f"Saving parking location for user {user_id}")

        return {
            "user_id": user_id,
            "airport_code": airport_code,
            "parking_lot": parking_lot,
            "spot_number": spot_number,
            "photo_url": photo_url,
            "saved_at": datetime.now().isoformat(),
            "reminder_sent": False,
            "walking_directions": [
                "Exit terminal through baggage claim",
                f"Follow signs to {parking_lot}",
                "Board parking shuttle",
                f"Look for spot {spot_number}"
            ]
        }

    @staticmethod
    def coordinate_rideshare_arrival(
        user_id: int,
        flight_number: str,
        arrival_time: datetime,
        pickup_location: str = "arrivals_curb"
    ) -> Dict[str, Any]:
        """
        Coordinate rideshare pickup with flight arrival.

        Args:
            user_id: User ID
            flight_number: Arriving flight number
            arrival_time: Estimated arrival time
            pickup_location: Where to meet driver

        Returns:
            Rideshare coordination details
        """
        logger.info(f"Coordinating rideshare for {flight_number}")

        # Calculate optimal request time (when landing + deplaning + walking)
        optimal_request = arrival_time + timedelta(minutes=25)

        return {
            "user_id": user_id,
            "flight_number": flight_number,
            "arrival_time": arrival_time.isoformat(),
            "pickup_location": pickup_location,
            "optimal_request_time": optimal_request.isoformat(),
            "auto_request_enabled": False,
            "notification_enabled": True,
            "notification_time": (optimal_request - timedelta(minutes=5)).isoformat(),
            "instructions": [
                "We'll notify you when to request your ride",
                "This ensures your driver arrives when you're ready",
                "Pickup at arrivals curb - follow signs"
            ]
        }

    @staticmethod
    def optimize_multi_stop_journey(
        stops: List[Dict[str, Any]],
        airport_code: str,
        flight_time: datetime,
        optimization_goal: str = "time"  # time, cost, carbon
    ) -> Dict[str, Any]:
        """
        Optimize journey with multiple stops before airport.

        Args:
            stops: List of stops to make before airport
            airport_code: Destination airport
            flight_time: Flight departure time
            optimization_goal: What to optimize for

        Returns:
            Optimized route and schedule
        """
        logger.info(f"Optimizing journey with {len(stops)} stops")

        # Simple optimization (in production, use routing algorithms)
        total_time = 0
        total_cost = 0.0

        optimized_route = []

        for i, stop in enumerate(stops):
            segment_time = stop.get("estimated_duration", 10)
            total_time += segment_time

            optimized_route.append({
                "stop_number": i + 1,
                "location": stop["location"],
                "purpose": stop.get("purpose", "stop"),
                "duration_minutes": segment_time,
                "arrival_time": (flight_time - timedelta(minutes=120 + (len(stops) - i) * 15)).isoformat()
            })

        return {
            "total_stops": len(stops),
            "optimized_route": optimized_route,
            "total_duration_minutes": total_time,
            "total_cost": total_cost,
            "optimization_goal": optimization_goal,
            "recommended_departure": (flight_time - timedelta(minutes=120 + total_time)).isoformat()
        }
