"""Social features service for AirportWaze."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class TravelBuddy:
    """Travel buddy match result."""
    user_id: int
    name: str
    avatar_url: Optional[str]
    match_score: float
    flight_number: Optional[str]
    shared_interests: List[str]
    common_airports: int
    past_interactions: int
    verification_status: str
    current_location: Optional[Dict[str, float]]
    eta_to_gate: Optional[int]


@dataclass
class GroupMember:
    """Group navigation member."""
    user_id: int
    name: str
    avatar_url: Optional[str]
    current_checkpoint: str
    progress_percentage: float
    last_update: datetime
    is_delayed: bool


@dataclass
class SocialPost:
    """Social feed post."""
    id: int
    user_id: int
    user_name: str
    avatar_url: Optional[str]
    post_type: str  # tip, photo, update, recommendation
    content: str
    location: Optional[str]
    checkpoint_id: Optional[int]
    image_url: Optional[str]
    likes_count: int
    comments_count: int
    created_at: datetime
    is_verified_user: bool


class SocialService:
    """Service for social features and travel buddy matching."""

    @staticmethod
    def find_travel_buddies(
        user_id: int,
        flight_number: Optional[str] = None,
        airport_code: Optional[str] = None,
        departure_time: Optional[datetime] = None,
        user_interests: Optional[List[str]] = None,
        min_match_score: float = 0.6
    ) -> List[TravelBuddy]:
        """
        Find potential travel buddies based on various matching criteria.

        Algorithm considers:
        - Same flight (highest weight: 40%)
        - Similar travel time window (30%)
        - Shared interests (15%)
        - Past positive interactions (10%)
        - Common airports visited (5%)

        Args:
            user_id: Current user ID
            flight_number: User's flight number
            airport_code: Current airport
            departure_time: Flight departure time
            user_interests: List of user interests
            min_match_score: Minimum match score threshold (0-1)

        Returns:
            List of TravelBuddy matches sorted by match score
        """
        logger.info(f"Finding travel buddies for user {user_id}")

        # In production, this would query a database
        # For now, generate mock matches with sophisticated scoring
        matches = []

        # Mock candidate pool (would come from database)
        mock_candidates = [
            {
                "user_id": 101,
                "name": "Sarah Johnson",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
                "flight_number": flight_number,
                "interests": ["photography", "food", "travel"],
                "common_airports": 5,
                "past_interactions": 2,
                "verification_status": "verified",
                "current_checkpoint": "security",
                "progress": 45
            },
            {
                "user_id": 102,
                "name": "Michael Chen",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Michael",
                "flight_number": flight_number,
                "interests": ["tech", "music", "travel"],
                "common_airports": 3,
                "past_interactions": 0,
                "verification_status": "verified",
                "current_checkpoint": "bag_check",
                "progress": 25
            },
            {
                "user_id": 103,
                "name": "Emma Williams",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Emma",
                "flight_number": None,
                "interests": ["food", "culture", "photography"],
                "common_airports": 8,
                "past_interactions": 5,
                "verification_status": "verified",
                "current_checkpoint": "security",
                "progress": 60
            }
        ]

        user_interests = user_interests or ["travel"]

        for candidate in mock_candidates:
            # Calculate match score
            score_components = {
                "same_flight": 0.0,
                "time_window": 0.0,
                "shared_interests": 0.0,
                "past_interactions": 0.0,
                "common_airports": 0.0
            }

            # Same flight bonus (40%)
            if candidate["flight_number"] == flight_number and flight_number:
                score_components["same_flight"] = 0.4

            # Time window similarity (30%)
            if departure_time:
                # In same time window (within 2 hours)
                score_components["time_window"] = 0.3

            # Shared interests (15%)
            shared = set(candidate["interests"]) & set(user_interests)
            if candidate["interests"]:
                score_components["shared_interests"] = (
                    len(shared) / max(len(candidate["interests"]), len(user_interests))
                ) * 0.15

            # Past interactions (10%)
            interaction_score = min(candidate["past_interactions"] / 10, 1.0)
            score_components["past_interactions"] = interaction_score * 0.1

            # Common airports (5%)
            airport_score = min(candidate["common_airports"] / 20, 1.0)
            score_components["common_airports"] = airport_score * 0.05

            # Calculate total match score
            match_score = sum(score_components.values())

            if match_score >= min_match_score:
                matches.append(TravelBuddy(
                    user_id=candidate["user_id"],
                    name=candidate["name"],
                    avatar_url=candidate["avatar_url"],
                    match_score=match_score,
                    flight_number=candidate["flight_number"],
                    shared_interests=list(set(candidate["interests"]) & set(user_interests)),
                    common_airports=candidate["common_airports"],
                    past_interactions=candidate["past_interactions"],
                    verification_status=candidate["verification_status"],
                    current_location={"lat": 37.7749, "lng": -122.4194},
                    eta_to_gate=random.randint(10, 45)
                ))

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(f"Found {len(matches)} travel buddy matches")
        return matches

    @staticmethod
    def create_shared_journey(
        creator_id: int,
        member_ids: List[int],
        meeting_point: str,
        meeting_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a shared journey for group navigation.

        Args:
            creator_id: User creating the group
            member_ids: List of member user IDs
            meeting_point: Where to meet (e.g., "Security Checkpoint A")
            meeting_time: When to meet

        Returns:
            Dictionary with journey ID and details
        """
        logger.info(f"Creating shared journey for {len(member_ids) + 1} members")

        journey_id = f"group_{creator_id}_{datetime.now().timestamp()}"

        return {
            "journey_id": journey_id,
            "creator_id": creator_id,
            "member_ids": member_ids,
            "meeting_point": meeting_point,
            "meeting_time": meeting_time or (datetime.now() + timedelta(minutes=10)),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }

    @staticmethod
    def get_group_progress(journey_id: str) -> Dict[str, Any]:
        """
        Get group navigation progress for all members.

        Args:
            journey_id: Shared journey ID

        Returns:
            Dictionary with group progress stats
        """
        # Mock data - would query database in production
        members = [
            GroupMember(
                user_id=101,
                name="Sarah Johnson",
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
                current_checkpoint="security",
                progress_percentage=65.0,
                last_update=datetime.now() - timedelta(minutes=2),
                is_delayed=False
            ),
            GroupMember(
                user_id=102,
                name="Michael Chen",
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Michael",
                current_checkpoint="bag_check",
                progress_percentage=35.0,
                last_update=datetime.now() - timedelta(minutes=1),
                is_delayed=True
            ),
            GroupMember(
                user_id=103,
                name="Emma Williams",
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Emma",
                current_checkpoint="security",
                progress_percentage=70.0,
                last_update=datetime.now(),
                is_delayed=False
            )
        ]

        avg_progress = sum(m.progress_percentage for m in members) / len(members)
        delayed_count = sum(1 for m in members if m.is_delayed)

        return {
            "journey_id": journey_id,
            "members": [
                {
                    "user_id": m.user_id,
                    "name": m.name,
                    "avatar_url": m.avatar_url,
                    "current_checkpoint": m.current_checkpoint,
                    "progress_percentage": m.progress_percentage,
                    "last_update": m.last_update.isoformat(),
                    "is_delayed": m.is_delayed
                }
                for m in members
            ],
            "average_progress": round(avg_progress, 1),
            "delayed_members": delayed_count,
            "total_members": len(members),
            "status": "on_track" if delayed_count == 0 else "delayed"
        }

    @staticmethod
    def get_social_feed(
        user_id: int,
        airport_code: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get social feed with travel updates, tips, and photos.

        Args:
            user_id: User ID requesting feed
            airport_code: Filter by airport
            limit: Maximum posts to return
            offset: Pagination offset

        Returns:
            List of social posts
        """
        # Mock data - would query database in production
        mock_posts = [
            {
                "id": 1,
                "user_id": 201,
                "user_name": "Alex Thompson",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex",
                "post_type": "tip",
                "content": "Pro tip: Security line at Checkpoint B is much shorter right now! 5 min wait vs 20 min at A.",
                "location": "Terminal 2",
                "checkpoint_id": 12,
                "image_url": None,
                "likes_count": 24,
                "comments_count": 3,
                "created_at": datetime.now() - timedelta(minutes=5),
                "is_verified_user": True
            },
            {
                "id": 2,
                "user_id": 202,
                "user_name": "Maria Garcia",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Maria",
                "post_type": "photo",
                "content": "Beautiful view from the observation deck!",
                "location": "Terminal 1 - Observation Deck",
                "checkpoint_id": None,
                "image_url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05",
                "likes_count": 45,
                "comments_count": 8,
                "created_at": datetime.now() - timedelta(minutes=15),
                "is_verified_user": True
            },
            {
                "id": 3,
                "user_id": 203,
                "user_name": "James Wilson",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=James",
                "post_type": "recommendation",
                "content": "The Italian restaurant near Gate 15 is amazing! Try the carbonara. 🍝",
                "location": "Terminal 3 - Gate Area",
                "checkpoint_id": None,
                "image_url": None,
                "likes_count": 18,
                "comments_count": 5,
                "created_at": datetime.now() - timedelta(minutes=30),
                "is_verified_user": False
            }
        ]

        return [
            {
                "id": post["id"],
                "user_id": post["user_id"],
                "user_name": post["user_name"],
                "avatar_url": post["avatar_url"],
                "post_type": post["post_type"],
                "content": post["content"],
                "location": post["location"],
                "checkpoint_id": post["checkpoint_id"],
                "image_url": post["image_url"],
                "likes_count": post["likes_count"],
                "comments_count": post["comments_count"],
                "created_at": post["created_at"].isoformat(),
                "is_verified_user": post["is_verified_user"]
            }
            for post in mock_posts[offset:offset + limit]
        ]

    @staticmethod
    def send_friend_invite(
        from_user_id: int,
        to_user_id: int,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a friend request with optional message.

        Args:
            from_user_id: User sending invite
            to_user_id: User receiving invite
            message: Optional personal message

        Returns:
            Invite details
        """
        logger.info(f"User {from_user_id} sending friend invite to {to_user_id}")

        return {
            "invite_id": f"inv_{from_user_id}_{to_user_id}_{datetime.now().timestamp()}",
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "message": message,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }

    @staticmethod
    def update_privacy_settings(
        user_id: int,
        share_location: bool = True,
        share_flight_info: bool = False,
        allow_buddy_requests: bool = True,
        visible_to: str = "verified_only"  # all, verified_only, friends_only
    ) -> Dict[str, Any]:
        """
        Update user privacy settings for social features.

        Args:
            user_id: User ID
            share_location: Allow location sharing
            share_flight_info: Share flight details
            allow_buddy_requests: Accept travel buddy requests
            visible_to: Profile visibility level

        Returns:
            Updated privacy settings
        """
        logger.info(f"Updating privacy settings for user {user_id}")

        return {
            "user_id": user_id,
            "share_location": share_location,
            "share_flight_info": share_flight_info,
            "allow_buddy_requests": allow_buddy_requests,
            "visible_to": visible_to,
            "updated_at": datetime.now().isoformat()
        }

    @staticmethod
    def create_checkpoint_photo(
        user_id: int,
        checkpoint_id: int,
        image_url: str,
        caption: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Share a photo at a checkpoint.

        Args:
            user_id: User sharing photo
            checkpoint_id: Checkpoint where photo was taken
            image_url: URL to uploaded image
            caption: Photo caption
            tags: Photo tags

        Returns:
            Photo post details
        """
        logger.info(f"User {user_id} sharing photo at checkpoint {checkpoint_id}")

        return {
            "photo_id": f"photo_{user_id}_{datetime.now().timestamp()}",
            "user_id": user_id,
            "checkpoint_id": checkpoint_id,
            "image_url": image_url,
            "caption": caption,
            "tags": tags or [],
            "likes_count": 0,
            "comments_count": 0,
            "created_at": datetime.now().isoformat()
        }
