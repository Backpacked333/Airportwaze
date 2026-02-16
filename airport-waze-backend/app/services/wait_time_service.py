"""Wait time service for crowdsourced reports."""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.wait_time_report import WaitTimeReport as WaitTimeReportModel
from app.schemas.wait_time import WaitTimeReport, WaitTimeDistribution
from app.data import AIRPORTS_DATA
from app.utils.calculations import get_wait_time_distribution

logger = logging.getLogger(__name__)


class WaitTimeService:
    """Service for wait time operations."""

    @staticmethod
    def create_report(db: Session, report: WaitTimeReport, user_id: Optional[int] = None) -> WaitTimeReportModel:
        """Create a new wait time report."""
        db_report = WaitTimeReportModel(
            airport_code=report.airport_code.upper(),
            checkpoint_id=report.checkpoint_id,
            reported_wait_minutes=report.reported_wait_minutes,
            reporter_id=report.reporter_id,
            user_id=user_id,
            user_lat=report.user_lat,
            user_lng=report.user_lng
        )

        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        logger.info(f"Created wait time report for {report.airport_code}-{report.checkpoint_id}")
        return db_report

    @staticmethod
    def get_recent_reports(
        db: Session,
        airport_code: str,
        limit: int = 20,
        hours_back: int = 24
    ) -> List[Dict]:
        """Get recent wait time reports for an airport."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        reports = db.query(WaitTimeReportModel).filter(
            WaitTimeReportModel.airport_code == airport_code.upper(),
            WaitTimeReportModel.created_at >= cutoff_time
        ).order_by(
            WaitTimeReportModel.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "airport_code": r.airport_code,
                "checkpoint_id": r.checkpoint_id,
                "reported_wait_minutes": r.reported_wait_minutes,
                "timestamp": r.created_at.isoformat(),
                "user_lat": r.user_lat,
                "user_lng": r.user_lng
            }
            for r in reports
        ]

    @staticmethod
    def get_checkpoint_distribution(checkpoint_id: str) -> Optional[Dict]:
        """Get wait time distribution for a checkpoint."""
        # Find checkpoint across all airports
        for airport_code, airport_data in AIRPORTS_DATA.items():
            for cp in airport_data["checkpoints"]:
                if cp["id"] == checkpoint_id:
                    distribution = get_wait_time_distribution(cp["base_wait"], cp["type"])
                    return {
                        "checkpoint_id": checkpoint_id,
                        "checkpoint_name": cp["name"],
                        "checkpoint_type": cp["type"],
                        "terminal": cp["terminal"],
                        "airport_code": airport_code,
                        "distribution": distribution
                    }

        logger.warning(f"Checkpoint not found: {checkpoint_id}")
        return None

    @staticmethod
    def cleanup_old_reports(db: Session, days_old: int = 30) -> int:
        """Delete reports older than specified days."""
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)

        deleted = db.query(WaitTimeReportModel).filter(
            WaitTimeReportModel.created_at < cutoff_time
        ).delete()

        db.commit()
        logger.info(f"Deleted {deleted} old wait time reports")
        return deleted
