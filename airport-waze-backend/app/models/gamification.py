"""
Gamification Models for AirportWaze
Provides user engagement through achievements, streaks, leaderboards, and challenges
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base


class AchievementRarity(str, Enum):
    """Achievement rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ChallengeType(str, Enum):
    """Types of challenges users can participate in"""
    DISTANCE = "distance"  # Walk a certain distance
    CHECKPOINTS = "checkpoints"  # Visit specific checkpoints
    TIME_TRIAL = "time_trial"  # Complete route in time
    STREAK = "streak"  # Maintain activity streak
    COMMUNITY = "community"  # Community-wide goal


class LeaderboardPeriod(str, Enum):
    """Leaderboard time periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


class UserProfile(Base):
    """
    User gamification profile with stats, level, and progress
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Level and Experience
    level = Column(Integer, default=1, nullable=False)
    total_xp = Column(Integer, default=0, nullable=False)
    current_level_xp = Column(Integer, default=0, nullable=False)
    xp_to_next_level = Column(Integer, default=100, nullable=False)

    # Avatar and Customization
    avatar_url = Column(String(500))
    avatar_frame = Column(String(100), default="default")
    title = Column(String(100), default="Airport Explorer")

    # Statistics
    total_trips = Column(Integer, default=0)
    total_distance_km = Column(Float, default=0.0)
    total_checkpoints_visited = Column(Integer, default=0)
    total_airports_visited = Column(Integer, default=0)
    total_time_saved_minutes = Column(Integer, default=0)

    # Badges and Collections
    badges_unlocked = Column(JSON, default=list)  # List of badge IDs
    badge_showcase = Column(JSON, default=list)  # Featured badges (max 5)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
    achievements = relationship("UserAchievement", back_populates="profile")
    travel_streak = relationship("TravelStreak", back_populates="profile", uselist=False)
    challenges = relationship("UserChallenge", back_populates="profile")

    def add_xp(self, amount: int) -> Dict[str, Any]:
        """
        Add XP to user profile and handle level ups
        Returns dict with level_up flag and new level if applicable
        """
        self.total_xp += amount
        self.current_level_xp += amount

        level_ups = 0
        result = {"level_up": False, "levels_gained": 0, "new_level": self.level}

        # Check for level up (can level up multiple times)
        while self.current_level_xp >= self.xp_to_next_level:
            self.current_level_xp -= self.xp_to_next_level
            self.level += 1
            level_ups += 1
            # Increase XP requirement for next level (exponential scaling)
            self.xp_to_next_level = int(100 * (1.5 ** (self.level - 1)))

        if level_ups > 0:
            result["level_up"] = True
            result["levels_gained"] = level_ups
            result["new_level"] = self.level

        self.updated_at = datetime.utcnow()
        return result

    def get_level_progress(self) -> float:
        """Get percentage progress to next level"""
        return (self.current_level_xp / self.xp_to_next_level) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "level": self.level,
            "total_xp": self.total_xp,
            "current_level_xp": self.current_level_xp,
            "xp_to_next_level": self.xp_to_next_level,
            "level_progress": self.get_level_progress(),
            "avatar_url": self.avatar_url,
            "avatar_frame": self.avatar_frame,
            "title": self.title,
            "stats": {
                "total_trips": self.total_trips,
                "total_distance_km": self.total_distance_km,
                "total_checkpoints_visited": self.total_checkpoints_visited,
                "total_airports_visited": self.total_airports_visited,
                "total_time_saved_minutes": self.total_time_saved_minutes
            },
            "badges_unlocked": self.badges_unlocked or [],
            "badge_showcase": self.badge_showcase or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None
        }


class Achievement(Base):
    """
    Achievements that users can unlock
    """
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)

    # Achievement Details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=False)
    icon = Column(String(100), nullable=False)  # Icon identifier or URL
    category = Column(String(50), default="general")  # travel, speed, social, etc.

    # Rewards
    xp_reward = Column(Integer, default=50, nullable=False)
    rarity = Column(SQLEnum(AchievementRarity), default=AchievementRarity.COMMON)

    # Requirements
    requirement_type = Column(String(50), nullable=False)  # trips, distance, checkpoints, etc.
    requirement_value = Column(Integer, nullable=False)  # Target value to unlock

    # Badge
    badge_id = Column(String(50), unique=True)  # Unlocks a badge

    # Visibility
    is_hidden = Column(Boolean, default=False)  # Hidden until unlocked
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")

    def to_dict(self, include_hidden: bool = False) -> Dict[str, Any]:
        """Convert achievement to dictionary"""
        if self.is_hidden and not include_hidden:
            return {
                "id": self.id,
                "name": "???",
                "description": "Hidden achievement",
                "icon": "mystery",
                "is_hidden": True
            }

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "xp_reward": self.xp_reward,
            "rarity": self.rarity.value,
            "requirement_type": self.requirement_type,
            "requirement_value": self.requirement_value,
            "badge_id": self.badge_id,
            "is_hidden": self.is_hidden
        }


class UserAchievement(Base):
    """
    User's progress and unlocked achievements
    """
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)

    # Progress
    progress = Column(Integer, default=0)  # Current progress towards achievement
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    def update_progress(self, amount: int) -> bool:
        """
        Update progress and check if achievement is unlocked
        Returns True if achievement was just unlocked
        """
        if self.is_unlocked:
            return False

        self.progress = amount
        self.updated_at = datetime.utcnow()

        if self.progress >= self.achievement.requirement_value:
            self.is_unlocked = True
            self.unlocked_at = datetime.utcnow()
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert user achievement to dictionary"""
        return {
            "id": self.id,
            "achievement": self.achievement.to_dict(include_hidden=self.is_unlocked),
            "progress": self.progress,
            "is_unlocked": self.is_unlocked,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "progress_percentage": (self.progress / self.achievement.requirement_value * 100)
                                   if self.achievement.requirement_value > 0 else 0
        }


class TravelStreak(Base):
    """
    User's travel streak tracking
    """
    __tablename__ = "travel_streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True, nullable=False)

    # Streak Data
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime)
    streak_start_date = Column(DateTime)

    # Milestones
    total_active_days = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="travel_streak")

    def check_and_update_streak(self) -> Dict[str, Any]:
        """
        Check streak status and update accordingly
        Returns streak status and whether it was broken
        """
        now = datetime.utcnow()
        result = {
            "streak_maintained": False,
            "streak_broken": False,
            "streak_started": False,
            "milestone_reached": False,
            "current_streak": self.current_streak
        }

        if not self.last_activity_date:
            # First activity
            self.current_streak = 1
            self.longest_streak = 1
            self.last_activity_date = now
            self.streak_start_date = now
            self.total_active_days = 1
            result["streak_started"] = True
            result["current_streak"] = 1
        else:
            days_since_last = (now.date() - self.last_activity_date.date()).days

            if days_since_last == 0:
                # Same day activity
                result["streak_maintained"] = True
            elif days_since_last == 1:
                # Consecutive day
                self.current_streak += 1
                self.total_active_days += 1
                self.last_activity_date = now
                result["streak_maintained"] = True
                result["current_streak"] = self.current_streak

                # Check for longest streak
                if self.current_streak > self.longest_streak:
                    self.longest_streak = self.current_streak

                # Check for milestones (7, 30, 100, 365 days)
                if self.current_streak in [7, 30, 100, 365]:
                    result["milestone_reached"] = True
            else:
                # Streak broken
                self.current_streak = 1
                self.last_activity_date = now
                self.streak_start_date = now
                self.total_active_days += 1
                result["streak_broken"] = True
                result["current_streak"] = 1

        self.updated_at = now
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert travel streak to dictionary"""
        return {
            "id": self.id,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "last_activity_date": self.last_activity_date.isoformat() if self.last_activity_date else None,
            "streak_start_date": self.streak_start_date.isoformat() if self.streak_start_date else None,
            "total_active_days": self.total_active_days,
            "is_active": self._is_streak_active()
        }

    def _is_streak_active(self) -> bool:
        """Check if streak is still active (within 24 hours)"""
        if not self.last_activity_date:
            return False
        days_since = (datetime.utcnow().date() - self.last_activity_date.date()).days
        return days_since <= 1


class Challenge(Base):
    """
    Time-limited challenges for users
    """
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)

    # Challenge Details
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    challenge_type = Column(SQLEnum(ChallengeType), nullable=False)
    icon = Column(String(100))

    # Requirements
    target_value = Column(Integer, nullable=False)  # Target to complete challenge
    target_metric = Column(String(50), nullable=False)  # What to measure

    # Duration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Rewards
    xp_reward = Column(Integer, default=100)
    badge_reward = Column(String(50))  # Optional badge unlock
    additional_rewards = Column(JSON)  # Other rewards (items, perks, etc.)

    # Status
    is_active = Column(Boolean, default=True)
    max_participants = Column(Integer)  # Optional participant limit
    current_participants = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_challenges = relationship("UserChallenge", back_populates="challenge")

    def is_ongoing(self) -> bool:
        """Check if challenge is currently ongoing"""
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date and self.is_active

    def can_join(self) -> bool:
        """Check if challenge can be joined"""
        if not self.is_ongoing():
            return False
        if self.max_participants and self.current_participants >= self.max_participants:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert challenge to dictionary"""
        now = datetime.utcnow()
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "challenge_type": self.challenge_type.value,
            "icon": self.icon,
            "target_value": self.target_value,
            "target_metric": self.target_metric,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "xp_reward": self.xp_reward,
            "badge_reward": self.badge_reward,
            "additional_rewards": self.additional_rewards,
            "is_active": self.is_active,
            "is_ongoing": self.is_ongoing(),
            "can_join": self.can_join(),
            "max_participants": self.max_participants,
            "current_participants": self.current_participants,
            "time_remaining_hours": (self.end_date - now).total_seconds() / 3600 if self.is_ongoing() else 0
        }


class UserChallenge(Base):
    """
    User's participation and progress in challenges
    """
    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)

    # Progress
    progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)

    # Rewards claimed
    rewards_claimed = Column(Boolean, default=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="challenges")
    challenge = relationship("Challenge", back_populates="user_challenges")

    def update_progress(self, amount: int) -> bool:
        """
        Update progress and check if challenge is completed
        Returns True if challenge was just completed
        """
        if self.is_completed:
            return False

        self.progress = amount
        self.updated_at = datetime.utcnow()

        if self.progress >= self.challenge.target_value:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert user challenge to dictionary"""
        return {
            "id": self.id,
            "challenge": self.challenge.to_dict(),
            "progress": self.progress,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "rewards_claimed": self.rewards_claimed,
            "progress_percentage": (self.progress / self.challenge.target_value * 100)
                                   if self.challenge.target_value > 0 else 0,
            "joined_at": self.joined_at.isoformat()
        }


class Reward(Base):
    """
    Unlockable items, perks, and customizations
    """
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)

    # Reward Details
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    reward_type = Column(String(50), nullable=False)  # avatar, frame, title, perk, item

    # Visuals
    icon = Column(String(100))
    preview_url = Column(String(500))

    # Requirements
    required_level = Column(Integer, default=0)
    required_xp = Column(Integer, default=0)
    required_achievement_id = Column(Integer, ForeignKey("achievements.id"))

    # Rarity
    rarity = Column(SQLEnum(AchievementRarity), default=AchievementRarity.COMMON)

    # Availability
    is_available = Column(Boolean, default=True)
    is_limited_time = Column(Boolean, default=False)
    available_until = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def can_unlock(self, user_profile: UserProfile) -> bool:
        """Check if user can unlock this reward"""
        if not self.is_available:
            return False

        if self.is_limited_time and self.available_until:
            if datetime.utcnow() > self.available_until:
                return False

        if user_profile.level < self.required_level:
            return False

        if user_profile.total_xp < self.required_xp:
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert reward to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "reward_type": self.reward_type,
            "icon": self.icon,
            "preview_url": self.preview_url,
            "required_level": self.required_level,
            "required_xp": self.required_xp,
            "rarity": self.rarity.value,
            "is_available": self.is_available,
            "is_limited_time": self.is_limited_time,
            "available_until": self.available_until.isoformat() if self.available_until else None
        }


class LeaderboardEntry(Base):
    """
    Leaderboard entries for different time periods
    """
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)

    # Period
    period = Column(SQLEnum(LeaderboardPeriod), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Rankings
    rank = Column(Integer)
    score = Column(Integer, default=0)  # Could be XP, distance, checkpoints, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile")

    def to_dict(self, include_profile: bool = True) -> Dict[str, Any]:
        """Convert leaderboard entry to dictionary"""
        entry = {
            "rank": self.rank,
            "score": self.score,
            "period": self.period.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat()
        }

        if include_profile and self.profile:
            entry["user"] = {
                "id": self.profile.user_id,
                "level": self.profile.level,
                "title": self.profile.title,
                "avatar_url": self.profile.avatar_url,
                "avatar_frame": self.profile.avatar_frame
            }

        return entry
