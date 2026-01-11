"""Wellness and stress management routes for AirportWaze."""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

from app.services.wellness_service import WellnessService, StressLevel
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wellness", tags=["wellness"])


# Request/Response Models
class StressAssessmentRequest(BaseModel):
    """Request for stress level assessment."""
    time_until_flight: int = Field(..., ge=0, description="Minutes until flight")
    current_checkpoint: str
    total_checkpoints_remaining: int = Field(..., ge=0)
    has_delays: bool = False
    first_time_flyer: bool = False
    traveling_with_children: bool = False
    recent_heart_rate: Optional[int] = Field(None, ge=40, le=200)


class HydrationTrackingRequest(BaseModel):
    """Request for hydration tracking."""
    user_id: int
    last_drink_time: Optional[str] = None
    flight_duration_hours: Optional[float] = Field(None, ge=0, le=20)


class ActivityTrackingRequest(BaseModel):
    """Request for activity tracking."""
    user_id: int
    steps_today: int = Field(..., ge=0)
    distance_walked_km: float = Field(..., ge=0)


class MeditationRequest(BaseModel):
    """Request for meditation recommendation."""
    available_time: int = Field(..., ge=1, le=60, description="Minutes available")
    environment: str = Field(default="terminal", pattern="^(terminal|lounge|gate)$")


class WellnessDashboardRequest(BaseModel):
    """Request for wellness dashboard."""
    user_id: int
    current_stress: Optional[str] = None
    steps_today: int = Field(default=0, ge=0)
    hours_since_hydration: float = Field(default=2.0, ge=0, le=24)


class TravelFatigueRequest(BaseModel):
    """Request for travel fatigue detection."""
    hours_traveling: float = Field(..., ge=0, le=48)
    time_since_sleep: float = Field(..., ge=0, le=72)
    stress_level: str
    layover_duration: Optional[int] = Field(None, ge=0)


@router.post("/stress/assess")
@limiter.limit("60/minute")
async def assess_stress(
    request: Request,
    assessment_request: StressAssessmentRequest
):
    """
    Assess current stress level based on journey factors.

    AI-powered stress detection considers:
    - Time pressure (how close to flight time)
    - Journey complexity (checkpoints remaining)
    - Environmental factors (delays, first-time travel)
    - Physiological indicators (heart rate if available)

    Returns personalized recommendations and breathing exercises.
    """
    try:
        assessment = WellnessService.assess_stress_level(
            time_until_flight=assessment_request.time_until_flight,
            current_checkpoint=assessment_request.current_checkpoint,
            total_checkpoints_remaining=assessment_request.total_checkpoints_remaining,
            has_delays=assessment_request.has_delays,
            first_time_flyer=assessment_request.first_time_flyer,
            traveling_with_children=assessment_request.traveling_with_children,
            recent_heart_rate=assessment_request.recent_heart_rate
        )

        return {
            "stress_level": assessment.stress_level.value,
            "stress_score": round(assessment.stress_score, 1),
            "factors": assessment.factors,
            "recommendations": assessment.recommendations,
            "breathing_exercises": assessment.breathing_exercises,
            "calm_zones": assessment.calm_zones,
            "estimated_relief_time": assessment.estimated_relief_time,
            "message": WellnessService._get_stress_message(assessment.stress_level)
        }

    except ValueError as e:
        logger.warning(f"Invalid stress assessment request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assessing stress: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to assess stress level"
        )


@router.get("/breathing/exercises")
@limiter.limit("100/minute")
async def get_breathing_exercises(
    request: Request,
    exercise_id: Optional[int] = Query(None, description="Specific exercise ID")
):
    """
    Get guided breathing exercises for stress relief.

    Includes:
    - 4-7-8 Breathing (quick calm)
    - Box Breathing (focus and performance)
    - Alternate Nostril (balance)
    - Emergency 60-second technique

    Each exercise shows step-by-step instructions.
    """
    try:
        if exercise_id:
            exercise = WellnessService.get_breathing_exercise(exercise_id)
            return exercise
        else:
            # Return all exercises
            return {
                "exercises": WellnessService.BREATHING_EXERCISES
            }

    except Exception as e:
        logger.error(f"Error getting breathing exercises: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get breathing exercises"
        )


@router.post("/hydration/track")
@limiter.limit("60/minute")
async def track_hydration(
    request: Request,
    hydration_request: HydrationTrackingRequest
):
    """
    Track hydration and get reminders.

    Stay healthy while traveling:
    - Monitor time since last drink
    - Get timely reminders
    - Flight-specific recommendations
    - Find nearby water fountains
    """
    try:
        last_drink = None
        if hydration_request.last_drink_time:
            try:
                last_drink = datetime.fromisoformat(
                    hydration_request.last_drink_time.replace('Z', '+00:00')
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid last_drink_time format. Use ISO format."
                )

        tracking = WellnessService.track_hydration(
            user_id=hydration_request.user_id,
            last_drink_time=last_drink,
            flight_duration_hours=hydration_request.flight_duration_hours
        )

        return tracking

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking hydration: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to track hydration"
        )


@router.post("/activity/track")
@limiter.limit("60/minute")
async def track_activity(
    request: Request,
    activity_request: ActivityTrackingRequest
):
    """
    Track walking activity and get encouragement.

    Airport walking counts!
    - Track steps and distance
    - See progress toward daily goal
    - Get motivational messages
    - Estimate calories burned
    """
    try:
        tracking = WellnessService.track_activity(
            user_id=activity_request.user_id,
            steps_today=activity_request.steps_today,
            distance_walked_km=activity_request.distance_walked_km
        )

        return tracking

    except Exception as e:
        logger.error(f"Error tracking activity: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to track activity"
        )


@router.post("/meditation/suggest")
@limiter.limit("60/minute")
async def suggest_meditation(
    request: Request,
    meditation_request: MeditationRequest
):
    """
    Get meditation recommendations based on available time.

    Meditations for:
    - Long layovers (15+ minutes)
    - Quick breaks (5-10 minutes)
    - Walking through terminal
    - Lounge relaxation

    All adapted for airport environments.
    """
    try:
        suggestions = WellnessService.suggest_meditation(
            available_time=meditation_request.available_time,
            environment=meditation_request.environment
        )

        return {
            "available_time": meditation_request.available_time,
            "environment": meditation_request.environment,
            "suggestions": suggestions,
            "total": len(suggestions)
        }

    except Exception as e:
        logger.error(f"Error suggesting meditation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to suggest meditation"
        )


@router.post("/dashboard")
@limiter.limit("60/minute")
async def get_wellness_dashboard(
    request: Request,
    dashboard_request: WellnessDashboardRequest
):
    """
    Get comprehensive wellness metrics dashboard.

    All-in-one view of:
    - Current stress level
    - Hydration status
    - Activity/steps today
    - Rest level
    - Personalized recommendations

    Your travel wellness command center.
    """
    try:
        # Convert stress level string to enum if provided
        stress_level = None
        if dashboard_request.current_stress:
            try:
                stress_level = StressLevel(dashboard_request.current_stress.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid stress level. Must be one of: calm, mild, moderate, high, critical"
                )

        metrics = WellnessService.get_wellness_dashboard(
            user_id=dashboard_request.user_id,
            current_stress=stress_level,
            steps_today=dashboard_request.steps_today,
            hours_since_hydration=dashboard_request.hours_since_hydration
        )

        return {
            "user_id": dashboard_request.user_id,
            "hydration_level": metrics.hydration_level,
            "activity_level": metrics.activity_level,
            "rest_level": metrics.rest_level,
            "stress_level": metrics.stress_level.value,
            "recommendations": metrics.recommendations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wellness dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get wellness dashboard"
        )


@router.post("/fatigue/detect")
@limiter.limit("30/minute")
async def detect_travel_fatigue(
    request: Request,
    fatigue_request: TravelFatigueRequest
):
    """
    Detect travel fatigue and suggest recovery actions.

    Long travel day? We'll help you:
    - Identify fatigue level
    - Find rest areas
    - Suggest recovery activities
    - Recommend nap rooms for long layovers

    Travel smart, arrive refreshed.
    """
    try:
        # Convert stress level string to enum
        try:
            stress_level = StressLevel(fatigue_request.stress_level.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stress level. Must be one of: calm, mild, moderate, high, critical"
            )

        fatigue = WellnessService.detect_travel_fatigue(
            hours_traveling=fatigue_request.hours_traveling,
            time_since_sleep=fatigue_request.time_since_sleep,
            stress_level=stress_level,
            layover_duration=fatigue_request.layover_duration
        )

        return fatigue

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting travel fatigue: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to detect travel fatigue"
        )


@router.get("/stretches")
@limiter.limit("100/minute")
async def get_stretching_exercises(request: Request):
    """
    Get stretching exercises for long waits.

    Combat sitting fatigue with:
    - Seated stretches
    - Standing exercises
    - Neck and shoulder relief
    - Back pain prevention

    All designed for airport environments (no equipment needed).
    """
    try:
        return {
            "stretches": WellnessService.STRETCHES,
            "total": len(WellnessService.STRETCHES)
        }

    except Exception as e:
        logger.error(f"Error getting stretches: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get stretching exercises"
        )


# Helper method for stress messages
def _get_stress_message(stress_level: StressLevel) -> str:
    """Get encouraging message based on stress level."""
    messages = {
        StressLevel.CALM: "You're doing great! Enjoy your journey.",
        StressLevel.MILD: "You're on track. Stay calm and focused.",
        StressLevel.MODERATE: "Take a breath. You've got this.",
        StressLevel.HIGH: "High stress detected. Let's work through this together.",
        StressLevel.CRITICAL: "Take a moment. We're here to help you through this."
    }
    return messages.get(stress_level, "Stay focused on your journey.")


# Add the helper method to WellnessService
WellnessService._get_stress_message = staticmethod(_get_stress_message)
