"""Utility functions for distance, time, and probabilistic calculations."""
import math
import random
import numpy as np
from scipy import stats
from datetime import datetime
from typing import Tuple

from app.schemas.wait_time import WaitTimeDistribution


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1, lng1: First point coordinates
        lat2, lng2: Second point coordinates

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_time_multiplier() -> float:
    """
    Get time-of-day and day-of-week multiplier for wait times.

    Returns:
        Multiplier based on current time and day
    """
    now = datetime.utcnow()
    hour = now.hour
    day = now.weekday()  # 0 = Monday, 6 = Sunday

    # Peak hours: morning (6-9) and evening (16-20)
    if 6 <= hour <= 9 or 16 <= hour <= 20:
        multiplier = 1.4
    # Off-peak hours: late night / early morning
    elif 22 <= hour or hour <= 5:
        multiplier = 0.6
    else:
        multiplier = 1.0

    # Weekend multiplier (Friday, Saturday, Sunday)
    if day in [4, 5, 6]:
        multiplier *= 1.2

    return multiplier


def calculate_current_wait(base_wait: int) -> int:
    """
    Calculate current wait time with time-of-day variation.

    Args:
        base_wait: Base wait time in minutes

    Returns:
        Current estimated wait time in minutes
    """
    multiplier = get_time_multiplier()
    variation = random.uniform(0.8, 1.2)
    return max(2, min(int(base_wait * multiplier * variation), 90))


def get_checkpoint_status(wait_minutes: int) -> str:
    """
    Get status label based on wait time.

    Args:
        wait_minutes: Wait time in minutes

    Returns:
        Status string: "low", "moderate", "high", or "very_high"
    """
    if wait_minutes <= 10:
        return "low"
    elif wait_minutes <= 25:
        return "moderate"
    elif wait_minutes <= 40:
        return "high"
    return "very_high"


def calculate_walking_time(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
    mobility_factor: float = 1.0
) -> Tuple[int, int]:
    """
    Calculate walking time and distance between two points.

    Args:
        lat1, lng1: Start point coordinates
        lat2, lng2: End point coordinates
        mobility_factor: Mobility factor (1.0 = normal, >1.0 = slower)

    Returns:
        Tuple of (walking_time_minutes, distance_meters)
    """
    distance = haversine_distance(lat1, lng1, lat2, lng2)
    walking_speed = 1.4 / mobility_factor  # meters per second
    time_seconds = distance / walking_speed
    return int(time_seconds / 60) + 1, int(distance)


def get_wait_time_distribution(
    base_wait: int,
    checkpoint_type: str
) -> WaitTimeDistribution:
    """
    Generate a log-normal wait time distribution for a checkpoint.

    Args:
        base_wait: Base wait time in minutes
        checkpoint_type: Type of checkpoint

    Returns:
        WaitTimeDistribution with percentiles and parameters
    """
    multiplier = get_time_multiplier()
    median_wait = max(2, base_wait * multiplier)

    # Sigma (variance) depends on checkpoint type
    sigma_map = {
        "bag_check": 0.5,       # High variance
        "tsa": 0.4,             # Moderate variance
        "tsa_precheck": 0.25,   # Low variance - more predictable
        "passport_control": 0.45,  # Moderate-high variance
    }
    sigma = sigma_map.get(checkpoint_type, 0.4)

    # For log-normal: if we want median = m, then mu = ln(m)
    mu = np.log(median_wait)

    # Calculate percentiles using log-normal distribution
    p50 = int(np.exp(mu))  # median
    p80 = int(np.exp(mu + sigma * stats.norm.ppf(0.80)))
    p90 = int(np.exp(mu + sigma * stats.norm.ppf(0.90)))
    p95 = int(np.exp(mu + sigma * stats.norm.ppf(0.95)))

    # Simulate sample size and confidence
    sample_size = random.randint(50, 500)
    if sample_size >= 200:
        confidence = "high"
    elif sample_size >= 100:
        confidence = "medium"
    else:
        confidence = "low"

    return WaitTimeDistribution(
        p50=max(1, p50),
        p80=max(1, p80),
        p90=max(1, p90),
        p95=max(1, p95),
        mu=round(mu, 4),
        sigma=round(sigma, 4),
        sample_size=sample_size,
        confidence=confidence
    )


def sample_wait_time(distribution: WaitTimeDistribution) -> float:
    """Sample a single wait time from the distribution for Monte Carlo simulation."""
    return max(1, np.random.lognormal(distribution.mu, distribution.sigma))


def sample_walking_time(base_minutes: int, mobility_factor: float = 1.0) -> float:
    """
    Sample walking time with variance.

    Args:
        base_minutes: Base walking time
        mobility_factor: Mobility factor

    Returns:
        Sampled walking time
    """
    mu = np.log(max(1, base_minutes))
    sigma = 0.15 * mobility_factor  # Slower walkers have more variance
    return max(0.5, np.random.lognormal(mu, sigma))


def run_monte_carlo_simulation(
    segments: list,
    num_simulations: int = 10000
) -> Tuple[np.ndarray, list]:
    """
    Run Monte Carlo simulation to get distribution of total journey times.

    Args:
        segments: List of journey segments with distributions
        num_simulations: Number of simulations to run

    Returns:
        Tuple of (total_times array, list of segment_times arrays)
    """
    total_times = np.zeros(num_simulations)
    segment_times = [np.zeros(num_simulations) for _ in segments]

    for i in range(num_simulations):
        total = 0
        for j, seg in enumerate(segments):
            # Sample wait time if there's a distribution
            if seg.get("wait_distribution"):
                wait = sample_wait_time(seg["wait_distribution"])
            else:
                wait = 0

            # Sample walking time
            walk = sample_walking_time(
                seg["walk_minutes"],
                seg.get("mobility_factor", 1.0)
            )

            segment_time = wait + walk
            segment_times[j][i] = segment_time
            total += segment_time

        total_times[i] = total

    return total_times, segment_times


def calculate_probability_of_making_it(
    total_times: np.ndarray,
    time_available: float
) -> float:
    """
    Calculate probability of making it given simulated total times.

    Args:
        total_times: Array of simulated total times
        time_available: Available time in minutes

    Returns:
        Probability (0.0 to 1.0)
    """
    return float(np.mean(total_times <= time_available))


def get_status_from_probability(prob: float) -> Tuple[str, str]:
    """
    Get status label and message from probability.

    Args:
        prob: Probability of making the flight (0.0 to 1.0)

    Returns:
        Tuple of (status, message)
    """
    if prob >= 0.95:
        return "safe", "You're in great shape! Plenty of time to spare."
    elif prob >= 0.80:
        return "good", "You should make it comfortably."
    elif prob >= 0.60:
        return "risky", "It's going to be close. Consider leaving soon."
    elif prob >= 0.40:
        return "unlikely", "High risk of missing your flight. Leave immediately!"
    else:
        return "very_unlikely", "Very high risk of missing your flight. You may need to rebook."
