"""Prediction service for probabilistic flight predictions."""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import numpy as np

from app.data import AIRPORTS_DATA, get_gate_position
from app.schemas.flight import (
    WillIMakeItRequest,
    WillIMakeItResponse,
    SegmentDistribution
)
from app.utils.calculations import (
    calculate_walking_time,
    get_wait_time_distribution,
    run_monte_carlo_simulation,
    calculate_probability_of_making_it,
    get_status_from_probability,
    get_time_multiplier
)

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for flight prediction and wait time forecasting."""

    @staticmethod
    def will_i_make_it(request: WillIMakeItRequest) -> Optional[WillIMakeItResponse]:
        """
        Calculate the probability of making your flight using Monte Carlo simulation.

        Args:
            request: Will I make it request with flight details and user preferences

        Returns:
            WillIMakeItResponse with probability and leave-by times, or None if airport not found
        """
        airport_code = request.flight.airport_code.upper()
        airport_data = AIRPORTS_DATA.get(airport_code)

        if not airport_data:
            logger.warning(f"Airport not found: {airport_code}")
            return None

        # Parse departure time
        try:
            departure_time = datetime.fromisoformat(
                request.flight.departure_time.replace('Z', '+00:00')
            )
            if departure_time.tzinfo:
                departure_time = departure_time.replace(tzinfo=None)
        except ValueError:
            logger.error(f"Invalid departure time: {request.flight.departure_time}")
            return None

        # Parse current time (or use now)
        if request.current_time:
            try:
                current_time = datetime.fromisoformat(
                    request.current_time.replace('Z', '+00:00')
                )
                if current_time.tzinfo:
                    current_time = current_time.replace(tzinfo=None)
            except ValueError:
                current_time = datetime.utcnow()
        else:
            current_time = datetime.utcnow()

        # Determine boarding cutoff time
        has_passport_control = any(
            cp["type"] == "passport_control"
            for cp in airport_data["checkpoints"]
            if cp["terminal"] == request.flight.terminal
        )
        boarding_cutoff_minutes = 30 if has_passport_control else 15

        # Calculate time until boarding closes
        boarding_time = departure_time - timedelta(minutes=boarding_cutoff_minutes)
        time_until_boarding = (boarding_time - current_time).total_seconds() / 60

        # Build journey segments with distributions
        segments = []

        # Determine starting position
        if request.user_lat and request.user_lng:
            current_lat, current_lng = request.user_lat, request.user_lng
        else:
            current_lat, current_lng = airport_data["lat"], airport_data["lng"]

        # Segment 1: Bag Check (if applicable)
        if request.has_checked_bags:
            bag_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] == "bag_check" and cp["terminal"] == request.flight.terminal
            ]

            if bag_checkpoints:
                cp = bag_checkpoints[0]
                walk_time, walk_dist = calculate_walking_time(
                    current_lat, current_lng, cp["lat"], cp["lng"],
                    request.mobility_factor
                )
                wait_dist = get_wait_time_distribution(cp["base_wait"], cp["type"])

                segments.append({
                    "step_name": "Bag Check-In",
                    "location": cp["name"],
                    "lat": cp["lat"],
                    "lng": cp["lng"],
                    "wait_distribution": wait_dist,
                    "walk_minutes": walk_time,
                    "walk_distance_meters": walk_dist,
                    "checkpoint_id": cp["id"],
                    "mobility_factor": request.mobility_factor
                })
                current_lat, current_lng = cp["lat"], cp["lng"]

        # Segment 2: Security
        if request.has_tsa_precheck:
            security_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] == "tsa_precheck" and cp["terminal"] == request.flight.terminal
            ]
        else:
            security_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] == "tsa" and cp["terminal"] == request.flight.terminal
            ]

        # Fallback to any security checkpoint
        if not security_checkpoints:
            security_checkpoints = [
                cp for cp in airport_data["checkpoints"]
                if cp["type"] in ["tsa", "tsa_precheck"] and cp["terminal"] == request.flight.terminal
            ]

        if security_checkpoints:
            # Choose checkpoint with lowest base wait
            cp = min(security_checkpoints, key=lambda x: x["base_wait"])
            walk_time, walk_dist = calculate_walking_time(
                current_lat, current_lng, cp["lat"], cp["lng"],
                request.mobility_factor
            )
            wait_dist = get_wait_time_distribution(cp["base_wait"], cp["type"])

            step_name = "Security (PreCheck)" if request.has_tsa_precheck else "Security Screening"
            segments.append({
                "step_name": step_name,
                "location": cp["name"],
                "lat": cp["lat"],
                "lng": cp["lng"],
                "wait_distribution": wait_dist,
                "walk_minutes": walk_time,
                "walk_distance_meters": walk_dist,
                "checkpoint_id": cp["id"],
                "mobility_factor": request.mobility_factor
            })
            current_lat, current_lng = cp["lat"], cp["lng"]

        # Segment 3: Walk to Gate
        gate_lat, gate_lng = get_gate_position(
            airport_code, request.flight.terminal, request.flight.gate
        )
        walk_time, walk_dist = calculate_walking_time(
            current_lat, current_lng, gate_lat, gate_lng,
            request.mobility_factor
        )

        segments.append({
            "step_name": "Walk to Gate",
            "location": f"Gate {request.flight.gate}",
            "lat": gate_lat,
            "lng": gate_lng,
            "wait_distribution": None,
            "walk_minutes": walk_time,
            "walk_distance_meters": walk_dist,
            "checkpoint_id": None,
            "mobility_factor": request.mobility_factor
        })

        # Run Monte Carlo simulation
        num_simulations = 10000
        total_times, _ = run_monte_carlo_simulation(segments, num_simulations)

        # Calculate percentiles
        p50 = int(np.percentile(total_times, 50))
        p80 = int(np.percentile(total_times, 80))
        p90 = int(np.percentile(total_times, 90))
        p95 = int(np.percentile(total_times, 95))

        # Calculate probability of making it
        probability = calculate_probability_of_making_it(total_times, time_until_boarding)
        status, status_message = get_status_from_probability(probability)

        # Calculate leave-by times for different confidence levels
        leave_by_80 = boarding_time - timedelta(minutes=p80)
        leave_by_90 = boarding_time - timedelta(minutes=p90)
        leave_by_95 = boarding_time - timedelta(minutes=p95)

        # Build segment distributions for response
        response_segments = []
        for seg in segments:
            wait_dist = seg.get("wait_distribution")
            response_segments.append(SegmentDistribution(
                step_name=seg["step_name"],
                location=seg["location"],
                lat=seg["lat"],
                lng=seg["lng"],
                wait_distribution=wait_dist,
                walk_minutes=seg["walk_minutes"],
                walk_distance_meters=seg["walk_distance_meters"],
                checkpoint_id=seg.get("checkpoint_id")
            ))

        return WillIMakeItResponse(
            probability_of_making_it=round(probability, 4),
            probability_percentage=int(probability * 100),
            status=status,
            status_message=status_message,
            total_time_p50=p50,
            total_time_p80=p80,
            total_time_p90=p90,
            total_time_p95=p95,
            time_until_boarding=max(0, int(time_until_boarding)),
            buffer_minutes=boarding_cutoff_minutes,
            leave_by_80=leave_by_80.isoformat(),
            leave_by_90=leave_by_90.isoformat(),
            leave_by_95=leave_by_95.isoformat(),
            segments=response_segments,
            simulation_runs=num_simulations,
            boarding_cutoff_minutes=boarding_cutoff_minutes
        )

    @staticmethod
    def get_predictions(airport_code: str, hours_ahead: int = 24) -> Optional[Dict]:
        """
        Get wait time predictions for the next 24-48 hours.

        Args:
            airport_code: Airport code (e.g., "JFK")
            hours_ahead: Number of hours to predict (default 24, max 48)

        Returns:
            Dictionary with predictions, or None if airport not found
        """
        airport_code = airport_code.upper()
        airport_data = AIRPORTS_DATA.get(airport_code)

        if not airport_data:
            logger.warning(f"Airport not found: {airport_code}")
            return None

        predictions = []
        now = datetime.utcnow()

        # Generate predictions every 2 hours
        for hour_offset in range(0, min(hours_ahead, 48), 2):
            future_time = now + timedelta(hours=hour_offset)
            hour = future_time.hour
            day = future_time.weekday()

            # Calculate time multiplier for this specific time
            # Peak hours: morning (6-9) and evening (16-20)
            if 6 <= hour <= 9 or 16 <= hour <= 20:
                mult = 1.4
            # Off-peak hours: late night / early morning
            elif 22 <= hour or hour <= 5:
                mult = 0.6
            else:
                mult = 1.0

            # Weekend multiplier (Friday, Saturday, Sunday)
            if day in [4, 5, 6]:
                mult *= 1.2

            # Calculate predicted wait for each checkpoint
            checkpoint_predictions = []
            for cp in airport_data["checkpoints"]:
                predicted_wait = int(cp["base_wait"] * mult)
                checkpoint_predictions.append({
                    "checkpoint_id": cp["id"],
                    "checkpoint_name": cp["name"],
                    "lat": cp["lat"],
                    "lng": cp["lng"],
                    "predicted_wait_minutes": max(2, min(predicted_wait, 90))
                })

            predictions.append({
                "time": future_time.isoformat(),
                "checkpoints": checkpoint_predictions
            })

        return {
            "airport_code": airport_code,
            "predictions": predictions
        }
