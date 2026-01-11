"""Journey planning service."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.data import AIRPORTS_DATA, get_gate_position
from app.schemas.journey import JourneyRequest, JourneyPlan, JourneyStep
from app.utils.calculations import (
    calculate_current_wait,
    calculate_walking_time
)

logger = logging.getLogger(__name__)


class JourneyService:
    """Service for journey planning operations."""

    @staticmethod
    def plan_journey(request: JourneyRequest) -> Optional[JourneyPlan]:
        """
        Plan a journey through the airport from current location to gate.

        Args:
            request: Journey request with airport, terminal, gate, and user preferences

        Returns:
            JourneyPlan with steps and timing, or None if airport not found
        """
        airport_code = request.airport_code.upper()
        airport_data = AIRPORTS_DATA.get(airport_code)

        if not airport_data:
            logger.warning(f"Airport not found: {airport_code}")
            return None

        steps = []
        total_time = 0
        total_distance = 0

        # Determine starting position
        if request.user_lat and request.user_lng:
            current_lat, current_lng = request.user_lat, request.user_lng
        else:
            current_lat, current_lng = airport_data["lat"], airport_data["lng"]

        # Step 1: Bag Check (if needed)
        if request.has_checked_bags:
            bag_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] == "bag_check" and cp["terminal"] == request.terminal
            ]

            if bag_checkpoints:
                cp = bag_checkpoints[0]
                walk_time, walk_dist = calculate_walking_time(
                    current_lat, current_lng, cp["lat"], cp["lng"],
                    request.mobility_factor
                )
                wait_time = calculate_current_wait(cp["base_wait"])

                steps.append(JourneyStep(
                    step_name="Bag Check-In",
                    location=cp["name"],
                    lat=cp["lat"],
                    lng=cp["lng"],
                    estimated_wait_minutes=wait_time,
                    estimated_walk_minutes=walk_time,
                    distance_meters=walk_dist,
                    checkpoint_id=cp["id"]
                ))

                total_time += walk_time + wait_time
                total_distance += walk_dist
                current_lat, current_lng = cp["lat"], cp["lng"]

        # Step 2: Security Screening
        if request.has_tsa_precheck:
            security_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] == "tsa_precheck" and cp["terminal"] == request.terminal
            ]
        else:
            security_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] == "tsa" and cp["terminal"] == request.terminal
            ]

        # Fallback to any security checkpoint if specific type not found
        if not security_checkpoints:
            security_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] in ["tsa", "tsa_precheck"] and cp["terminal"] == request.terminal
            ]

        if security_checkpoints:
            # Choose checkpoint with lowest current wait
            cp = min(
                security_checkpoints,
                key=lambda x: calculate_current_wait(x["base_wait"])
            )

            walk_time, walk_dist = calculate_walking_time(
                current_lat, current_lng, cp["lat"], cp["lng"],
                request.mobility_factor
            )
            wait_time = calculate_current_wait(cp["base_wait"])

            step_name = "Security Screening"
            if request.has_tsa_precheck:
                step_name += " (PreCheck)"

            steps.append(JourneyStep(
                step_name=step_name,
                location=cp["name"],
                lat=cp["lat"],
                lng=cp["lng"],
                estimated_wait_minutes=wait_time,
                estimated_walk_minutes=walk_time,
                distance_meters=walk_dist,
                checkpoint_id=cp["id"]
            ))

            total_time += walk_time + wait_time
            total_distance += walk_dist
            current_lat, current_lng = cp["lat"], cp["lng"]

        # Step 3: Walk to Gate
        gate_lat, gate_lng = get_gate_position(
            airport_code, request.terminal, request.gate
        )
        walk_time, walk_dist = calculate_walking_time(
            current_lat, current_lng, gate_lat, gate_lng,
            request.mobility_factor
        )

        steps.append(JourneyStep(
            step_name="Walk to Gate",
            location=f"Gate {request.gate}",
            lat=gate_lat,
            lng=gate_lng,
            estimated_wait_minutes=0,
            estimated_walk_minutes=walk_time,
            distance_meters=walk_dist,
            checkpoint_id=None
        ))

        total_time += walk_time
        total_distance += walk_dist

        # Calculate buffer time (more for international flights)
        has_passport_control = any(
            cp["type"] == "passport_control"
            for cp in airport_data["checkpoints"]
            if cp["terminal"] == request.terminal
        )
        buffer = 30 if has_passport_control else 15

        # Calculate recommended arrival time
        if request.departure_time:
            try:
                departure = datetime.fromisoformat(
                    request.departure_time.replace('Z', '+00:00')
                )
            except ValueError:
                departure = datetime.utcnow() + timedelta(hours=3)
        else:
            departure = datetime.utcnow() + timedelta(hours=3)

        recommended_arrival = departure - timedelta(minutes=total_time + buffer)

        return JourneyPlan(
            total_time_minutes=total_time,
            total_distance_meters=total_distance,
            recommended_arrival_time=recommended_arrival.isoformat(),
            steps=steps,
            buffer_minutes=buffer
        )
