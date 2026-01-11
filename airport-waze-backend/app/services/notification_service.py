"""
Smart Notification Service for AirportWaze.

Provides intelligent, context-aware notifications:
- Proactive alerts based on predictions
- Personalized timing and recommendations
- Gate changes and flight updates
- Smart reminders and suggestions
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import json

from app.models.notifications import (
    NotificationPreference,
    NotificationHistory,
    AlertRule,
    UserLearningProfile,
    NotificationType,
    NotificationPriority,
    NotificationChannel
)
from app.models.user import User
from app.services.predictive_ai_service import predictive_ai_service
from app.core.cache import cache_manager

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Smart notification service with personalization and context awareness.

    Features:
    - Proactive "leave now" alerts
    - Gate change detection
    - Security spike warnings
    - Personalized timing based on learned behavior
    - Smart reminders for travel documents
    """

    def __init__(self):
        self.cache = cache_manager
        self.ai_service = predictive_ai_service

    async def send_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        priority: str = "medium",
        data: Optional[Dict] = None,
        flight_number: Optional[str] = None,
        airport_code: Optional[str] = None
    ) -> Optional[NotificationHistory]:
        """
        Send a notification to a user.

        Args:
            db: Database session
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level
            data: Additional structured data
            flight_number: Related flight number
            airport_code: Related airport code

        Returns:
            NotificationHistory record or None if user doesn't want this notification
        """
        # Get user preferences
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        # Check if user wants this type of notification
        if not self._should_send_notification(prefs, notification_type):
            logger.info(f"User {user_id} has disabled {notification_type} notifications")
            return None

        # Check quiet hours
        if self._is_quiet_hours(prefs):
            if priority not in ["urgent", "high"]:
                logger.info(f"Skipping {notification_type} notification during quiet hours")
                return None

        # Determine channel
        channel = self._select_channel(prefs, priority)

        # Create notification history record
        notification = NotificationHistory(
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            channel=channel,
            title=title,
            message=message,
            data=data or {},
            flight_number=flight_number,
            airport_code=airport_code,
            sent_at=datetime.utcnow(),
            delivery_status="pending"
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Actually send the notification
        success = await self._deliver_notification(
            notification, prefs, channel
        )

        # Update delivery status
        if success:
            notification.delivery_status = "sent"
            notification.delivered_at = datetime.utcnow()
        else:
            notification.delivery_status = "failed"
            notification.error_message = "Delivery failed"

        db.commit()

        return notification

    def _should_send_notification(
        self,
        prefs: NotificationPreference,
        notification_type: str
    ) -> bool:
        """Check if user wants this type of notification."""
        type_map = {
            NotificationType.GATE_CHANGE: prefs.enable_gate_changes,
            NotificationType.FLIGHT_DELAY: prefs.enable_flight_delays,
            NotificationType.SECURITY_SPIKE: prefs.enable_security_alerts,
            NotificationType.LEAVE_NOW: prefs.enable_leave_now_alerts,
            NotificationType.BOARDING_ALERT: prefs.enable_boarding_alerts,
            NotificationType.ROUTE_SUGGESTION: prefs.enable_route_suggestions,
            NotificationType.WEATHER_DELAY: prefs.enable_weather_alerts,
            NotificationType.REMINDER: prefs.enable_reminders,
            NotificationType.PERSONALIZED_TIP: prefs.enable_personalized_tips,
        }

        return type_map.get(notification_type, True)

    def _is_quiet_hours(self, prefs: NotificationPreference) -> bool:
        """Check if currently in user's quiet hours."""
        if prefs.quiet_hours_start is None or prefs.quiet_hours_end is None:
            return False

        current_hour = datetime.utcnow().hour

        # Handle wrap-around (e.g., 22:00 to 07:00)
        if prefs.quiet_hours_start > prefs.quiet_hours_end:
            return current_hour >= prefs.quiet_hours_start or current_hour < prefs.quiet_hours_end
        else:
            return prefs.quiet_hours_start <= current_hour < prefs.quiet_hours_end

    def _select_channel(
        self,
        prefs: NotificationPreference,
        priority: str
    ) -> str:
        """Select the best channel for this notification."""
        # Urgent notifications always use push
        if priority == "urgent" and prefs.enable_push:
            return NotificationChannel.PUSH

        # Otherwise, use user's preferred channel
        if prefs.enable_push:
            return NotificationChannel.PUSH
        elif prefs.enable_in_app:
            return NotificationChannel.IN_APP
        elif prefs.enable_email:
            return NotificationChannel.EMAIL
        elif prefs.enable_sms:
            return NotificationChannel.SMS

        return NotificationChannel.IN_APP  # Fallback

    async def _deliver_notification(
        self,
        notification: NotificationHistory,
        prefs: NotificationPreference,
        channel: str
    ) -> bool:
        """
        Actually deliver the notification via the specified channel.

        In production, this would integrate with:
        - FCM/APNS for push notifications
        - SendGrid/AWS SES for email
        - Twilio for SMS
        """
        try:
            if channel == NotificationChannel.PUSH:
                return await self._send_push_notification(notification, prefs)
            elif channel == NotificationChannel.EMAIL:
                return await self._send_email_notification(notification)
            elif channel == NotificationChannel.SMS:
                return await self._send_sms_notification(notification)
            else:  # IN_APP
                # Store in cache for in-app retrieval
                cache_key = f"notifications:user:{notification.user_id}"
                await self.cache.set(
                    cache_key,
                    json.dumps({
                        "id": notification.id,
                        "title": notification.title,
                        "message": notification.message,
                        "data": notification.data
                    }),
                    expire=3600  # 1 hour
                )
                return True

        except Exception as e:
            logger.error(f"Error delivering notification: {e}")
            return False

    async def _send_push_notification(
        self,
        notification: NotificationHistory,
        prefs: NotificationPreference
    ) -> bool:
        """Send push notification via FCM/APNS."""
        if not prefs.push_tokens:
            logger.warning(f"No push tokens for user {notification.user_id}")
            return False

        # In production, integrate with FCM/APNS
        logger.info(f"Would send push to {len(prefs.push_tokens)} devices")
        return True

    async def _send_email_notification(
        self,
        notification: NotificationHistory
    ) -> bool:
        """Send email notification."""
        # In production, integrate with SendGrid/AWS SES
        logger.info(f"Would send email: {notification.title}")
        return True

    async def _send_sms_notification(
        self,
        notification: NotificationHistory
    ) -> bool:
        """Send SMS notification."""
        # In production, integrate with Twilio
        logger.info(f"Would send SMS: {notification.title}")
        return True

    async def check_and_send_proactive_alerts(
        self,
        db: Session,
        user_id: int,
        flight_info: Dict,
        current_location: Optional[Dict] = None
    ) -> List[NotificationHistory]:
        """
        Check if any proactive alerts should be sent for this user's flight.

        Args:
            db: Database session
            user_id: User ID
            flight_info: Flight information (airport, gate, departure time, etc.)
            current_location: User's current location (lat, lng)

        Returns:
            List of notifications sent
        """
        notifications_sent = []

        # Get user preferences for personalization
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)
            db.commit()

        # Get learning profile for personalized predictions
        learning_profile = db.query(UserLearningProfile).filter(
            UserLearningProfile.user_id == user_id
        ).first()

        # Check 1: "Leave now" alert
        leave_now_alert = await self._check_leave_now_alert(
            db, user_id, flight_info, prefs, learning_profile, current_location
        )
        if leave_now_alert:
            notifications_sent.append(leave_now_alert)

        # Check 2: Security spike alert
        security_alert = await self._check_security_spike(
            db, user_id, flight_info, prefs
        )
        if security_alert:
            notifications_sent.append(security_alert)

        # Check 3: Weather delay prediction
        weather_alert = await self._check_weather_delay(
            db, user_id, flight_info, prefs
        )
        if weather_alert:
            notifications_sent.append(weather_alert)

        # Check 4: Gate change (would integrate with flight status API)
        gate_change_alert = await self._check_gate_change(
            db, user_id, flight_info
        )
        if gate_change_alert:
            notifications_sent.append(gate_change_alert)

        # Check 5: Document reminders (passport, etc.)
        reminder = await self._check_document_reminders(
            db, user_id, flight_info
        )
        if reminder:
            notifications_sent.append(reminder)

        return notifications_sent

    async def _check_leave_now_alert(
        self,
        db: Session,
        user_id: int,
        flight_info: Dict,
        prefs: NotificationPreference,
        learning_profile: Optional[UserLearningProfile],
        current_location: Optional[Dict]
    ) -> Optional[NotificationHistory]:
        """
        Check if user should leave now to make their flight.

        Uses AI predictions and personalized timing.
        """
        try:
            departure_time = datetime.fromisoformat(
                flight_info["departure_time"].replace('Z', '+00:00')
            )
            if departure_time.tzinfo:
                departure_time = departure_time.replace(tzinfo=None)
        except (ValueError, KeyError):
            return None

        # Calculate when user should leave
        airport_code = flight_info.get("airport_code", "").upper()

        # Get advanced prediction for journey time
        # This would integrate with the predictive AI service
        journey_prediction = await self.ai_service.predict_wait_time_advanced(
            airport_code=airport_code,
            checkpoint_id=flight_info.get("checkpoint_id", "tsa_1"),
            target_time=departure_time
        )

        if not journey_prediction:
            return None

        # Use p90 confidence for safety
        predicted_time = journey_prediction["confidence_intervals"]["p90"]

        # Add user's preferred buffer
        buffer = prefs.preferred_buffer_minutes

        # Adjust for learned pace if available
        if learning_profile and learning_profile.learned_pace_multiplier:
            predicted_time *= learning_profile.learned_pace_multiplier

        # Calculate leave-by time
        total_time_needed = predicted_time + buffer
        leave_by_time = departure_time - timedelta(minutes=total_time_needed)

        # Check if we should send alert now
        time_until_leave = (leave_by_time - datetime.utcnow()).total_seconds() / 60

        # Send alert when user should leave in next 5-15 minutes
        if 5 <= time_until_leave <= 15:
            # Check if we haven't sent this alert recently
            recent_alert = db.query(NotificationHistory).filter(
                NotificationHistory.user_id == user_id,
                NotificationHistory.notification_type == NotificationType.LEAVE_NOW,
                NotificationHistory.flight_number == flight_info.get("flight_number"),
                NotificationHistory.sent_at >= datetime.utcnow() - timedelta(hours=1)
            ).first()

            if recent_alert:
                return None  # Already sent

            confidence = journey_prediction.get("confidence_score", 0.85)

            message = (
                f"Leave now to make your flight with {int(confidence * 100)}% confidence. "
                f"Current wait time at security: {predicted_time} minutes. "
                f"You have {int(time_until_leave)} minutes before optimal departure."
            )

            return await self.send_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.LEAVE_NOW,
                title=f"Time to head to {airport_code}!",
                message=message,
                priority=NotificationPriority.HIGH,
                data={
                    "leave_by": leave_by_time.isoformat(),
                    "predicted_time": predicted_time,
                    "confidence": confidence
                },
                flight_number=flight_info.get("flight_number"),
                airport_code=airport_code
            )

        return None

    async def _check_security_spike(
        self,
        db: Session,
        user_id: int,
        flight_info: Dict,
        prefs: NotificationPreference
    ) -> Optional[NotificationHistory]:
        """Check for sudden security line spikes."""
        airport_code = flight_info.get("airport_code", "").upper()
        checkpoint_id = flight_info.get("checkpoint_id", "tsa_1")

        # Get current prediction
        prediction = await self.ai_service.predict_wait_time_advanced(
            airport_code=airport_code,
            checkpoint_id=checkpoint_id,
            target_time=datetime.utcnow()
        )

        if not prediction:
            return None

        current_wait = prediction["predicted_wait_minutes"]

        # Check if wait time is significantly higher than normal
        # Get historical average from cache
        cache_key = f"avg_wait:{airport_code}:{checkpoint_id}"
        avg_wait_cached = await self.cache.get(cache_key)

        if avg_wait_cached:
            avg_wait = float(avg_wait_cached)
            # If current wait is 50% higher than average, alert
            if current_wait > avg_wait * 1.5:
                # Check if already alerted recently
                recent_alert = db.query(NotificationHistory).filter(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.notification_type == NotificationType.SECURITY_SPIKE,
                    NotificationHistory.sent_at >= datetime.utcnow() - timedelta(minutes=30)
                ).first()

                if recent_alert:
                    return None

                message = (
                    f"Security line just spiked to {current_wait} minutes "
                    f"(normally {int(avg_wait)} min). Consider using alternate checkpoint."
                )

                return await self.send_notification(
                    db=db,
                    user_id=user_id,
                    notification_type=NotificationType.SECURITY_SPIKE,
                    title="Security Line Alert",
                    message=message,
                    priority=NotificationPriority.HIGH,
                    data={
                        "current_wait": current_wait,
                        "normal_wait": int(avg_wait),
                        "checkpoint_id": checkpoint_id
                    },
                    airport_code=airport_code
                )

        return None

    async def _check_weather_delay(
        self,
        db: Session,
        user_id: int,
        flight_info: Dict,
        prefs: NotificationPreference
    ) -> Optional[NotificationHistory]:
        """Check for weather-related delay predictions."""
        airport_code = flight_info.get("airport_code", "").upper()

        try:
            departure_time = datetime.fromisoformat(
                flight_info["departure_time"].replace('Z', '+00:00')
            )
            if departure_time.tzinfo:
                departure_time = departure_time.replace(tzinfo=None)
        except (ValueError, KeyError):
            return None

        # Get weather impact prediction
        _, weather_impact = await self.ai_service._calculate_weather_impact(
            airport_code, departure_time
        )

        if weather_impact and weather_impact.get("delays_likely"):
            severity = weather_impact.get("severity_level", "medium")

            if severity in ["high", "severe"]:
                # Check if already alerted
                recent_alert = db.query(NotificationHistory).filter(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.notification_type == NotificationType.WEATHER_DELAY,
                    NotificationHistory.flight_number == flight_info.get("flight_number"),
                    NotificationHistory.sent_at >= datetime.utcnow() - timedelta(hours=6)
                ).first()

                if recent_alert:
                    return None

                condition = weather_impact.get("condition", "adverse weather")
                message = (
                    f"Your flight might be delayed due to {condition}. "
                    f"Check with your airline for updates. Consider arriving early."
                )

                return await self.send_notification(
                    db=db,
                    user_id=user_id,
                    notification_type=NotificationType.WEATHER_DELAY,
                    title="Possible Weather Delay",
                    message=message,
                    priority=NotificationPriority.MEDIUM,
                    data=weather_impact,
                    flight_number=flight_info.get("flight_number"),
                    airport_code=airport_code
                )

        return None

    async def _check_gate_change(
        self,
        db: Session,
        user_id: int,
        flight_info: Dict
    ) -> Optional[NotificationHistory]:
        """
        Check for gate changes.

        In production, would integrate with flight status APIs.
        """
        # Simulated gate change detection
        # In production: Check flight status API for gate changes
        # For now, return None (no gate change)
        return None

    async def _check_document_reminders(
        self,
        db: Session,
        user_id: int,
        flight_info: Dict
    ) -> Optional[NotificationHistory]:
        """Send reminders for travel documents."""
        is_international = flight_info.get("is_international", False)

        if not is_international:
            return None

        try:
            departure_time = datetime.fromisoformat(
                flight_info["departure_time"].replace('Z', '+00:00')
            )
            if departure_time.tzinfo:
                departure_time = departure_time.replace(tzinfo=None)
        except (ValueError, KeyError):
            return None

        # Send reminder 24 hours before international flight
        time_until_flight = (departure_time - datetime.utcnow()).total_seconds() / 3600

        if 23 <= time_until_flight <= 25:  # ~24 hours before
            # Check if already reminded
            recent_reminder = db.query(NotificationHistory).filter(
                NotificationHistory.user_id == user_id,
                NotificationHistory.notification_type == NotificationType.REMINDER,
                NotificationHistory.flight_number == flight_info.get("flight_number"),
                NotificationHistory.sent_at >= datetime.utcnow() - timedelta(hours=12)
            ).first()

            if recent_reminder:
                return None

            message = (
                "Don't forget your passport for your international flight! "
                "Also check visa requirements and vaccination records if needed."
            )

            return await self.send_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.REMINDER,
                title="Travel Document Reminder",
                message=message,
                priority=NotificationPriority.MEDIUM,
                data={"document_types": ["passport", "visa", "vaccination"]},
                flight_number=flight_info.get("flight_number"),
                airport_code=flight_info.get("airport_code")
            )

        return None

    async def register_push_token(
        self,
        db: Session,
        user_id: int,
        token: str,
        device_type: str
    ) -> bool:
        """
        Register a push notification token for a user.

        Args:
            db: Database session
            user_id: User ID
            token: Push notification token
            device_type: Device type (ios, android, web)

        Returns:
            Success status
        """
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)

        # Add token if not already present
        tokens = prefs.push_tokens or []
        token_entry = {"token": token, "device_type": device_type, "registered_at": datetime.utcnow().isoformat()}

        # Remove old entry for this token if exists
        tokens = [t for t in tokens if t.get("token") != token]
        tokens.append(token_entry)

        prefs.push_tokens = tokens
        db.commit()

        logger.info(f"Registered push token for user {user_id}")
        return True

    async def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[NotificationHistory]:
        """
        Get notification history for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of notifications to return
            unread_only: Only return unread notifications

        Returns:
            List of notification history records
        """
        query = db.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id
        )

        if unread_only:
            query = query.filter(NotificationHistory.read_at.is_(None))

        notifications = query.order_by(
            NotificationHistory.sent_at.desc()
        ).limit(limit).all()

        return notifications


# Global instance
notification_service = NotificationService()
