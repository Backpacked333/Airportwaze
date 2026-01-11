"""
AI Features and Smart Notification Routes.

Provides advanced AI-powered predictions and intelligent notifications.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.predictive_ai_service import predictive_ai_service
from app.services.notification_service import notification_service
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.notifications import NotificationPreference, NotificationHistory
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai-features"])


# Pydantic schemas for request/response
class AdvancedPredictionRequest(BaseModel):
    """Request for advanced wait time prediction."""
    airport_code: str = Field(..., description="Airport code (e.g., JFK)", min_length=3, max_length=3)
    checkpoint_id: str = Field(..., description="Checkpoint identifier")
    target_time: Optional[str] = Field(None, description="Target time (ISO format, defaults to now)")
    include_weather: bool = Field(True, description="Include weather impact analysis")
    include_events: bool = Field(True, description="Include event-based predictions")


class SmartSuggestionRequest(BaseModel):
    """Request for smart suggestions."""
    airport_code: str = Field(..., description="Airport code")
    current_lat: float = Field(..., description="Current latitude")
    current_lng: float = Field(..., description="Current longitude")
    flight_info: Optional[Dict] = Field(None, description="Flight information")


class CrowdingPredictionRequest(BaseModel):
    """Request for crowding prediction."""
    airport_code: str = Field(..., description="Airport code")
    terminal: str = Field(..., description="Terminal identifier")
    hours_ahead: int = Field(6, description="Hours to predict ahead", ge=1, le=24)


class NotificationSubscribeRequest(BaseModel):
    """Request to subscribe to push notifications."""
    push_token: str = Field(..., description="Push notification token")
    device_type: str = Field(..., description="Device type (ios, android, web)")


class NotificationPreferenceUpdate(BaseModel):
    """Request to update notification preferences."""
    enable_push: Optional[bool] = None
    enable_email: Optional[bool] = None
    enable_sms: Optional[bool] = None
    enable_in_app: Optional[bool] = None
    enable_gate_changes: Optional[bool] = None
    enable_flight_delays: Optional[bool] = None
    enable_security_alerts: Optional[bool] = None
    enable_leave_now_alerts: Optional[bool] = None
    enable_boarding_alerts: Optional[bool] = None
    enable_route_suggestions: Optional[bool] = None
    enable_weather_alerts: Optional[bool] = None
    enable_reminders: Optional[bool] = None
    enable_personalized_tips: Optional[bool] = None
    min_probability_threshold: Optional[float] = None
    advance_notice_minutes: Optional[int] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    preferred_buffer_minutes: Optional[int] = None


class TestNotificationRequest(BaseModel):
    """Request to send a test notification."""
    notification_type: str = Field("personalized_tip", description="Type of notification to test")


@router.post("/predict-wait-time")
@limiter.limit("100/minute")
async def predict_wait_time_advanced(
    request: Request,
    prediction_request: AdvancedPredictionRequest
) -> Dict:
    """
    Advanced wait time prediction using AI and machine learning.

    Uses multiple ML techniques including:
    - Time series forecasting (ARIMA-like models)
    - Weather impact analysis
    - Event-based predictions
    - Flight schedule analysis
    - Real-time adjustments

    Args:
        prediction_request: Prediction parameters

    Returns:
        Comprehensive prediction with confidence intervals and contributing factors

    Raises:
        HTTPException: 404 if airport/checkpoint not found
    """
    try:
        # Parse target time if provided
        target_time = None
        if prediction_request.target_time:
            try:
                target_time = datetime.fromisoformat(
                    prediction_request.target_time.replace('Z', '+00:00')
                )
                if target_time.tzinfo:
                    target_time = target_time.replace(tzinfo=None)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid target_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )

        result = await predictive_ai_service.predict_wait_time_advanced(
            airport_code=prediction_request.airport_code,
            checkpoint_id=prediction_request.checkpoint_id,
            target_time=target_time,
            include_weather=prediction_request.include_weather,
            include_events=prediction_request.include_events
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Airport or checkpoint not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in advanced prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate advanced prediction"
        )


@router.post("/predict-crowding")
@limiter.limit("50/minute")
async def predict_crowding(
    request: Request,
    crowding_request: CrowdingPredictionRequest
) -> Dict:
    """
    Predict future crowding levels using LSTM-like neural network approach.

    Provides hourly predictions of terminal crowding including:
    - Overall crowding level (low/moderate/high/very_high)
    - Average wait times
    - Checkpoint-specific predictions

    Args:
        crowding_request: Crowding prediction parameters

    Returns:
        Hourly crowding predictions

    Raises:
        HTTPException: 404 if airport not found
    """
    try:
        predictions = await predictive_ai_service.predict_crowding_lstm(
            airport_code=crowding_request.airport_code,
            terminal=crowding_request.terminal,
            hours_ahead=crowding_request.hours_ahead
        )

        if not predictions:
            raise HTTPException(
                status_code=404,
                detail=f"Airport '{crowding_request.airport_code.upper()}' not found"
            )

        return {
            "airport_code": crowding_request.airport_code.upper(),
            "terminal": crowding_request.terminal,
            "predictions": predictions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in crowding prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate crowding prediction"
        )


@router.post("/smart-suggestions")
@limiter.limit("50/minute")
async def get_smart_suggestions(
    request: Request,
    suggestion_request: SmartSuggestionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get context-aware smart suggestions for the user.

    Provides personalized recommendations including:
    - Best checkpoint to use
    - Optimal departure time
    - Route optimization
    - Nearby amenities on route

    Requires authentication.

    Args:
        suggestion_request: Request with location and context
        current_user: Authenticated user

    Returns:
        List of smart suggestions

    Raises:
        HTTPException: 401 if not authenticated, 404 if airport not found
    """
    try:
        suggestions = await predictive_ai_service.generate_smart_suggestions(
            user_id=current_user.id,
            airport_code=suggestion_request.airport_code,
            current_lat=suggestion_request.current_lat,
            current_lng=suggestion_request.current_lng,
            flight_info=suggestion_request.flight_info
        )

        return {
            "suggestions": suggestions,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating smart suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate smart suggestions"
        )


# Notification routes
notification_router = APIRouter(prefix="/notifications", tags=["notifications"])


@notification_router.post("/subscribe")
@limiter.limit("20/minute")
async def subscribe_to_notifications(
    request: Request,
    subscribe_request: NotificationSubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Subscribe to push notifications.

    Register a device token for receiving push notifications.
    Requires authentication.

    Args:
        subscribe_request: Push token and device info
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        success = await notification_service.register_push_token(
            db=db,
            user_id=current_user.id,
            token=subscribe_request.push_token,
            device_type=subscribe_request.device_type
        )

        if success:
            return {
                "status": "success",
                "message": "Successfully subscribed to notifications"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to register push token"
            )

    except Exception as e:
        logger.error(f"Error subscribing to notifications: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to subscribe to notifications"
        )


@notification_router.get("/preferences")
@limiter.limit("50/minute")
async def get_notification_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get user's notification preferences.

    Returns current notification settings for the authenticated user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Notification preferences
    """
    try:
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == current_user.id
        ).first()

        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(user_id=current_user.id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        return {
            "enable_push": prefs.enable_push,
            "enable_email": prefs.enable_email,
            "enable_sms": prefs.enable_sms,
            "enable_in_app": prefs.enable_in_app,
            "enable_gate_changes": prefs.enable_gate_changes,
            "enable_flight_delays": prefs.enable_flight_delays,
            "enable_security_alerts": prefs.enable_security_alerts,
            "enable_leave_now_alerts": prefs.enable_leave_now_alerts,
            "enable_boarding_alerts": prefs.enable_boarding_alerts,
            "enable_route_suggestions": prefs.enable_route_suggestions,
            "enable_weather_alerts": prefs.enable_weather_alerts,
            "enable_reminders": prefs.enable_reminders,
            "enable_personalized_tips": prefs.enable_personalized_tips,
            "min_probability_threshold": prefs.min_probability_threshold,
            "advance_notice_minutes": prefs.advance_notice_minutes,
            "quiet_hours_start": prefs.quiet_hours_start,
            "quiet_hours_end": prefs.quiet_hours_end,
            "preferred_buffer_minutes": prefs.preferred_buffer_minutes
        }

    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get notification preferences"
        )


@notification_router.put("/preferences")
@limiter.limit("30/minute")
async def update_notification_preferences(
    request: Request,
    preferences: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Update user's notification preferences.

    Allows users to customize which notifications they receive and how.

    Args:
        preferences: Updated preference values
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated notification preferences
    """
    try:
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == current_user.id
        ).first()

        if not prefs:
            prefs = NotificationPreference(user_id=current_user.id)
            db.add(prefs)

        # Update only provided fields
        update_data = preferences.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(prefs, field):
                setattr(prefs, field, value)

        db.commit()
        db.refresh(prefs)

        return {
            "status": "success",
            "message": "Notification preferences updated",
            "preferences": {
                "enable_push": prefs.enable_push,
                "enable_email": prefs.enable_email,
                "enable_sms": prefs.enable_sms,
                "enable_in_app": prefs.enable_in_app
            }
        }

    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update notification preferences"
        )


@notification_router.get("/history")
@limiter.limit("50/minute")
async def get_notification_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Maximum notifications to return"),
    unread_only: bool = Query(False, description="Only return unread notifications")
) -> Dict:
    """
    Get notification history for the authenticated user.

    Returns recent notifications sent to the user.

    Args:
        current_user: Authenticated user
        db: Database session
        limit: Maximum number of notifications to return
        unread_only: Filter for unread notifications only

    Returns:
        List of notification history records
    """
    try:
        notifications = await notification_service.get_user_notifications(
            db=db,
            user_id=current_user.id,
            limit=limit,
            unread_only=unread_only
        )

        return {
            "notifications": [
                {
                    "id": n.id,
                    "type": n.notification_type,
                    "priority": n.priority,
                    "title": n.title,
                    "message": n.message,
                    "data": n.data,
                    "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                    "flight_number": n.flight_number,
                    "airport_code": n.airport_code
                }
                for n in notifications
            ],
            "count": len(notifications)
        }

    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get notification history"
        )


@notification_router.post("/test")
@limiter.limit("5/minute")
async def send_test_notification(
    request: Request,
    test_request: TestNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Send a test notification to verify setup.

    Allows users to test their notification configuration.

    Args:
        test_request: Test notification parameters
        current_user: Authenticated user
        db: Database session

    Returns:
        Status of test notification
    """
    try:
        notification = await notification_service.send_notification(
            db=db,
            user_id=current_user.id,
            notification_type=test_request.notification_type,
            title="Test Notification",
            message="This is a test notification from AirportWaze. If you see this, your notifications are working!",
            priority="low",
            data={"is_test": True}
        )

        if notification:
            return {
                "status": "success",
                "message": "Test notification sent",
                "notification_id": notification.id
            }
        else:
            return {
                "status": "skipped",
                "message": "Notification was skipped (check your preferences)"
            }

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send test notification"
        )


# Include both routers
def get_routers():
    """Get all AI feature routers."""
    return [router, notification_router]
