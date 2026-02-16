"""Wait time related Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional


class WaitTimeReport(BaseModel):
    """Schema for wait time report submission."""
    airport_code: str
    checkpoint_id: str
    reported_wait_minutes: int
    reporter_id: Optional[str] = None
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None


class WaitTimeDistribution(BaseModel):
    """Probabilistic wait time using log-normal distribution."""
    p50: int  # median (50th percentile)
    p80: int  # 80th percentile
    p90: int  # 90th percentile
    p95: int  # 95th percentile
    mu: float  # log-normal mu parameter
    sigma: float  # log-normal sigma parameter
    sample_size: int  # number of observations
    confidence: str  # "high", "medium", "low" based on data quality
