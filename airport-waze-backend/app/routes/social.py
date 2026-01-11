"""Social features routes for AirportWaze."""
import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

from app.services.social_service import SocialService
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["social"])


# Request/Response Models
class TravelBuddyRequest(BaseModel):
    """Request for finding travel buddies."""
    user_id: int
    flight_number: Optional[str] = None
    airport_code: Optional[str] = None
    departure_time: Optional[str] = None
    interests: Optional[List[str]] = Field(default_factory=list)
    min_match_score: float = Field(default=0.6, ge=0.0, le=1.0)


class SharedJourneyRequest(BaseModel):
    """Request to create shared journey."""
    creator_id: int
    member_ids: List[int]
    meeting_point: str
    meeting_time: Optional[str] = None


class FriendInviteRequest(BaseModel):
    """Request to send friend invite."""
    from_user_id: int
    to_user_id: int
    message: Optional[str] = None


class PrivacySettingsRequest(BaseModel):
    """Request to update privacy settings."""
    user_id: int
    share_location: bool = True
    share_flight_info: bool = False
    allow_buddy_requests: bool = True
    visible_to: str = Field(default="verified_only", pattern="^(all|verified_only|friends_only)$")


class CheckpointPhotoRequest(BaseModel):
    """Request to share checkpoint photo."""
    user_id: int
    checkpoint_id: int
    image_url: str
    caption: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


@router.post("/travel-buddies/find")
@limiter.limit("30/minute")
async def find_travel_buddies(
    request: Request,
    buddy_request: TravelBuddyRequest
):
    """
    Find potential travel buddies based on matching criteria.

    Matches users based on:
    - Same flight (highest priority)
    - Similar travel time window
    - Shared interests
    - Past positive interactions
    - Common airports visited

    Returns list of matches sorted by compatibility score.
    """
    try:
        departure_time = None
        if buddy_request.departure_time:
            try:
                departure_time = datetime.fromisoformat(
                    buddy_request.departure_time.replace('Z', '+00:00')
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid departure_time format. Use ISO format."
                )

        matches = SocialService.find_travel_buddies(
            user_id=buddy_request.user_id,
            flight_number=buddy_request.flight_number,
            airport_code=buddy_request.airport_code,
            departure_time=departure_time,
            user_interests=buddy_request.interests,
            min_match_score=buddy_request.min_match_score
        )

        return {
            "matches": [
                {
                    "user_id": m.user_id,
                    "name": m.name,
                    "avatar_url": m.avatar_url,
                    "match_score": round(m.match_score, 2),
                    "flight_number": m.flight_number,
                    "shared_interests": m.shared_interests,
                    "common_airports": m.common_airports,
                    "past_interactions": m.past_interactions,
                    "verification_status": m.verification_status,
                    "current_location": m.current_location,
                    "eta_to_gate": m.eta_to_gate
                }
                for m in matches
            ],
            "total_matches": len(matches)
        }

    except ValueError as e:
        logger.warning(f"Invalid buddy request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error finding travel buddies: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to find travel buddies"
        )


@router.post("/shared-journey/create")
@limiter.limit("20/minute")
async def create_shared_journey(
    request: Request,
    journey_request: SharedJourneyRequest
):
    """
    Create a shared journey for group navigation.

    Allows coordinating with friends/travel buddies by:
    - Setting a meeting point
    - Tracking everyone's progress
    - Sending alerts if someone is delayed
    """
    try:
        meeting_time = None
        if journey_request.meeting_time:
            try:
                meeting_time = datetime.fromisoformat(
                    journey_request.meeting_time.replace('Z', '+00:00')
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid meeting_time format. Use ISO format."
                )

        journey = SocialService.create_shared_journey(
            creator_id=journey_request.creator_id,
            member_ids=journey_request.member_ids,
            meeting_point=journey_request.meeting_point,
            meeting_time=meeting_time
        )

        return journey

    except Exception as e:
        logger.error(f"Error creating shared journey: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create shared journey"
        )


@router.get("/shared-journey/{journey_id}/progress")
@limiter.limit("60/minute")
async def get_group_progress(
    request: Request,
    journey_id: str
):
    """
    Get real-time progress of all group members.

    Shows:
    - Each member's current location
    - Progress percentage to meeting point
    - Who's delayed
    - Average group progress
    """
    try:
        progress = SocialService.get_group_progress(journey_id)
        return progress

    except Exception as e:
        logger.error(f"Error getting group progress: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get group progress"
        )


@router.get("/feed")
@limiter.limit("100/minute")
async def get_social_feed(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    airport_code: Optional[str] = Query(None, description="Filter by airport"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get social feed with travel updates, tips, and photos.

    Feed includes:
    - Real-time tips (e.g., "Security line B is shorter")
    - Community recommendations
    - Checkpoint photos
    - Travel updates from friends
    """
    try:
        posts = SocialService.get_social_feed(
            user_id=user_id,
            airport_code=airport_code,
            limit=limit,
            offset=offset
        )

        return {
            "posts": posts,
            "total": len(posts),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error getting social feed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get social feed"
        )


@router.post("/friends/invite")
@limiter.limit("10/minute")
async def send_friend_invite(
    request: Request,
    invite_request: FriendInviteRequest
):
    """
    Send a friend request to another user.

    Friend system features:
    - Personal invitations
    - See friends' travel plans (with permission)
    - Coordinate meetups at airports
    """
    try:
        if invite_request.from_user_id == invite_request.to_user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot send friend invite to yourself"
            )

        invite = SocialService.send_friend_invite(
            from_user_id=invite_request.from_user_id,
            to_user_id=invite_request.to_user_id,
            message=invite_request.message
        )

        return invite

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending friend invite: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send friend invite"
        )


@router.put("/privacy/settings")
@limiter.limit("10/minute")
async def update_privacy_settings(
    request: Request,
    settings: PrivacySettingsRequest
):
    """
    Update privacy settings for social features.

    Control:
    - Location sharing (opt-in)
    - Flight information visibility
    - Who can send buddy requests
    - Profile visibility level

    Safety first: All sharing is opt-in, only verified users by default.
    """
    try:
        updated_settings = SocialService.update_privacy_settings(
            user_id=settings.user_id,
            share_location=settings.share_location,
            share_flight_info=settings.share_flight_info,
            allow_buddy_requests=settings.allow_buddy_requests,
            visible_to=settings.visible_to
        )

        return updated_settings

    except Exception as e:
        logger.error(f"Error updating privacy settings: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update privacy settings"
        )


@router.post("/photos/checkpoint")
@limiter.limit("20/minute")
async def share_checkpoint_photo(
    request: Request,
    photo_request: CheckpointPhotoRequest
):
    """
    Share a photo at a checkpoint.

    Build community by:
    - Sharing experiences at different checkpoints
    - Helping others visualize locations
    - Creating travel memories
    """
    try:
        photo_post = SocialService.create_checkpoint_photo(
            user_id=photo_request.user_id,
            checkpoint_id=photo_request.checkpoint_id,
            image_url=photo_request.image_url,
            caption=photo_request.caption,
            tags=photo_request.tags
        )

        return photo_post

    except Exception as e:
        logger.error(f"Error sharing checkpoint photo: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to share checkpoint photo"
        )
