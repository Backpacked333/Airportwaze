"""Wellness and stress management service for AirportWaze."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StressLevel(Enum):
    """Stress level categories."""
    CALM = "calm"
    MILD = "mild"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StressAssessment:
    """User stress level assessment."""
    stress_level: StressLevel
    stress_score: float  # 0-100
    factors: Dict[str, Any]
    recommendations: List[str]
    breathing_exercises: List[Dict[str, Any]]
    calm_zones: List[Dict[str, Any]]
    estimated_relief_time: int  # minutes


@dataclass
class BreathingExercise:
    """Guided breathing exercise."""
    id: int
    name: str
    description: str
    duration_minutes: int
    difficulty: str  # easy, medium, advanced
    steps: List[str]
    benefits: List[str]
    stress_reduction: int  # percentage


@dataclass
class WellnessMetrics:
    """User wellness metrics."""
    hydration_level: str  # well_hydrated, moderate, dehydrated
    activity_level: int  # steps today
    rest_level: str  # well_rested, moderate, tired
    stress_level: StressLevel
    recommendations: List[str]


class WellnessService:
    """Service for wellness and stress management features."""

    # Breathing exercises library
    BREATHING_EXERCISES = [
        {
            "id": 1,
            "name": "4-7-8 Breathing",
            "description": "A calming technique that helps reduce anxiety quickly",
            "duration_minutes": 5,
            "difficulty": "easy",
            "steps": [
                "Exhale completely through your mouth",
                "Close your mouth and inhale through nose for 4 counts",
                "Hold your breath for 7 counts",
                "Exhale through mouth for 8 counts",
                "Repeat 3-4 times"
            ],
            "benefits": ["Reduces anxiety", "Lowers heart rate", "Promotes sleep"],
            "stress_reduction": 30
        },
        {
            "id": 2,
            "name": "Box Breathing",
            "description": "Used by Navy SEALs to stay calm under pressure",
            "duration_minutes": 10,
            "difficulty": "medium",
            "steps": [
                "Breathe in for 4 counts",
                "Hold for 4 counts",
                "Breathe out for 4 counts",
                "Hold for 4 counts",
                "Repeat for 10 minutes"
            ],
            "benefits": ["Increases focus", "Reduces stress", "Improves performance"],
            "stress_reduction": 40
        },
        {
            "id": 3,
            "name": "Alternate Nostril Breathing",
            "description": "Ancient yogic technique for balance and calm",
            "duration_minutes": 8,
            "difficulty": "advanced",
            "steps": [
                "Close right nostril with thumb",
                "Inhale through left nostril",
                "Close left nostril, release right",
                "Exhale through right nostril",
                "Inhale through right",
                "Switch and repeat"
            ],
            "benefits": ["Balances nervous system", "Improves focus", "Reduces anxiety"],
            "stress_reduction": 45
        },
        {
            "id": 4,
            "name": "Quick Calm",
            "description": "60-second emergency stress relief",
            "duration_minutes": 1,
            "difficulty": "easy",
            "steps": [
                "Take a deep breath in for 4 counts",
                "Hold for 2 counts",
                "Exhale slowly for 6 counts",
                "Repeat 3 times"
            ],
            "benefits": ["Instant calm", "Lowers cortisol", "Quick reset"],
            "stress_reduction": 20
        }
    ]

    # Meditation recommendations
    MEDITATIONS = [
        {
            "id": 1,
            "name": "Travel Meditation",
            "duration_minutes": 10,
            "description": "A guided meditation for travelers",
            "type": "guided",
            "benefits": ["Reduces travel anxiety", "Increases mindfulness"]
        },
        {
            "id": 2,
            "name": "Body Scan",
            "duration_minutes": 15,
            "description": "Progressive relaxation technique",
            "type": "body_scan",
            "benefits": ["Releases tension", "Promotes relaxation"]
        },
        {
            "id": 3,
            "name": "Mindful Walking",
            "duration_minutes": 5,
            "description": "Walking meditation through terminal",
            "type": "walking",
            "benefits": ["Combines exercise and mindfulness", "Reduces restlessness"]
        }
    ]

    # Stretching exercises
    STRETCHES = [
        {
            "id": 1,
            "name": "Seated Spinal Twist",
            "duration_seconds": 60,
            "description": "Relieves back tension from sitting",
            "difficulty": "easy",
            "equipment": "chair"
        },
        {
            "id": 2,
            "name": "Neck Rolls",
            "duration_seconds": 45,
            "description": "Releases neck and shoulder tension",
            "difficulty": "easy",
            "equipment": "none"
        },
        {
            "id": 3,
            "name": "Standing Forward Fold",
            "duration_seconds": 90,
            "description": "Stretches hamstrings and back",
            "difficulty": "medium",
            "equipment": "none"
        }
    ]

    @staticmethod
    def assess_stress_level(
        time_until_flight: int,  # minutes
        current_checkpoint: str,
        total_checkpoints_remaining: int,
        has_delays: bool = False,
        first_time_flyer: bool = False,
        traveling_with_children: bool = False,
        recent_heart_rate: Optional[int] = None
    ) -> StressAssessment:
        """
        Predict user stress level based on journey factors.

        Algorithm considers:
        - Time pressure (40% weight)
        - Journey complexity (30% weight)
        - Environmental factors (20% weight)
        - Physiological indicators (10% weight)

        Args:
            time_until_flight: Minutes until flight
            current_checkpoint: Current location
            total_checkpoints_remaining: Checkpoints left
            has_delays: Whether there are delays
            first_time_flyer: Is this their first time
            traveling_with_children: Traveling with kids
            recent_heart_rate: Recent heart rate if available

        Returns:
            StressAssessment with level, score, and recommendations
        """
        logger.info(f"Assessing stress level: {time_until_flight}min to flight")

        stress_score = 0.0
        factors = {}

        # Time pressure factor (40%)
        if time_until_flight < 30:
            time_stress = 40.0
            factors["time_pressure"] = "critical"
        elif time_until_flight < 60:
            time_stress = 30.0
            factors["time_pressure"] = "high"
        elif time_until_flight < 90:
            time_stress = 20.0
            factors["time_pressure"] = "moderate"
        else:
            time_stress = 10.0
            factors["time_pressure"] = "low"

        stress_score += time_stress

        # Journey complexity (30%)
        checkpoint_stress = min(total_checkpoints_remaining * 7.5, 30.0)
        stress_score += checkpoint_stress
        factors["checkpoints_remaining"] = total_checkpoints_remaining

        # Environmental factors (20%)
        env_stress = 0.0
        if has_delays:
            env_stress += 10.0
            factors["has_delays"] = True
        if first_time_flyer:
            env_stress += 5.0
            factors["first_time_flyer"] = True
        if traveling_with_children:
            env_stress += 5.0
            factors["traveling_with_children"] = True

        stress_score += env_stress

        # Physiological indicators (10%)
        if recent_heart_rate:
            if recent_heart_rate > 100:
                stress_score += 10.0
                factors["elevated_heart_rate"] = True
            elif recent_heart_rate > 85:
                stress_score += 5.0

        # Determine stress level
        if stress_score >= 80:
            stress_level = StressLevel.CRITICAL
        elif stress_score >= 60:
            stress_level = StressLevel.HIGH
        elif stress_score >= 40:
            stress_level = StressLevel.MODERATE
        elif stress_score >= 20:
            stress_level = StressLevel.MILD
        else:
            stress_level = StressLevel.CALM

        # Generate recommendations
        recommendations = WellnessService._generate_stress_recommendations(
            stress_level, time_until_flight, factors
        )

        # Suggest breathing exercises
        if stress_score >= 40:
            exercises = [
                WellnessService.BREATHING_EXERCISES[0],  # 4-7-8
                WellnessService.BREATHING_EXERCISES[3]   # Quick Calm
            ]
        else:
            exercises = [WellnessService.BREATHING_EXERCISES[0]]

        # Find calm zones
        calm_zones = [
            {
                "name": "Meditation Room",
                "location": "Near Gate 15",
                "distance_minutes": 5,
                "amenities": ["quiet", "seating", "dim_lighting"]
            },
            {
                "name": "Observation Deck",
                "location": "Terminal 2, Level 3",
                "distance_minutes": 8,
                "amenities": ["natural_light", "views", "fresh_air"]
            }
        ]

        estimated_relief = int(5 + (stress_score / 10))

        return StressAssessment(
            stress_level=stress_level,
            stress_score=stress_score,
            factors=factors,
            recommendations=recommendations,
            breathing_exercises=exercises,
            calm_zones=calm_zones,
            estimated_relief_time=estimated_relief
        )

    @staticmethod
    def _generate_stress_recommendations(
        stress_level: StressLevel,
        time_until_flight: int,
        factors: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized stress management recommendations."""
        recommendations = []

        if stress_level in [StressLevel.CRITICAL, StressLevel.HIGH]:
            recommendations.append("Try a quick 1-minute breathing exercise now")
            recommendations.append("Focus on one step at a time")

            if time_until_flight < 45:
                recommendations.append("Notify airline staff if you need assistance")
            else:
                recommendations.append("You have time - take a 5-minute break")

        if stress_level == StressLevel.MODERATE:
            recommendations.append("Consider a 5-minute breathing exercise")
            recommendations.append("Stay hydrated - grab water if needed")

        if factors.get("first_time_flyer"):
            recommendations.append("Ask staff for help - they're here to assist you")

        if factors.get("traveling_with_children"):
            recommendations.append("Find a family care room for a quiet moment")

        if factors.get("has_delays"):
            recommendations.append("Check with gate agent for latest updates")

        if not recommendations:
            recommendations.append("You're doing great! Keep up the good pace")

        return recommendations

    @staticmethod
    def get_breathing_exercise(exercise_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a breathing exercise by ID or recommend based on time available.

        Args:
            exercise_id: Specific exercise ID, or None for recommendation

        Returns:
            Breathing exercise details
        """
        if exercise_id:
            for exercise in WellnessService.BREATHING_EXERCISES:
                if exercise["id"] == exercise_id:
                    return exercise
            return WellnessService.BREATHING_EXERCISES[0]

        # Recommend quick exercise by default
        return WellnessService.BREATHING_EXERCISES[3]  # Quick Calm

    @staticmethod
    def track_hydration(
        user_id: int,
        last_drink_time: Optional[datetime] = None,
        flight_duration_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Track hydration and provide reminders.

        Args:
            user_id: User ID
            last_drink_time: Last time user drank water
            flight_duration_hours: Upcoming flight duration

        Returns:
            Hydration status and recommendations
        """
        now = datetime.now()

        if last_drink_time:
            hours_since_drink = (now - last_drink_time).total_seconds() / 3600
        else:
            hours_since_drink = 2.0  # Assume 2 hours if unknown

        # Hydration status
        if hours_since_drink < 1:
            status = "well_hydrated"
            reminder = None
        elif hours_since_drink < 2:
            status = "moderate"
            reminder = "Consider drinking water soon"
        else:
            status = "dehydrated"
            reminder = "Time to hydrate! Find a water fountain nearby"

        # Flight-specific recommendations
        recommendations = []
        if flight_duration_hours and flight_duration_hours > 3:
            recommendations.append(f"Bring water bottle for {flight_duration_hours:.1f}h flight")
            recommendations.append("Drink 8oz every hour during flight")

        return {
            "user_id": user_id,
            "status": status,
            "hours_since_drink": round(hours_since_drink, 1),
            "reminder": reminder,
            "recommendations": recommendations,
            "next_reminder_at": (now + timedelta(hours=1)).isoformat()
        }

    @staticmethod
    def track_activity(
        user_id: int,
        steps_today: int,
        distance_walked_km: float
    ) -> Dict[str, Any]:
        """
        Track walking activity and provide encouragement.

        Args:
            user_id: User ID
            steps_today: Steps taken today
            distance_walked_km: Distance walked in km

        Returns:
            Activity stats and encouragement
        """
        # Goals
        step_goal = 10000
        distance_goal = 8.0

        step_progress = (steps_today / step_goal) * 100
        distance_progress = (distance_walked_km / distance_goal) * 100

        messages = []
        if step_progress >= 100:
            messages.append("Amazing! You've hit your step goal!")
        elif step_progress >= 75:
            messages.append("Almost there! Just a bit more to hit your goal")
        elif step_progress >= 50:
            messages.append("Great progress! You're halfway to your goal")
        else:
            messages.append("Every step counts! Keep moving")

        # Calculate calories (rough estimate)
        calories_burned = steps_today * 0.04

        return {
            "user_id": user_id,
            "steps_today": steps_today,
            "step_goal": step_goal,
            "step_progress": round(step_progress, 1),
            "distance_km": round(distance_walked_km, 2),
            "distance_goal": distance_goal,
            "distance_progress": round(distance_progress, 1),
            "calories_burned": round(calories_burned),
            "encouragement": messages
        }

    @staticmethod
    def suggest_meditation(
        available_time: int,  # minutes
        environment: str = "terminal"  # terminal, lounge, gate
    ) -> List[Dict[str, Any]]:
        """
        Suggest meditation based on available time and environment.

        Args:
            available_time: Minutes available
            environment: Current environment

        Returns:
            List of suitable meditations
        """
        suitable = []

        for meditation in WellnessService.MEDITATIONS:
            if meditation["duration_minutes"] <= available_time:
                # Adjust recommendations based on environment
                if environment == "terminal" and meditation["type"] == "walking":
                    meditation["recommendation_score"] = 1.0
                elif environment == "lounge" and meditation["type"] == "guided":
                    meditation["recommendation_score"] = 1.0
                else:
                    meditation["recommendation_score"] = 0.8

                suitable.append(meditation)

        # Sort by recommendation score
        suitable.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)

        return suitable

    @staticmethod
    def get_wellness_dashboard(
        user_id: int,
        current_stress: Optional[StressLevel] = None,
        steps_today: int = 0,
        hours_since_hydration: float = 2.0
    ) -> WellnessMetrics:
        """
        Get comprehensive wellness metrics dashboard.

        Args:
            user_id: User ID
            current_stress: Current stress level
            steps_today: Steps taken today
            hours_since_hydration: Hours since last drink

        Returns:
            WellnessMetrics with all health indicators
        """
        # Hydration assessment
        if hours_since_hydration < 1:
            hydration = "well_hydrated"
        elif hours_since_hydration < 2:
            hydration = "moderate"
        else:
            hydration = "dehydrated"

        # Rest assessment (would integrate with sleep data)
        rest = "well_rested"

        # Activity assessment
        if steps_today > 8000:
            activity_msg = "Great activity level today!"
        elif steps_today > 5000:
            activity_msg = "Good movement, keep it up!"
        else:
            activity_msg = "Try to walk more when possible"

        # Generate recommendations
        recommendations = []

        if hydration == "dehydrated":
            recommendations.append("💧 Hydrate now - find a water fountain")

        if steps_today < 5000:
            recommendations.append("🚶 Take a walking break through the terminal")

        if current_stress in [StressLevel.HIGH, StressLevel.CRITICAL]:
            recommendations.append("🧘 High stress detected - try breathing exercises")

        if not recommendations:
            recommendations.append("✨ You're doing well! Keep it up")

        return WellnessMetrics(
            hydration_level=hydration,
            activity_level=steps_today,
            rest_level=rest,
            stress_level=current_stress or StressLevel.CALM,
            recommendations=recommendations
        )

    @staticmethod
    def detect_travel_fatigue(
        hours_traveling: float,
        time_since_sleep: float,
        stress_level: StressLevel,
        layover_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Detect travel fatigue and suggest recovery actions.

        Args:
            hours_traveling: Hours spent traveling today
            time_since_sleep: Hours since last sleep
            stress_level: Current stress level
            layover_duration: Minutes of layover if applicable

        Returns:
            Fatigue assessment and suggestions
        """
        fatigue_score = 0.0

        # Travel duration factor
        fatigue_score += min(hours_traveling * 10, 40)

        # Sleep deprivation factor
        if time_since_sleep > 16:
            fatigue_score += 30
        elif time_since_sleep > 12:
            fatigue_score += 20
        elif time_since_sleep > 8:
            fatigue_score += 10

        # Stress factor
        stress_weights = {
            StressLevel.CRITICAL: 20,
            StressLevel.HIGH: 15,
            StressLevel.MODERATE: 10,
            StressLevel.MILD: 5,
            StressLevel.CALM: 0
        }
        fatigue_score += stress_weights.get(stress_level, 0)

        # Determine fatigue level
        if fatigue_score >= 70:
            fatigue_level = "severe"
        elif fatigue_score >= 50:
            fatigue_level = "high"
        elif fatigue_score >= 30:
            fatigue_level = "moderate"
        else:
            fatigue_level = "low"

        # Generate suggestions
        suggestions = []

        if fatigue_level in ["severe", "high"]:
            if layover_duration and layover_duration > 180:
                suggestions.append("Consider booking a nap room for rest")
                suggestions.append("Look for a quiet lounge to recharge")
            suggestions.append("Find a comfortable seating area")
            suggestions.append("Try a 10-minute meditation")

        if time_since_sleep > 12:
            suggestions.append("Even a 20-minute power nap can help")

        suggestions.append("Stay hydrated to combat fatigue")
        suggestions.append("Light stretching can boost energy")

        return {
            "fatigue_level": fatigue_level,
            "fatigue_score": round(fatigue_score, 1),
            "suggestions": suggestions,
            "should_rest": fatigue_level in ["severe", "high"]
        }
