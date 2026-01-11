"""Amenities discovery service for AirportWaze."""
import logging
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class Amenity:
    """Airport amenity (restaurant, lounge, facility)."""
    id: int
    name: str
    type: str  # restaurant, lounge, restroom, charging_station, etc.
    category: Optional[str]  # cuisine type, facility type
    location: str
    terminal: str
    lat: float
    lng: float
    distance_from_route: float
    walking_time_minutes: int
    is_on_route: bool
    current_wait_time: Optional[int]
    rating: float
    review_count: int
    price_range: Optional[str]  # $, $$, $$$, $$$$
    operating_hours: Dict[str, Any]
    is_open_now: bool
    amenities: List[str]
    dietary_options: List[str]


@dataclass
class LoungeAccess:
    """Lounge access information."""
    lounge_id: int
    lounge_name: str
    location: str
    terminal: str
    has_access: bool
    access_methods: List[str]  # priority_pass, credit_card, airline_status
    credit_cards_accepted: List[str]
    current_capacity: str  # low, medium, high
    amenities: List[str]
    operating_hours: Dict[str, Any]
    is_open_now: bool
    estimated_wait: int


class AmenitiesService:
    """Service for discovering and recommending airport amenities."""

    # Mock amenities database
    MOCK_AMENITIES = [
        {
            "id": 1,
            "name": "Trattoria Italiana",
            "type": "restaurant",
            "category": "Italian",
            "terminal": "Terminal 2",
            "location": "Near Gate 15",
            "lat": 37.621313,
            "lng": -122.390264,
            "rating": 4.5,
            "review_count": 342,
            "price_range": "$$",
            "dietary_options": ["vegetarian", "gluten_free"],
            "amenities": ["wifi", "table_service", "takeout"]
        },
        {
            "id": 2,
            "name": "Sushi Bar Express",
            "type": "restaurant",
            "category": "Japanese",
            "terminal": "Terminal 2",
            "location": "Gate Area B",
            "lat": 37.621413,
            "lng": -122.390364,
            "rating": 4.2,
            "review_count": 198,
            "price_range": "$$$",
            "dietary_options": ["pescatarian", "gluten_free"],
            "amenities": ["wifi", "quick_service", "takeout"]
        },
        {
            "id": 3,
            "name": "Green Bowl Café",
            "type": "restaurant",
            "category": "Healthy",
            "terminal": "Terminal 2",
            "location": "Security Exit",
            "lat": 37.621213,
            "lng": -122.390164,
            "rating": 4.7,
            "review_count": 523,
            "price_range": "$$",
            "dietary_options": ["vegan", "vegetarian", "gluten_free", "keto"],
            "amenities": ["wifi", "quick_service", "mobile_order"]
        },
        {
            "id": 4,
            "name": "Starbucks",
            "type": "restaurant",
            "category": "Coffee",
            "terminal": "Terminal 2",
            "location": "Gate 10",
            "lat": 37.621113,
            "lng": -122.390064,
            "rating": 4.0,
            "review_count": 1250,
            "price_range": "$$",
            "dietary_options": ["vegetarian", "vegan_options"],
            "amenities": ["wifi", "quick_service", "mobile_order", "seating"]
        }
    ]

    MOCK_LOUNGES = [
        {
            "id": 1,
            "name": "United Club",
            "terminal": "Terminal 2",
            "location": "Near Gate 20",
            "lat": 37.621513,
            "lng": -122.390464,
            "access_methods": ["priority_pass", "united_status", "credit_card"],
            "credit_cards": ["Chase Sapphire Reserve", "United Club Card"],
            "amenities": ["wifi", "showers", "food", "drinks", "workspace", "phone_booths"],
            "capacity": "medium"
        },
        {
            "id": 2,
            "name": "Priority Pass Lounge",
            "terminal": "Terminal 2",
            "location": "Central Terminal",
            "lat": 37.621613,
            "lng": -122.390564,
            "access_methods": ["priority_pass"],
            "credit_cards": ["Amex Platinum", "Chase Sapphire Reserve", "Capital One Venture X"],
            "amenities": ["wifi", "food", "drinks", "workspace"],
            "capacity": "high"
        }
    ]

    MOCK_FACILITIES = [
        {"id": 101, "type": "restroom", "name": "Restroom", "terminal": "Terminal 2", "location": "Gate 12", "lat": 37.621213, "lng": -122.390264},
        {"id": 102, "type": "charging_station", "name": "Charging Station", "terminal": "Terminal 2", "location": "Gate 15", "lat": 37.621313, "lng": -122.390364},
        {"id": 103, "type": "water_fountain", "name": "Water Fountain", "terminal": "Terminal 2", "location": "Security Exit", "lat": 37.621113, "lng": -122.390164},
        {"id": 104, "type": "family_room", "name": "Family Care Room", "terminal": "Terminal 2", "location": "Gate 8", "lat": 37.621013, "lng": -122.390064},
        {"id": 105, "type": "prayer_room", "name": "Meditation Room", "terminal": "Terminal 2", "location": "Gate 18", "lat": 37.621413, "lng": -122.390464},
    ]

    @staticmethod
    def _calculate_distance_from_route(
        amenity_lat: float,
        amenity_lng: float,
        user_lat: float,
        user_lng: float,
        gate_lat: float,
        gate_lng: float
    ) -> tuple[float, int, bool]:
        """
        Calculate if amenity is on user's route and distance/time.

        Returns:
            (distance_meters, walking_minutes, is_on_route)
        """
        # Simplified distance calculation
        # In production, use proper route calculation
        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000  # Earth radius in meters
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c

        distance = haversine(user_lat, user_lng, amenity_lat, amenity_lng)
        walking_time = int(distance / 80)  # 80 meters per minute

        # Check if on route (simplified: within 50m of direct path)
        total_route_distance = haversine(user_lat, user_lng, gate_lat, gate_lng)
        detour_distance = (
            haversine(user_lat, user_lng, amenity_lat, amenity_lng) +
            haversine(amenity_lat, amenity_lng, gate_lat, gate_lng)
        )
        is_on_route = (detour_distance - total_route_distance) < 50

        return distance, walking_time, is_on_route

    @staticmethod
    def find_restaurants(
        airport_code: str,
        terminal: str,
        user_lat: float,
        user_lng: float,
        gate_lat: float,
        gate_lng: float,
        cuisine_type: Optional[str] = None,
        dietary_restrictions: Optional[List[str]] = None,
        price_range: Optional[List[str]] = None,
        on_route_only: bool = False,
        max_walking_time: int = 15
    ) -> List[Amenity]:
        """
        Find restaurants with smart filtering and ranking.

        Args:
            airport_code: Airport code
            terminal: Terminal
            user_lat: Current user latitude
            user_lng: Current user longitude
            gate_lat: Destination gate latitude
            gate_lng: Destination gate longitude
            cuisine_type: Filter by cuisine
            dietary_restrictions: Filter by dietary options
            price_range: Filter by price (e.g., ["$", "$$"])
            on_route_only: Only show restaurants on route
            max_walking_time: Maximum walking time in minutes

        Returns:
            List of matching restaurants, sorted by relevance
        """
        logger.info(f"Finding restaurants at {airport_code} {terminal}")

        results = []
        dietary_restrictions = dietary_restrictions or []
        price_range = price_range or ["$", "$$", "$$$", "$$$$"]

        for restaurant in AmenitiesService.MOCK_AMENITIES:
            if restaurant["type"] != "restaurant":
                continue

            if restaurant["terminal"] != terminal:
                continue

            # Apply filters
            if cuisine_type and restaurant["category"] != cuisine_type:
                continue

            if restaurant["price_range"] not in price_range:
                continue

            # Check dietary restrictions
            if dietary_restrictions:
                if not any(diet in restaurant["dietary_options"] for diet in dietary_restrictions):
                    continue

            # Calculate distance and route info
            distance, walking_time, is_on_route = AmenitiesService._calculate_distance_from_route(
                restaurant["lat"], restaurant["lng"],
                user_lat, user_lng, gate_lat, gate_lng
            )

            if on_route_only and not is_on_route:
                continue

            if walking_time > max_walking_time:
                continue

            # Calculate wait time (mock)
            current_hour = datetime.now().hour
            if 11 <= current_hour <= 13 or 18 <= current_hour <= 20:
                wait_time = random.randint(10, 25)
            else:
                wait_time = random.randint(3, 10)

            results.append(Amenity(
                id=restaurant["id"],
                name=restaurant["name"],
                type=restaurant["type"],
                category=restaurant["category"],
                location=restaurant["location"],
                terminal=restaurant["terminal"],
                lat=restaurant["lat"],
                lng=restaurant["lng"],
                distance_from_route=distance,
                walking_time_minutes=walking_time,
                is_on_route=is_on_route,
                current_wait_time=wait_time,
                rating=restaurant["rating"],
                review_count=restaurant["review_count"],
                price_range=restaurant["price_range"],
                operating_hours={"open": "05:00", "close": "22:00"},
                is_open_now=True,
                amenities=restaurant["amenities"],
                dietary_options=restaurant["dietary_options"]
            ))

        # Sort by relevance: on_route first, then by rating, then by distance
        results.sort(key=lambda x: (
            not x.is_on_route,
            -x.rating,
            x.walking_time_minutes
        ))

        logger.info(f"Found {len(results)} restaurants")
        return results

    @staticmethod
    def check_lounge_access(
        user_id: int,
        airport_code: str,
        terminal: str,
        credit_cards: Optional[List[str]] = None,
        airline_status: Optional[str] = None,
        has_priority_pass: bool = False
    ) -> List[LoungeAccess]:
        """
        Check which lounges user can access.

        Args:
            user_id: User ID
            airport_code: Airport code
            terminal: Terminal
            credit_cards: List of user's credit cards
            airline_status: Airline loyalty status
            has_priority_pass: Whether user has Priority Pass

        Returns:
            List of accessible lounges
        """
        logger.info(f"Checking lounge access for user {user_id}")

        credit_cards = credit_cards or []
        results = []

        for lounge in AmenitiesService.MOCK_LOUNGES:
            if lounge["terminal"] != terminal:
                continue

            has_access = False
            access_methods = []

            # Check Priority Pass
            if has_priority_pass and "priority_pass" in lounge["access_methods"]:
                has_access = True
                access_methods.append("Priority Pass")

            # Check credit cards
            for card in credit_cards:
                if card in lounge["credit_cards"]:
                    has_access = True
                    access_methods.append(f"Credit Card ({card})")

            # Check airline status
            if airline_status and f"{airline_status}_status" in lounge["access_methods"]:
                has_access = True
                access_methods.append(f"Airline Status ({airline_status})")

            # Calculate wait time based on capacity
            capacity_wait = {
                "low": 0,
                "medium": random.randint(5, 10),
                "high": random.randint(15, 30)
            }

            results.append(LoungeAccess(
                lounge_id=lounge["id"],
                lounge_name=lounge["name"],
                location=lounge["location"],
                terminal=lounge["terminal"],
                has_access=has_access,
                access_methods=access_methods,
                credit_cards_accepted=lounge["credit_cards"],
                current_capacity=lounge["capacity"],
                amenities=lounge["amenities"],
                operating_hours={"open": "05:00", "close": "22:00"},
                is_open_now=True,
                estimated_wait=capacity_wait.get(lounge["capacity"], 0)
            ))

        # Sort by access (accessible first), then by capacity
        results.sort(key=lambda x: (not x.has_access, x.estimated_wait))

        logger.info(f"Found {len([r for r in results if r.has_access])} accessible lounges")
        return results

    @staticmethod
    def find_facilities(
        airport_code: str,
        terminal: str,
        facility_types: Optional[List[str]] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        max_distance: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Find airport facilities (restrooms, charging stations, etc.).

        Args:
            airport_code: Airport code
            terminal: Terminal
            facility_types: Types to filter (restroom, charging_station, etc.)
            user_lat: User latitude for distance calculation
            user_lng: User longitude for distance calculation
            max_distance: Maximum distance in meters

        Returns:
            List of facilities
        """
        logger.info(f"Finding facilities at {airport_code} {terminal}")

        facility_types = facility_types or [
            "restroom", "charging_station", "water_fountain",
            "family_room", "prayer_room"
        ]

        results = []

        for facility in AmenitiesService.MOCK_FACILITIES:
            if facility["terminal"] != terminal:
                continue

            if facility["type"] not in facility_types:
                continue

            # Calculate distance if user location provided
            distance = None
            if user_lat and user_lng:
                from math import radians, cos, sin, asin, sqrt
                R = 6371000
                lat1, lon1, lat2, lon2 = map(
                    radians,
                    [user_lat, user_lng, facility["lat"], facility["lng"]]
                )
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                distance = R * c

                if distance > max_distance:
                    continue

            results.append({
                "id": facility["id"],
                "type": facility["type"],
                "name": facility["name"],
                "terminal": facility["terminal"],
                "location": facility["location"],
                "lat": facility["lat"],
                "lng": facility["lng"],
                "distance_meters": distance,
                "walking_time_minutes": int(distance / 80) if distance else None
            })

        # Sort by distance if location provided
        if user_lat and user_lng:
            results.sort(key=lambda x: x["distance_meters"] or float('inf'))

        logger.info(f"Found {len(results)} facilities")
        return results

    @staticmethod
    def get_amenity_reviews(amenity_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get reviews and ratings for an amenity.

        Args:
            amenity_id: Amenity ID
            limit: Maximum reviews to return

        Returns:
            List of reviews
        """
        # Mock reviews
        mock_reviews = [
            {
                "id": 1,
                "user_name": "John D.",
                "rating": 5,
                "comment": "Great food and quick service!",
                "created_at": datetime.now().isoformat(),
                "helpful_count": 12
            },
            {
                "id": 2,
                "user_name": "Sarah M.",
                "rating": 4,
                "comment": "Good options but a bit pricey.",
                "created_at": datetime.now().isoformat(),
                "helpful_count": 8
            }
        ]

        return mock_reviews[:limit]
