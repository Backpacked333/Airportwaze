"""Amenities discovery routes for AirportWaze."""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

from app.services.amenities_service import AmenitiesService
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/amenities", tags=["amenities"])


# Request/Response Models
class RestaurantSearchRequest(BaseModel):
    """Request for restaurant search."""
    airport_code: str
    terminal: str
    user_lat: float = Field(..., ge=-90, le=90)
    user_lng: float = Field(..., ge=-180, le=180)
    gate_lat: float = Field(..., ge=-90, le=90)
    gate_lng: float = Field(..., ge=-180, le=180)
    cuisine_type: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    price_range: Optional[List[str]] = Field(default_factory=lambda: ["$", "$$", "$$$", "$$$$"])
    on_route_only: bool = False
    max_walking_time: int = Field(default=15, ge=1, le=30)


class LoungeAccessRequest(BaseModel):
    """Request for lounge access check."""
    user_id: int
    airport_code: str
    terminal: str
    credit_cards: Optional[List[str]] = Field(default_factory=list)
    airline_status: Optional[str] = None
    has_priority_pass: bool = False


class FacilitySearchRequest(BaseModel):
    """Request for facility search."""
    airport_code: str
    terminal: str
    facility_types: Optional[List[str]] = Field(
        default_factory=lambda: [
            "restroom", "charging_station", "water_fountain",
            "family_room", "prayer_room"
        ]
    )
    user_lat: Optional[float] = Field(None, ge=-90, le=90)
    user_lng: Optional[float] = Field(None, ge=-180, le=180)
    max_distance: int = Field(default=500, ge=50, le=2000)


@router.post("/restaurants/search")
@limiter.limit("60/minute")
async def search_restaurants(
    request: Request,
    search_request: RestaurantSearchRequest
):
    """
    Search for restaurants with smart recommendations.

    Features:
    - Filter by cuisine type and dietary restrictions
    - Show "on your route" options first
    - Wait time predictions
    - Reviews and ratings
    - Price range filtering

    Perfect for finding a quick bite that won't make you late!
    """
    try:
        restaurants = AmenitiesService.find_restaurants(
            airport_code=search_request.airport_code,
            terminal=search_request.terminal,
            user_lat=search_request.user_lat,
            user_lng=search_request.user_lng,
            gate_lat=search_request.gate_lat,
            gate_lng=search_request.gate_lng,
            cuisine_type=search_request.cuisine_type,
            dietary_restrictions=search_request.dietary_restrictions,
            price_range=search_request.price_range,
            on_route_only=search_request.on_route_only,
            max_walking_time=search_request.max_walking_time
        )

        return {
            "restaurants": [
                {
                    "id": r.id,
                    "name": r.name,
                    "type": r.type,
                    "category": r.category,
                    "location": r.location,
                    "terminal": r.terminal,
                    "position": {"lat": r.lat, "lng": r.lng},
                    "distance_from_route": round(r.distance_from_route, 1),
                    "walking_time_minutes": r.walking_time_minutes,
                    "is_on_route": r.is_on_route,
                    "current_wait_time": r.current_wait_time,
                    "rating": r.rating,
                    "review_count": r.review_count,
                    "price_range": r.price_range,
                    "operating_hours": r.operating_hours,
                    "is_open_now": r.is_open_now,
                    "amenities": r.amenities,
                    "dietary_options": r.dietary_options
                }
                for r in restaurants
            ],
            "total": len(restaurants),
            "filters_applied": {
                "cuisine_type": search_request.cuisine_type,
                "dietary_restrictions": search_request.dietary_restrictions,
                "price_range": search_request.price_range,
                "on_route_only": search_request.on_route_only,
                "max_walking_time": search_request.max_walking_time
            }
        }

    except ValueError as e:
        logger.warning(f"Invalid restaurant search: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching restaurants: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search restaurants"
        )


@router.post("/lounges/check-access")
@limiter.limit("30/minute")
async def check_lounge_access(
    request: Request,
    access_request: LoungeAccessRequest
):
    """
    Check which airport lounges you can access.

    Checks access via:
    - Priority Pass membership
    - Credit cards (Amex Platinum, Chase Sapphire Reserve, etc.)
    - Airline loyalty status
    - One-time pass purchase

    Shows real-time capacity and wait times.
    """
    try:
        lounges = AmenitiesService.check_lounge_access(
            user_id=access_request.user_id,
            airport_code=access_request.airport_code,
            terminal=access_request.terminal,
            credit_cards=access_request.credit_cards,
            airline_status=access_request.airline_status,
            has_priority_pass=access_request.has_priority_pass
        )

        accessible_lounges = [l for l in lounges if l.has_access]
        other_lounges = [l for l in lounges if not l.has_access]

        return {
            "accessible_lounges": [
                {
                    "lounge_id": l.lounge_id,
                    "lounge_name": l.lounge_name,
                    "location": l.location,
                    "terminal": l.terminal,
                    "access_methods": l.access_methods,
                    "current_capacity": l.current_capacity,
                    "amenities": l.amenities,
                    "operating_hours": l.operating_hours,
                    "is_open_now": l.is_open_now,
                    "estimated_wait": l.estimated_wait
                }
                for l in accessible_lounges
            ],
            "other_lounges": [
                {
                    "lounge_id": l.lounge_id,
                    "lounge_name": l.lounge_name,
                    "location": l.location,
                    "terminal": l.terminal,
                    "credit_cards_accepted": l.credit_cards_accepted,
                    "amenities": l.amenities
                }
                for l in other_lounges
            ],
            "total_accessible": len(accessible_lounges),
            "total_lounges": len(lounges)
        }

    except Exception as e:
        logger.error(f"Error checking lounge access: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check lounge access"
        )


@router.post("/facilities/search")
@limiter.limit("100/minute")
async def search_facilities(
    request: Request,
    search_request: FacilitySearchRequest
):
    """
    Find airport facilities near you.

    Locate:
    - Restrooms
    - Water fountains
    - Charging stations
    - Family care rooms
    - Prayer/meditation rooms
    - Pet relief areas

    Shows distance and walking time from your location.
    """
    try:
        facilities = AmenitiesService.find_facilities(
            airport_code=search_request.airport_code,
            terminal=search_request.terminal,
            facility_types=search_request.facility_types,
            user_lat=search_request.user_lat,
            user_lng=search_request.user_lng,
            max_distance=search_request.max_distance
        )

        return {
            "facilities": facilities,
            "total": len(facilities),
            "filters": {
                "facility_types": search_request.facility_types,
                "max_distance": search_request.max_distance
            }
        }

    except Exception as e:
        logger.error(f"Error searching facilities: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search facilities"
        )


@router.get("/restaurants/{amenity_id}/reviews")
@limiter.limit("60/minute")
async def get_amenity_reviews(
    request: Request,
    amenity_id: int,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get reviews and ratings for a restaurant or amenity.

    Reviews include:
    - User ratings
    - Comments
    - Helpful votes
    - Recent experiences
    """
    try:
        reviews = AmenitiesService.get_amenity_reviews(
            amenity_id=amenity_id,
            limit=limit
        )

        return {
            "amenity_id": amenity_id,
            "reviews": reviews,
            "total": len(reviews)
        }

    except Exception as e:
        logger.error(f"Error getting amenity reviews: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get amenity reviews"
        )


@router.get("/restaurants/cuisines")
@limiter.limit("100/minute")
async def get_available_cuisines(
    request: Request,
    airport_code: str = Query(..., description="Airport code"),
    terminal: Optional[str] = Query(None, description="Filter by terminal")
):
    """
    Get list of available cuisine types at the airport.

    Helps users discover food options before searching.
    """
    try:
        # In production, this would query the database
        cuisines = [
            {"type": "Italian", "restaurant_count": 3},
            {"type": "Japanese", "restaurant_count": 2},
            {"type": "American", "restaurant_count": 5},
            {"type": "Mexican", "restaurant_count": 2},
            {"type": "Healthy", "restaurant_count": 4},
            {"type": "Coffee", "restaurant_count": 6},
            {"type": "Fast Food", "restaurant_count": 8}
        ]

        return {
            "airport_code": airport_code,
            "terminal": terminal,
            "cuisines": cuisines
        }

    except Exception as e:
        logger.error(f"Error getting cuisines: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get available cuisines"
        )


@router.get("/dietary-options")
@limiter.limit("100/minute")
async def get_dietary_options(request: Request):
    """
    Get list of supported dietary restriction filters.

    Helps users with specific dietary needs find suitable options.
    """
    try:
        options = [
            {"id": "vegetarian", "name": "Vegetarian", "description": "No meat"},
            {"id": "vegan", "name": "Vegan", "description": "No animal products"},
            {"id": "gluten_free", "name": "Gluten-Free", "description": "No gluten"},
            {"id": "keto", "name": "Keto", "description": "Low-carb, high-fat"},
            {"id": "halal", "name": "Halal", "description": "Islamic dietary laws"},
            {"id": "kosher", "name": "Kosher", "description": "Jewish dietary laws"},
            {"id": "pescatarian", "name": "Pescatarian", "description": "Fish but no meat"},
            {"id": "dairy_free", "name": "Dairy-Free", "description": "No dairy products"}
        ]

        return {"dietary_options": options}

    except Exception as e:
        logger.error(f"Error getting dietary options: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get dietary options"
        )
