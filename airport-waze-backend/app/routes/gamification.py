"""
Gamification API Routes for AirportWaze
Provides endpoints for user profiles, achievements, leaderboards, challenges, and streaks
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from app.database import get_db
from app.models.gamification import (
    UserProfile,
    Achievement,
    UserAchievement,
    TravelStreak,
    Challenge,
    UserChallenge,
    Reward,
    LeaderboardEntry,
    LeaderboardPeriod,
    ChallengeType,
    AchievementRarity
)
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


# Request/Response Models
class XPAwardRequest(BaseModel):
    user_id: int
    amount: int = Field(..., gt=0, description="Amount of XP to award")
    reason: Optional[str] = None


class XPAwardResponse(BaseModel):
    success: bool
    total_xp: int
    level: int
    level_up: bool
    levels_gained: int = 0
    new_level: Optional[int] = None


class ChallengeJoinRequest(BaseModel):
    user_id: int
    challenge_id: int


class ProgressUpdateRequest(BaseModel):
    user_id: int
    achievement_id: Optional[int] = None
    challenge_id: Optional[int] = None
    progress: int


# Helper Functions
def get_or_create_user_profile(db: Session, user_id: int) -> UserProfile:
    """Get or create user profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

        # Create initial streak
        streak = TravelStreak(user_profile_id=profile.id)
        db.add(streak)
        db.commit()

    return profile


def check_achievement_progress(db: Session, user_id: int, profile: UserProfile) -> List[dict]:
    """Check and update achievement progress, return newly unlocked achievements"""
    unlocked_achievements = []

    # Get all achievements
    achievements = db.query(Achievement).filter(Achievement.is_active == True).all()

    for achievement in achievements:
        # Get or create user achievement
        user_achievement = db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_profile_id == profile.id,
                UserAchievement.achievement_id == achievement.id
            )
        ).first()

        if not user_achievement:
            user_achievement = UserAchievement(
                user_profile_id=profile.id,
                achievement_id=achievement.id
            )
            db.add(user_achievement)

        # Skip if already unlocked
        if user_achievement.is_unlocked:
            continue

        # Check progress based on requirement type
        current_progress = 0
        if achievement.requirement_type == 'trips':
            current_progress = profile.total_trips
        elif achievement.requirement_type == 'distance':
            current_progress = int(profile.total_distance_km)
        elif achievement.requirement_type == 'checkpoints':
            current_progress = profile.total_checkpoints_visited
        elif achievement.requirement_type == 'airports':
            current_progress = profile.total_airports_visited
        elif achievement.requirement_type == 'time_saved':
            current_progress = profile.total_time_saved_minutes
        elif achievement.requirement_type == 'level':
            current_progress = profile.level

        # Update progress
        if user_achievement.update_progress(current_progress):
            # Achievement just unlocked
            unlocked_achievements.append({
                'id': achievement.id,
                'name': achievement.name,
                'xp_reward': achievement.xp_reward,
                'badge_id': achievement.badge_id
            })

            # Award XP
            profile.add_xp(achievement.xp_reward)

            # Add badge if applicable
            if achievement.badge_id and achievement.badge_id not in profile.badges_unlocked:
                badges = profile.badges_unlocked or []
                badges.append(achievement.badge_id)
                profile.badges_unlocked = badges

    db.commit()
    return unlocked_achievements


# Endpoints

@router.get("/profile")
async def get_user_profile(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get user gamification profile with stats and progress"""
    profile = get_or_create_user_profile(db, user_id)
    return profile.to_dict()


@router.post("/award-xp", response_model=XPAwardResponse)
async def award_xp(
    request: XPAwardRequest,
    db: Session = Depends(get_db)
):
    """Award XP to a user and check for level ups"""
    profile = get_or_create_user_profile(db, request.user_id)

    # Award XP
    result = profile.add_xp(request.amount)
    profile.last_active_at = datetime.utcnow()

    # Update streak
    if profile.travel_streak:
        streak_result = profile.travel_streak.check_and_update_streak()
        if streak_result.get('milestone_reached'):
            # Award bonus XP for streak milestone
            milestone_xp = profile.travel_streak.current_streak * 10
            profile.add_xp(milestone_xp)

    # Check for newly unlocked achievements
    unlocked = check_achievement_progress(db, request.user_id, profile)

    db.commit()

    return XPAwardResponse(
        success=True,
        total_xp=profile.total_xp,
        level=profile.level,
        level_up=result['level_up'],
        levels_gained=result['levels_gained'],
        new_level=result.get('new_level')
    )


@router.get("/achievements")
async def get_achievements(
    user_id: Optional[int] = Query(None, description="User ID for progress tracking"),
    recent: Optional[int] = Query(None, description="Get N most recent unlocked achievements"),
    category: Optional[str] = Query(None, description="Filter by category"),
    rarity: Optional[str] = Query(None, description="Filter by rarity"),
    db: Session = Depends(get_db)
):
    """Get all achievements with optional user progress"""
    query = db.query(Achievement).filter(Achievement.is_active == True)

    # Apply filters
    if category:
        query = query.filter(Achievement.category == category)
    if rarity:
        query = query.filter(Achievement.rarity == rarity)

    achievements = query.all()

    if user_id:
        profile = get_or_create_user_profile(db, user_id)

        # Get user achievements with progress
        user_achievements = []
        for achievement in achievements:
            user_achievement = db.query(UserAchievement).filter(
                and_(
                    UserAchievement.user_profile_id == profile.id,
                    UserAchievement.achievement_id == achievement.id
                )
            ).first()

            if not user_achievement:
                user_achievement = UserAchievement(
                    user_profile_id=profile.id,
                    achievement_id=achievement.id
                )
                db.add(user_achievement)

            user_achievements.append(user_achievement.to_dict())

        db.commit()

        # Filter for recent unlocked if requested
        if recent:
            user_achievements = [
                ua for ua in user_achievements if ua['is_unlocked']
            ]
            user_achievements.sort(
                key=lambda x: x.get('unlocked_at', ''),
                reverse=True
            )
            user_achievements = user_achievements[:recent]

        return user_achievements
    else:
        return [achievement.to_dict() for achievement in achievements]


@router.get("/leaderboard")
async def get_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.WEEKLY, description="Time period"),
    metric: str = Query("xp", description="Metric to rank by (xp, distance, checkpoints, airports)"),
    limit: int = Query(100, ge=1, le=500, description="Number of entries to return"),
    user_id: Optional[int] = Query(None, description="Get current user's rank"),
    db: Session = Depends(get_db)
):
    """Get leaderboard rankings for specified period and metric"""

    # Calculate period dates
    now = datetime.utcnow()
    if period == LeaderboardPeriod.DAILY:
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)
    elif period == LeaderboardPeriod.WEEKLY:
        days_since_monday = now.weekday()
        period_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=7)
    elif period == LeaderboardPeriod.MONTHLY:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = period_start.month % 12 + 1
        year = period_start.year if next_month > 1 else period_start.year + 1
        period_end = period_start.replace(month=next_month, year=year)
    else:  # ALL_TIME
        period_start = datetime(2020, 1, 1)
        period_end = now + timedelta(days=365)

    # Build query based on metric
    if metric == "xp":
        score_column = UserProfile.total_xp
    elif metric == "distance":
        score_column = UserProfile.total_distance_km
    elif metric == "checkpoints":
        score_column = UserProfile.total_checkpoints_visited
    elif metric == "airports":
        score_column = UserProfile.total_airports_visited
    else:
        raise HTTPException(status_code=400, detail="Invalid metric")

    # Get ranked profiles
    profiles = db.query(UserProfile).order_by(desc(score_column)).limit(limit).all()

    rankings = []
    for idx, profile in enumerate(profiles, start=1):
        score = getattr(profile, score_column.name)
        rankings.append({
            'rank': idx,
            'user_id': profile.user_id,
            'level': profile.level,
            'title': profile.title,
            'avatar_url': profile.avatar_url,
            'avatar_frame': profile.avatar_frame,
            'score': float(score) if isinstance(score, (int, float)) else 0
        })

    response = {'rankings': rankings}

    # Add current user's rank if requested
    if user_id:
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if user_profile:
            # Find user's rank
            all_profiles = db.query(UserProfile).order_by(desc(score_column)).all()
            user_rank = next(
                (idx + 1 for idx, p in enumerate(all_profiles) if p.user_id == user_id),
                None
            )
            if user_rank:
                score = getattr(user_profile, score_column.name)
                response['current_user'] = {
                    'rank': user_rank,
                    'user_id': user_profile.user_id,
                    'level': user_profile.level,
                    'title': user_profile.title,
                    'avatar_url': user_profile.avatar_url,
                    'avatar_frame': user_profile.avatar_frame,
                    'score': float(score) if isinstance(score, (int, float)) else 0
                }

    return response


@router.get("/challenges")
async def get_challenges(
    user_id: Optional[int] = Query(None, description="User ID for participation tracking"),
    active_only: bool = Query(True, description="Only return active challenges"),
    db: Session = Depends(get_db)
):
    """Get all challenges with optional user participation status"""
    query = db.query(Challenge)

    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            and_(
                Challenge.is_active == True,
                Challenge.start_date <= now,
                Challenge.end_date >= now
            )
        )

    challenges = query.all()
    challenge_list = []

    for challenge in challenges:
        challenge_data = challenge.to_dict()

        if user_id:
            profile = get_or_create_user_profile(db, user_id)
            user_challenge = db.query(UserChallenge).filter(
                and_(
                    UserChallenge.user_profile_id == profile.id,
                    UserChallenge.challenge_id == challenge.id
                )
            ).first()

            if user_challenge:
                challenge_data['user_progress'] = user_challenge.to_dict()
            else:
                challenge_data['user_progress'] = None

        challenge_list.append(challenge_data)

    return challenge_list


@router.post("/challenges/join")
async def join_challenge(
    request: ChallengeJoinRequest,
    db: Session = Depends(get_db)
):
    """Join a challenge"""
    profile = get_or_create_user_profile(db, request.user_id)

    # Get challenge
    challenge = db.query(Challenge).filter(Challenge.id == request.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if not challenge.can_join():
        raise HTTPException(status_code=400, detail="Cannot join this challenge")

    # Check if already joined
    existing = db.query(UserChallenge).filter(
        and_(
            UserChallenge.user_profile_id == profile.id,
            UserChallenge.challenge_id == challenge.id
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already joined this challenge")

    # Create user challenge
    user_challenge = UserChallenge(
        user_profile_id=profile.id,
        challenge_id=challenge.id
    )
    db.add(user_challenge)

    # Increment participant count
    challenge.current_participants += 1

    db.commit()

    return {
        "success": True,
        "message": "Successfully joined challenge",
        "challenge": user_challenge.to_dict()
    }


@router.get("/streak")
async def get_streak(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get user's travel streak"""
    profile = get_or_create_user_profile(db, user_id)

    if not profile.travel_streak:
        streak = TravelStreak(user_profile_id=profile.id)
        db.add(streak)
        db.commit()
        db.refresh(streak)
        profile.travel_streak = streak

    return profile.travel_streak.to_dict()


@router.post("/streak/update")
async def update_streak(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Update user's travel streak (call when user completes an activity)"""
    profile = get_or_create_user_profile(db, user_id)

    if not profile.travel_streak:
        streak = TravelStreak(user_profile_id=profile.id)
        db.add(streak)
        db.commit()
        db.refresh(streak)
        profile.travel_streak = streak

    result = profile.travel_streak.check_and_update_streak()
    profile.last_active_at = datetime.utcnow()

    # Award bonus XP for milestones
    if result.get('milestone_reached'):
        milestone_xp = profile.travel_streak.current_streak * 10
        profile.add_xp(milestone_xp)
        result['xp_awarded'] = milestone_xp

    db.commit()

    return {
        "success": True,
        "streak": profile.travel_streak.to_dict(),
        "result": result
    }


@router.get("/rewards")
async def get_rewards(
    user_id: Optional[int] = Query(None, description="User ID to check unlock status"),
    reward_type: Optional[str] = Query(None, description="Filter by reward type"),
    available_only: bool = Query(True, description="Only show available rewards"),
    db: Session = Depends(get_db)
):
    """Get available rewards and unlockables"""
    query = db.query(Reward)

    if available_only:
        now = datetime.utcnow()
        query = query.filter(
            and_(
                Reward.is_available == True,
                or_(
                    Reward.is_limited_time == False,
                    and_(
                        Reward.is_limited_time == True,
                        Reward.available_until >= now
                    )
                )
            )
        )

    if reward_type:
        query = query.filter(Reward.reward_type == reward_type)

    rewards = query.all()
    reward_list = []

    for reward in rewards:
        reward_data = reward.to_dict()

        if user_id:
            profile = get_or_create_user_profile(db, user_id)
            reward_data['can_unlock'] = reward.can_unlock(profile)
        else:
            reward_data['can_unlock'] = False

        reward_list.append(reward_data)

    return reward_list


@router.post("/activity/trip")
async def record_trip(
    user_id: int,
    distance_km: float = 0.0,
    checkpoints_visited: int = 0,
    time_saved_minutes: int = 0,
    airport_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Record a completed trip and update user stats"""
    profile = get_or_create_user_profile(db, user_id)

    # Update stats
    profile.total_trips += 1
    profile.total_distance_km += distance_km
    profile.total_checkpoints_visited += checkpoints_visited
    profile.total_time_saved_minutes += time_saved_minutes

    if airport_id and airport_id not in getattr(profile, 'airports_visited', []):
        profile.total_airports_visited += 1

    profile.last_active_at = datetime.utcnow()

    # Award XP based on activity
    base_xp = 50
    distance_xp = int(distance_km * 10)
    checkpoint_xp = checkpoints_visited * 5
    total_xp = base_xp + distance_xp + checkpoint_xp

    xp_result = profile.add_xp(total_xp)

    # Update streak
    if profile.travel_streak:
        streak_result = profile.travel_streak.check_and_update_streak()

    # Check achievements
    unlocked_achievements = check_achievement_progress(db, user_id, profile)

    db.commit()

    return {
        "success": True,
        "xp_awarded": total_xp,
        "level": profile.level,
        "level_up": xp_result['level_up'],
        "unlocked_achievements": unlocked_achievements,
        "profile": profile.to_dict()
    }


@router.get("/stats/summary")
async def get_stats_summary(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get comprehensive stats summary for a user"""
    profile = get_or_create_user_profile(db, user_id)

    # Get achievement stats
    achievements = db.query(UserAchievement).filter(
        UserAchievement.user_profile_id == profile.id
    ).all()

    unlocked_count = len([a for a in achievements if a.is_unlocked])
    total_count = db.query(Achievement).filter(Achievement.is_active == True).count()

    # Get active challenges
    active_challenges = db.query(UserChallenge).join(Challenge).filter(
        and_(
            UserChallenge.user_profile_id == profile.id,
            UserChallenge.is_completed == False,
            Challenge.is_active == True
        )
    ).count()

    return {
        "profile": profile.to_dict(),
        "streak": profile.travel_streak.to_dict() if profile.travel_streak else None,
        "achievements": {
            "unlocked": unlocked_count,
            "total": total_count,
            "percentage": round((unlocked_count / total_count * 100) if total_count > 0 else 0, 1)
        },
        "active_challenges": active_challenges
    }
