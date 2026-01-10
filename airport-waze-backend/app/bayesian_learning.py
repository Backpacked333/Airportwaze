"""
Hierarchical Bayesian Wait Time Learning Model.

This implements the Moovit-style learning approach where:
- Global priors are learned from all airports
- Airport-level priors are learned from all checkpoints at that airport
- Checkpoint-level distributions borrow strength from airport-level when data is sparse

This approach gracefully handles sparse data by falling back to higher-level priors.
"""

import numpy as np
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Optional, Tuple
import logging

from app.models import WaitTimeObservation, Checkpoint, CheckpointDistribution
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class HierarchicalWaitTimeModel:
    """
    Hierarchical Bayesian model for wait times.

    Structure:
    - Level 0 (Global): All airports worldwide
    - Level 1 (Airport): Each airport has its own distribution
    - Level 2 (Checkpoint): Each checkpoint within airport

    Uses log-normal distributions (positive-valued, right-skewed).
    """

    def __init__(self):
        # Global hyperparameters (learned from all airports)
        self.global_mu = 3.0  # log(20 minutes) ≈ 3.0
        self.global_sigma = 0.5
        self.global_tau = 1.0  # Precision of global prior

        # Airport-level parameters
        self.airport_params: Dict[str, Dict] = {}

        # Checkpoint-level parameters (loaded from database)
        self.checkpoint_params: Dict[str, Dict] = {}

    def load_from_database(self, db: Session):
        """Load existing learned parameters from database."""
        distributions = db.query(CheckpointDistribution).all()

        for dist in distributions:
            self.checkpoint_params[dist.checkpoint_id] = {
                "mu": dist.mu,
                "sigma": dist.sigma,
                "sample_size": dist.sample_size,
                "confidence": dist.confidence,
                "last_updated": dist.last_updated
            }

        logger.info(f"Loaded {len(self.checkpoint_params)} checkpoint distributions")

    def update_all_checkpoints(self, db: Session, lookback_days: int = 30):
        """
        Update all checkpoint distributions based on recent observations.
        This should be run periodically (e.g., nightly batch job).

        Args:
            db: Database session
            lookback_days: How many days of data to use for learning
        """
        cutoff_time = datetime.utcnow() - timedelta(days=lookback_days)

        # First, update airport-level parameters
        self._update_airport_level(db, cutoff_time)

        # Then, update each checkpoint
        checkpoints = db.query(Checkpoint).all()
        updates_count = 0

        for checkpoint in checkpoints:
            success = self._update_checkpoint(db, checkpoint, cutoff_time)
            if success:
                updates_count += 1

        logger.info(f"Updated {updates_count}/{len(checkpoints)} checkpoints")

        return updates_count

    def _update_airport_level(self, db: Session, cutoff_time: datetime):
        """
        Update airport-level parameters based on all checkpoints.
        """
        from sqlalchemy import select

        # Get all airports with observations
        airport_codes = db.query(Checkpoint.airport_code).distinct().all()

        for (airport_code,) in airport_codes:
            # Get all observations for this airport
            observations = db.query(WaitTimeObservation.wait_minutes).join(
                WaitTimeObservation.checkpoint
            ).filter(
                WaitTimeObservation.checkpoint.has(airport_code=airport_code),
                WaitTimeObservation.observed_at >= cutoff_time,
                WaitTimeObservation.wait_minutes > 0
            ).all()

            if len(observations) < 10:
                # Not enough data, use global prior
                self.airport_params[airport_code] = {
                    "mu": self.global_mu,
                    "sigma": self.global_sigma,
                    "sample_size": 0
                }
                continue

            # Calculate airport-level distribution
            wait_times = [obs[0] for obs in observations]
            log_wait_times = np.log(wait_times)

            mu = np.mean(log_wait_times)
            sigma = np.std(log_wait_times)

            self.airport_params[airport_code] = {
                "mu": mu,
                "sigma": sigma,
                "sample_size": len(observations)
            }

            logger.debug(f"Airport {airport_code}: mu={mu:.3f}, sigma={sigma:.3f}, n={len(observations)}")

    def _update_checkpoint(
        self,
        db: Session,
        checkpoint: Checkpoint,
        cutoff_time: datetime
    ) -> bool:
        """
        Update a single checkpoint's distribution using Bayesian updating.

        Returns:
            True if update was successful, False otherwise
        """
        # Get observations for this checkpoint
        observations = db.query(WaitTimeObservation.wait_minutes).filter(
            WaitTimeObservation.checkpoint_id == checkpoint.id,
            WaitTimeObservation.observed_at >= cutoff_time,
            WaitTimeObservation.wait_minutes > 0
        ).all()

        n = len(observations)

        if n < 5:
            # Not enough data, use airport-level prior
            airport_prior = self.airport_params.get(checkpoint.airport_code)

            if not airport_prior or airport_prior["sample_size"] < 10:
                # Airport also has insufficient data, use global
                mu = self.global_mu
                sigma = self.global_sigma
                confidence = "low"
            else:
                mu = airport_prior["mu"]
                sigma = airport_prior["sigma"]
                confidence = "low"

        else:
            # Enough data for Bayesian update
            wait_times = [obs[0] for obs in observations]
            mu, sigma, confidence = self._bayesian_update(
                wait_times,
                checkpoint.airport_code,
                n
            )

        # Save to database
        existing = db.query(CheckpointDistribution).filter(
            CheckpointDistribution.checkpoint_id == checkpoint.id
        ).first()

        if existing:
            existing.mu = mu
            existing.sigma = sigma
            existing.sample_size = n
            existing.confidence = confidence
            existing.last_updated = datetime.utcnow()
        else:
            new_dist = CheckpointDistribution(
                checkpoint_id=checkpoint.id,
                mu=mu,
                sigma=sigma,
                sample_size=n,
                confidence=confidence
            )
            db.add(new_dist)

        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update checkpoint {checkpoint.id}: {e}")
            return False

    def _bayesian_update(
        self,
        wait_times: list,
        airport_code: str,
        n: int
    ) -> Tuple[float, float, str]:
        """
        Perform Bayesian update with conjugate priors.

        Uses Normal-Gamma conjugate prior for log-normal data.

        Args:
            wait_times: List of observed wait times (minutes)
            airport_code: Airport code for prior
            n: Number of observations

        Returns:
            (mu, sigma, confidence) tuple
        """
        # Calculate sample statistics in log space
        log_wait_times = np.log(wait_times)
        sample_mu = np.mean(log_wait_times)
        sample_sigma = np.std(log_wait_times)

        # Get prior from airport level (or global if airport insufficient)
        airport_prior = self.airport_params.get(airport_code)

        if airport_prior and airport_prior["sample_size"] >= 10:
            prior_mu = airport_prior["mu"]
            prior_sigma = airport_prior["sigma"]
        else:
            prior_mu = self.global_mu
            prior_sigma = self.global_sigma

        # Bayesian update formula (weighted average by precision)
        # Precision = 1 / variance

        # Prior precision (inverse variance)
        prior_precision = 1 / (prior_sigma ** 2)

        # Sample precision
        sample_precision = n / (sample_sigma ** 2)

        # Posterior mean (weighted average)
        posterior_mu = (
            (prior_precision * prior_mu + sample_precision * sample_mu) /
            (prior_precision + sample_precision)
        )

        # Posterior precision
        posterior_precision = prior_precision + sample_precision

        # Posterior standard deviation
        posterior_sigma = np.sqrt(1 / posterior_precision)

        # Determine confidence based on sample size and consistency
        if n >= 100:
            confidence = "high"
        elif n >= 30:
            confidence = "medium"
        else:
            confidence = "low"

        return posterior_mu, posterior_sigma, confidence

    def predict_wait_time_distribution(
        self,
        db: Session,
        checkpoint_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Get predicted wait time distribution for a checkpoint.

        Args:
            db: Database session
            checkpoint_id: Checkpoint ID
            context: Optional context (time-of-day, day-of-week, etc.)

        Returns:
            Distribution dict with percentiles and parameters
        """
        # Load distribution from database
        dist = db.query(CheckpointDistribution).filter(
            CheckpointDistribution.checkpoint_id == checkpoint_id
        ).first()

        if dist:
            mu = dist.mu
            sigma = dist.sigma
            confidence = dist.confidence
            sample_size = dist.sample_size
        else:
            # No learned distribution, use prior
            checkpoint = db.query(Checkpoint).filter(Checkpoint.id == checkpoint_id).first()

            if not checkpoint:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")

            airport_prior = self.airport_params.get(checkpoint.airport_code)

            if airport_prior and airport_prior["sample_size"] >= 10:
                mu = airport_prior["mu"]
                sigma = airport_prior["sigma"]
            else:
                mu = self.global_mu
                sigma = self.global_sigma

            confidence = "low"
            sample_size = 0

        # Apply context adjustments (time-of-day, day-of-week)
        if context:
            mu, sigma = self._apply_context_adjustment(mu, sigma, context)

        # Calculate percentiles
        p50 = int(np.exp(mu))
        p80 = int(np.exp(mu + sigma * stats.norm.ppf(0.80)))
        p90 = int(np.exp(mu + sigma * stats.norm.ppf(0.90)))
        p95 = int(np.exp(mu + sigma * stats.norm.ppf(0.95)))

        return {
            "p50": max(1, p50),
            "p80": max(1, p80),
            "p90": max(1, p90),
            "p95": max(1, p95),
            "mu": round(mu, 4),
            "sigma": round(sigma, 4),
            "sample_size": sample_size,
            "confidence": confidence
        }

    def _apply_context_adjustment(
        self,
        mu: float,
        sigma: float,
        context: Dict
    ) -> Tuple[float, float]:
        """
        Apply context-specific adjustments to base distribution.

        Context factors:
        - Time of day (peak hours vs off-peak)
        - Day of week (weekend vs weekday)
        - Seasonal effects (summer travel season)
        - Special events (holidays)
        """
        adjusted_mu = mu
        adjusted_sigma = sigma

        # Time of day adjustment
        if "hour" in context:
            hour = context["hour"]
            if 6 <= hour <= 9 or 16 <= hour <= 20:
                # Peak hours: increase mean by 40%
                adjusted_mu += np.log(1.4)
            elif 22 <= hour or hour <= 5:
                # Late night: decrease mean by 40%
                adjusted_mu -= np.log(1.4)

        # Day of week adjustment
        if "day_of_week" in context:
            day = context["day_of_week"]  # 0=Monday, 6=Sunday
            if day in [4, 5, 6]:  # Friday, Saturday, Sunday
                # Weekend: increase mean by 20%
                adjusted_mu += np.log(1.2)

        # Increase variance for peak times (less predictable)
        if "is_peak" in context and context["is_peak"]:
            adjusted_sigma *= 1.2

        return adjusted_mu, adjusted_sigma


def run_learning_update(lookback_days: int = 30):
    """
    Standalone function to run learning update.
    Can be called from a cron job or background worker.
    """
    db = SessionLocal()
    try:
        model = HierarchicalWaitTimeModel()
        model.load_from_database(db)

        updates_count = model.update_all_checkpoints(db, lookback_days)

        logger.info(f"Learning update complete: {updates_count} checkpoints updated")

        return {"status": "success", "updates": updates_count}

    except Exception as e:
        logger.error(f"Learning update failed: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
