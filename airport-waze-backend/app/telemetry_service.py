"""
Telemetry processing service for learning from user-contributed data.
Implements Bayesian updates and k-anonymity protection.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import numpy as np
from scipy import stats
import logging

from app.models import (
    Checkpoint,
    CheckpointDistribution,
    WaitTimeObservation,
    TelemetrySession,
    TelemetryBatch
)

logger = logging.getLogger(__name__)

# K-anonymity threshold: minimum users required to use data
K_ANONYMITY_THRESHOLD = 10


class TelemetryProcessor:
    """
    Processes telemetry data and updates Bayesian wait time distributions.
    Implements hierarchical Bayesian learning: Global → Airport → Checkpoint
    """

    def __init__(self, db: Session):
        self.db = db

    def process_wait_time_observation(
        self,
        checkpoint_id: str,
        wait_time_minutes: int,
        confidence: float = 1.0,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Process a single wait time observation and update the distribution.

        Args:
            checkpoint_id: ID of the checkpoint
            wait_time_minutes: Observed wait time in minutes
            confidence: Confidence in the observation (0-1)
            context: Optional context (hour, day_of_week)

        Returns:
            True if observation was processed, False if rejected
        """
        # Validate checkpoint exists
        checkpoint = self.db.query(Checkpoint).filter(
            Checkpoint.id == checkpoint_id
        ).first()

        if not checkpoint:
            logger.warning(f"Checkpoint {checkpoint_id} not found")
            return False

        # Validate wait time is reasonable (1 min to 4 hours)
        if wait_time_minutes < 1 or wait_time_minutes > 240:
            logger.warning(f"Invalid wait time: {wait_time_minutes} minutes")
            return False

        # Get or create distribution for this checkpoint
        distribution = self.db.query(CheckpointDistribution).filter(
            CheckpointDistribution.checkpoint_id == checkpoint_id
        ).first()

        if not distribution:
            # Create new distribution from first observation
            mu = np.log(wait_time_minutes)
            sigma = self._get_default_sigma(checkpoint.type)

            distribution = CheckpointDistribution(
                checkpoint_id=checkpoint_id,
                mu=mu,
                sigma=sigma,
                sample_size=1,
                confidence="low",
                last_updated=datetime.utcnow()
            )
            self.db.add(distribution)
        else:
            # Update distribution using Bayesian inference
            self._update_distribution_bayesian(
                distribution,
                wait_time_minutes,
                confidence
            )

        self.db.commit()
        logger.info(f"Updated distribution for {checkpoint_id}: μ={distribution.mu:.2f}, σ={distribution.sigma:.2f}, n={distribution.sample_size}")
        return True

    def _update_distribution_bayesian(
        self,
        distribution: CheckpointDistribution,
        new_wait_time: int,
        confidence: float
    ):
        """
        Update distribution parameters using Bayesian inference.
        Uses online update formula for log-normal parameters.
        """
        # Current parameters
        mu = distribution.mu
        sigma = distribution.sigma
        n = distribution.sample_size

        # New observation (log-transformed)
        log_wait = np.log(new_wait_time)

        # Weighted update (confidence acts as weight for the estimate)
        # But sample count always increases by 1
        weight = confidence
        n_new = n + 1  # Each observation adds 1 to sample count
        n_effective = n + weight  # Effective sample for weighted average

        # Update mu (weighted average)
        mu_new = (n * mu + weight * log_wait) / n_effective if n_effective > 0 else log_wait

        # Update sigma (incremental variance update)
        delta = log_wait - mu
        sigma_squared = sigma ** 2
        sigma_squared_new = (n * sigma_squared + weight * delta * (log_wait - mu_new)) / n_effective

        # Apply smoothing to prevent sigma from going to zero
        sigma_squared_new = max(sigma_squared_new, 0.01)

        # Update distribution
        distribution.mu = mu_new
        distribution.sigma = np.sqrt(sigma_squared_new)
        distribution.sample_size = n_new  # Use actual observation count
        distribution.last_updated = datetime.utcnow()

        # Update confidence level based on sample size
        if distribution.sample_size >= 100:
            distribution.confidence = "high"
        elif distribution.sample_size >= 30:
            distribution.confidence = "medium"
        else:
            distribution.confidence = "low"

    def _get_default_sigma(self, checkpoint_type: str) -> float:
        """Get default sigma value based on checkpoint type"""
        sigma_defaults = {
            "tsa_precheck": 0.25,  # Very predictable
            "tsa": 0.40,            # Moderate variation
            "bag_check": 0.50,      # Higher variation
            "passport_control": 0.45,
            "customs": 0.50
        }
        return sigma_defaults.get(checkpoint_type, 0.45)

    def check_k_anonymity(
        self,
        airport_code: str,
        time_window_hours: int = 24
    ) -> Tuple[bool, int]:
        """
        Check if k-anonymity threshold is met for an airport.

        Args:
            airport_code: Airport code to check
            time_window_hours: Time window to check (default 24 hours)

        Returns:
            Tuple of (meets_threshold, unique_session_count)
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        unique_sessions = self.db.query(TelemetrySession).filter(
            TelemetrySession.airport_code == airport_code,
            TelemetrySession.created_at >= cutoff_time
        ).distinct(TelemetrySession.session_id).count()

        meets_threshold = unique_sessions >= K_ANONYMITY_THRESHOLD

        return meets_threshold, unique_sessions

    def get_telemetry_stats(
        self,
        airport_code: str,
        time_window_hours: int = 24
    ) -> Optional[Dict]:
        """
        Get aggregated telemetry statistics for an airport.
        Returns None if k-anonymity threshold not met.

        Args:
            airport_code: Airport code
            time_window_hours: Time window for statistics

        Returns:
            Statistics dict or None if insufficient data
        """
        meets_threshold, session_count = self.check_k_anonymity(
            airport_code,
            time_window_hours
        )

        if not meets_threshold:
            return None

        # Get total telemetry points collected
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        total_points = 0
        checkpoint_counts = {}

        # Count telemetry batches for this airport in the time window
        batches = self.db.query(TelemetryBatch).filter(
            TelemetryBatch.airport_code == airport_code,
            TelemetryBatch.uploaded_at >= cutoff_time
        ).all()

        for batch in batches:
            if batch.points:
                total_points += len(batch.points) if isinstance(batch.points, list) else 0

        # Count checkpoint observations (from all sources)
        from app.models import Checkpoint
        checkpoints = self.db.query(Checkpoint).filter(
            Checkpoint.airport_code == airport_code
        ).all()

        for checkpoint in checkpoints:
            dist = self.db.query(CheckpointDistribution).filter(
                CheckpointDistribution.checkpoint_id == checkpoint.id
            ).first()
            if dist and dist.sample_size > 0:
                checkpoint_counts[checkpoint.id] = dist.sample_size

        # Determine coverage quality
        total_observations = sum(checkpoint_counts.values())
        if session_count >= 100:
            coverage_quality = "excellent"
        elif session_count >= 50:
            coverage_quality = "good"
        elif session_count >= K_ANONYMITY_THRESHOLD:
            coverage_quality = "limited"
        else:
            coverage_quality = "insufficient"

        return {
            "airport_code": airport_code,
            "active_sessions_24h": session_count,
            "total_observations": total_observations,
            "coverage_quality": coverage_quality,
            "last_updated": datetime.utcnow().isoformat(),
            "checkpoint_coverage": checkpoint_counts
        }

    def aggregate_observations_hourly(
        self,
        checkpoint_id: str,
        hours_back: int = 24
    ) -> List[Dict]:
        """
        Aggregate observations by hour for a checkpoint.
        Useful for time-of-day analysis.

        Args:
            checkpoint_id: Checkpoint to aggregate
            hours_back: How many hours back to aggregate

        Returns:
            List of hourly aggregates
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        observations = self.db.query(WaitTimeObservation).filter(
            WaitTimeObservation.checkpoint_id == checkpoint_id,
            WaitTimeObservation.observed_at >= cutoff_time
        ).all()

        # Group by hour
        hourly_data = {}
        for obs in observations:
            hour = obs.observed_at.hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(obs.wait_time_minutes)

        # Calculate statistics for each hour
        hourly_stats = []
        for hour in sorted(hourly_data.keys()):
            wait_times = hourly_data[hour]
            if len(wait_times) >= 3:  # Minimum sample size
                hourly_stats.append({
                    "hour": hour,
                    "count": len(wait_times),
                    "mean": np.mean(wait_times),
                    "median": np.median(wait_times),
                    "std": np.std(wait_times),
                    "p80": np.percentile(wait_times, 80),
                    "p90": np.percentile(wait_times, 90)
                })

        return hourly_stats
