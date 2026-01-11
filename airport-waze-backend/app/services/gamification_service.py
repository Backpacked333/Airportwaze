"""
Gamification Service - Rewards, Achievements, and Engagement

Transform airport navigation into an engaging, rewarding experience with:
- XP points and leveling system
- Achievements and badges
- Travel streaks and milestones
- Leaderboards and competitions
- Rewards and unlockables
- Social sharing and challenges
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from collections import defaultdict

from app.models.gamification import (
    UserProfile,
    Achievement,
    UserAchievement,
    TravelStreak,
    Leaderboard,
    Challenge,
    UserChallenge,
    Reward
)

logger = logging.getLogger(__name__)


class GamificationService:
    """Service for gamification features."""

    # XP Points for different actions
    XP_VALUES = {
        "location_trace_submitted": 5,
        "wait_time_reported": 10,
        "checkpoint_discovered": 50,
        "flight_completed": 100,
        "helped_another_user": 25,
        "verified_checkpoint": 75,
        "daily_login": 10,
        "weekly_streak": 50,
        "monthly_streak": 200,
        "referral": 500,
        "feedback_submitted": 15,
        "bug_report": 30,
        "photo_uploaded": 20,
        "review_written": 25,
    }

    # Level thresholds (XP needed for each level)
    LEVEL_THRESHOLDS = [
        0, 100, 250, 500, 1000, 2000, 3500, 5500, 8000,
        11000, 15000, 20000, 26000, 33000, 41000, 50000
    ]

    @staticmethod
    def get_or_create_profile(db: Session, user_id: int) -> UserProfile:
        """Get or create user gamification profile."""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not profile:
            profile = UserProfile(
                user_id=user_id,
                level=1,
                total_xp=0,
                current_streak_days=0
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

        return profile

    @staticmethod
    def award_xp(
        db: Session,
        user_id: int,
        action: str,
        amount: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[int, int, bool]:
        """
        Award XP points to user and check for level up.

        Returns:
            Tuple of (new_xp, new_level, leveled_up)
        """
        profile = GamificationService.get_or_create_profile(db, user_id)

        # Get XP amount
        xp_amount = amount if amount is not None else GamificationService.XP_VALUES.get(action, 0)

        if xp_amount == 0:
            logger.warning(f"Unknown action for XP: {action}")
            return profile.total_xp, profile.level, False

        # Add XP
        old_level = profile.level
        profile.total_xp += xp_amount
        profile.xp_this_week += xp_amount
        profile.xp_this_month += xp_amount

        # Check for level up
        new_level = GamificationService._calculate_level(profile.total_xp)
        leveled_up = new_level > old_level

        if leveled_up:
            profile.level = new_level
            logger.info(f"User {user_id} leveled up to {new_level}!")

            # Award level-up achievement
            GamificationService._check_level_achievements(db, user_id, new_level)

        db.commit()
        db.refresh(profile)

        return profile.total_xp, profile.level, leveled_up

    @staticmethod
    def _calculate_level(total_xp: int) -> int:
        """Calculate level based on total XP."""
        for level, threshold in enumerate(GamificationService.LEVEL_THRESHOLDS, start=1):
            if total_xp < threshold:
                return max(1, level - 1)
        return len(GamificationService.LEVEL_THRESHOLDS)

    @staticmethod
    def _check_level_achievements(db: Session, user_id: int, level: int):
        """Award achievements for reaching certain levels."""
        level_achievements = {
            5: "level_5_explorer",
            10: "level_10_navigator",
            15: "level_15_master",
            20: "level_20_legend"
        }

        achievement_id = level_achievements.get(level)
        if achievement_id:
            GamificationService.unlock_achievement(db, user_id, achievement_id)

    @staticmethod
    def unlock_achievement(
        db: Session,
        user_id: int,
        achievement_id: str,
        progress: int = 100
    ) -> Optional[UserAchievement]:
        """
        Unlock an achievement for a user.

        Returns the UserAchievement if newly unlocked, None if already unlocked.
        """
        # Check if already unlocked
        existing = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        ).first()

        if existing and existing.unlocked:
            return None  # Already unlocked

        # Get achievement details
        achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()

        if not achievement:
            logger.error(f"Achievement not found: {achievement_id}")
            return None

        if existing:
            # Update progress
            existing.progress = progress
            existing.unlocked = progress >= 100
            existing.unlocked_at = datetime.utcnow() if existing.unlocked else None
            user_achievement = existing
        else:
            # Create new
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                progress=progress,
                unlocked=progress >= 100,
                unlocked_at=datetime.utcnow() if progress >= 100 else None
            )
            db.add(user_achievement)

        # Award XP if unlocked
        if user_achievement.unlocked and achievement.xp_reward:
            GamificationService.award_xp(
                db, user_id, f"achievement_{achievement_id}", amount=achievement.xp_reward
            )

        db.commit()
        db.refresh(user_achievement)

        logger.info(f"Achievement {achievement_id} unlocked for user {user_id}")
        return user_achievement

    @staticmethod
    def update_streak(db: Session, user_id: int) -> Dict:
        """
        Update user's travel streak.

        A streak continues if the user has activity within 7 days.
        """
        profile = GamificationService.get_or_create_profile(db, user_id)
        streak = db.query(TravelStreak).filter(TravelStreak.user_id == user_id).first()

        now = datetime.utcnow()

        if not streak:
            # First time
            streak = TravelStreak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_activity_date=now.date()
            )
            db.add(streak)
        else:
            days_since_last = (now.date() - streak.last_activity_date).days

            if days_since_last == 0:
                # Same day, no change
                pass
            elif days_since_last <= 7:
                # Within 7 days, continue streak
                streak.current_streak += 1
                streak.last_activity_date = now.date()

                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak

                # Award streak achievements
                if streak.current_streak == 7:
                    GamificationService.unlock_achievement(db, user_id, "week_warrior")
                    GamificationService.award_xp(db, user_id, "weekly_streak")
                elif streak.current_streak == 30:
                    GamificationService.unlock_achievement(db, user_id, "monthly_master")
                    GamificationService.award_xp(db, user_id, "monthly_streak")
            else:
                # Streak broken
                streak.current_streak = 1
                streak.last_activity_date = now.date()

        # Update profile
        profile.current_streak_days = streak.current_streak
        profile.longest_streak_days = max(profile.longest_streak_days, streak.longest_streak)

        db.commit()

        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "broke_streak": (streak.current_streak == 1 and streak.longest_streak > 1)
        }

    @staticmethod
    def get_leaderboard(
        db: Session,
        period: str = "all_time",  # "daily", "weekly", "monthly", "all_time"
        category: str = "xp",  # "xp", "reports", "discoveries", "flights"
        limit: int = 100
    ) -> List[Dict]:
        """Get leaderboard rankings."""
        now = datetime.utcnow()

        query = db.query(UserProfile).join(UserProfile.user)

        # Filter by period
        if period == "daily":
            # Reset daily at midnight
            pass  # XP is cumulative, would need separate daily tracking
        elif period == "weekly":
            query = query.filter(UserProfile.xp_this_week > 0)
        elif period == "monthly":
            query = query.filter(UserProfile.xp_this_month > 0)

        # Order by category
        if category == "xp":
            if period == "weekly":
                query = query.order_by(UserProfile.xp_this_week.desc())
            elif period == "monthly":
                query = query.order_by(UserProfile.xp_this_month.desc())
            else:
                query = query.order_by(UserProfile.total_xp.desc())
        elif category == "reports":
            query = query.order_by(UserProfile.total_reports_submitted.desc())
        elif category == "discoveries":
            query = query.order_by(UserProfile.total_checkpoints_discovered.desc())
        elif category == "flights":
            query = query.order_by(UserProfile.total_flights_completed.desc())

        profiles = query.limit(limit).all()

        leaderboard = []
        for rank, profile in enumerate(profiles, start=1):
            leaderboard.append({
                "rank": rank,
                "user_id": profile.user_id,
                "username": profile.user.full_name if profile.user else "Anonymous",
                "level": profile.level,
                "total_xp": profile.total_xp,
                "xp_this_week": profile.xp_this_week,
                "xp_this_month": profile.xp_this_month,
                "avatar": profile.avatar_url,
                "badge": profile.display_badge
            })

        return leaderboard

    @staticmethod
    def create_challenge(
        db: Session,
        title: str,
        description: str,
        challenge_type: str,
        target_value: int,
        start_date: datetime,
        end_date: datetime,
        xp_reward: int,
        metadata: Optional[Dict] = None
    ) -> Challenge:
        """Create a new challenge."""
        challenge = Challenge(
            title=title,
            description=description,
            challenge_type=challenge_type,
            target_value=target_value,
            start_date=start_date,
            end_date=end_date,
            xp_reward=xp_reward,
            metadata=metadata
        )

        db.add(challenge)
        db.commit()
        db.refresh(challenge)

        logger.info(f"Challenge created: {title}")
        return challenge

    @staticmethod
    def join_challenge(db: Session, user_id: int, challenge_id: int) -> UserChallenge:
        """User joins a challenge."""
        # Check if already joined
        existing = db.query(UserChallenge).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.challenge_id == challenge_id
        ).first()

        if existing:
            return existing

        user_challenge = UserChallenge(
            user_id=user_id,
            challenge_id=challenge_id,
            current_progress=0,
            completed=False
        )

        db.add(user_challenge)
        db.commit()
        db.refresh(user_challenge)

        return user_challenge

    @staticmethod
    def update_challenge_progress(
        db: Session,
        user_id: int,
        challenge_id: int,
        progress_increment: int
    ) -> bool:
        """
        Update user's progress in a challenge.

        Returns True if challenge was completed.
        """
        user_challenge = db.query(UserChallenge).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.challenge_id == challenge_id
        ).first()

        if not user_challenge:
            logger.warning(f"User {user_id} not in challenge {challenge_id}")
            return False

        if user_challenge.completed:
            return False  # Already completed

        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()

        user_challenge.current_progress += progress_increment

        if user_challenge.current_progress >= challenge.target_value:
            user_challenge.completed = True
            user_challenge.completed_at = datetime.utcnow()

            # Award XP
            GamificationService.award_xp(
                db, user_id, f"challenge_{challenge_id}", amount=challenge.xp_reward
            )

            logger.info(f"User {user_id} completed challenge {challenge_id}")
            db.commit()
            return True

        db.commit()
        return False

    @staticmethod
    def get_user_stats(db: Session, user_id: int) -> Dict:
        """Get comprehensive user statistics."""
        profile = GamificationService.get_or_create_profile(db, user_id)
        streak = db.query(TravelStreak).filter(TravelStreak.user_id == user_id).first()

        # Get achievements
        unlocked_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.unlocked == True
        ).count()

        total_achievements = db.query(Achievement).count()

        # Get active challenges
        active_challenges = db.query(UserChallenge).join(Challenge).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.completed == False,
            Challenge.end_date >= datetime.utcnow()
        ).count()

        # Calculate next level progress
        current_level_threshold = GamificationService.LEVEL_THRESHOLDS[profile.level - 1]
        next_level_threshold = GamificationService.LEVEL_THRESHOLDS[profile.level] if profile.level < len(GamificationService.LEVEL_THRESHOLDS) else current_level_threshold
        progress_to_next_level = (profile.total_xp - current_level_threshold) / (next_level_threshold - current_level_threshold) * 100

        return {
            "user_id": user_id,
            "level": profile.level,
            "total_xp": profile.total_xp,
            "xp_this_week": profile.xp_this_week,
            "xp_this_month": profile.xp_this_month,
            "progress_to_next_level": round(progress_to_next_level, 1),
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "achievements_unlocked": unlocked_achievements,
            "total_achievements": total_achievements,
            "achievement_completion_rate": round(unlocked_achievements / total_achievements * 100, 1) if total_achievements > 0 else 0,
            "active_challenges": active_challenges,
            "total_flights": profile.total_flights_completed,
            "total_reports": profile.total_reports_submitted,
            "total_discoveries": profile.total_checkpoints_discovered,
            "total_airports_visited": profile.total_airports_visited,
            "favorite_airport": profile.favorite_airport,
            "rank_global": GamificationService._get_user_rank(db, user_id),
            "display_badge": profile.display_badge,
            "title": profile.title
        }

    @staticmethod
    def _get_user_rank(db: Session, user_id: int) -> int:
        """Get user's global rank by total XP."""
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if not profile:
            return 0

        rank = db.query(func.count(UserProfile.id)).filter(
            UserProfile.total_xp > profile.total_xp
        ).scalar()

        return rank + 1

    @staticmethod
    def reset_weekly_stats(db: Session):
        """Reset weekly XP counters (run as scheduled job)."""
        db.query(UserProfile).update({"xp_this_week": 0})
        db.commit()
        logger.info("Weekly stats reset")

    @staticmethod
    def reset_monthly_stats(db: Session):
        """Reset monthly XP counters (run as scheduled job)."""
        db.query(UserProfile).update({"xp_this_month": 0})
        db.commit()
        logger.info("Monthly stats reset")
