"""
Zone Discovery Algorithm using DBSCAN Clustering.

This implements automatic discovery of checkpoint locations from user telemetry data.
No need for manual mapping - the algorithm learns where bottlenecks are by observing
where users slow down and wait.

Algorithm:
1. Filter telemetry points inside airport boundary
2. Identify "dwell points" where users were stationary (speed < 0.3 m/s for > 45 seconds)
3. Cluster dwell points using DBSCAN (density-based clustering)
4. Label clusters using weak signals (dwell duration, time ordering, POI names)
5. Output discovered zones with confidence scores
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Optional, Tuple
import logging
import math

from app.models import TelemetryBatch, Checkpoint
from app.database import SessionLocal

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula."""
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


class ZoneDiscovery:
    """
    Automatic zone discovery from telemetry data.
    """

    def __init__(self, airport_code: str, airport_lat: float, airport_lng: float):
        self.airport_code = airport_code.upper()
        self.airport_lat = airport_lat
        self.airport_lng = airport_lng

        # Parameters
        self.airport_radius_meters = 3000  # Consider points within 3km of airport center
        self.min_dwell_seconds = 45  # Minimum time to be considered "dwelling"
        self.dbscan_epsilon_meters = 25  # Cluster radius (25 meters)
        self.dbscan_min_samples = 30  # Minimum points to form a cluster
        self.min_speed_threshold = 0.3  # m/s (about 1 km/h) to be considered stationary

    def discover_zones(
        self,
        db: Session,
        lookback_days: int = 30,
        min_confidence: float = 0.5
    ) -> List[Dict]:
        """
        Discover checkpoint zones from telemetry data.

        Args:
            db: Database session
            lookback_days: How many days of data to use
            min_confidence: Minimum confidence score to include zone

        Returns:
            List of discovered zones with metadata
        """
        logger.info(f"Starting zone discovery for {self.airport_code}")

        # Step 1: Load telemetry data
        telemetry_points = self._load_telemetry_points(db, lookback_days)

        if len(telemetry_points) < 100:
            logger.warning(f"Insufficient telemetry data for {self.airport_code}: {len(telemetry_points)} points")
            return []

        logger.info(f"Loaded {len(telemetry_points)} telemetry points")

        # Step 2: Identify dwell points
        dwell_points = self._identify_dwell_points(telemetry_points)

        if len(dwell_points) < self.dbscan_min_samples:
            logger.warning(f"Insufficient dwell points for {self.airport_code}: {len(dwell_points)} dwells")
            return []

        logger.info(f"Identified {len(dwell_points)} dwell points")

        # Step 3: Cluster using DBSCAN
        zones = self._cluster_dwell_points(dwell_points)

        logger.info(f"Discovered {len(zones)} zones")

        # Step 4: Filter by confidence
        high_confidence_zones = [z for z in zones if z["confidence"] >= min_confidence]

        logger.info(f"Filtered to {len(high_confidence_zones)} high-confidence zones")

        return high_confidence_zones

    def _load_telemetry_points(self, db: Session, lookback_days: int) -> List[Dict]:
        """
        Load telemetry points from database, filtered by airport and time.
        """
        cutoff_time = datetime.utcnow() - timedelta(days=lookback_days)

        batches = db.query(TelemetryBatch).filter(
            TelemetryBatch.airport_code == self.airport_code,
            TelemetryBatch.uploaded_at >= cutoff_time
        ).all()

        all_points = []

        for batch in batches:
            # batch.points is JSONB array
            points = batch.points if isinstance(batch.points, list) else []

            for point in points:
                # Check if point is inside airport boundary
                if self._is_inside_airport(point["lat"], point["lng"]):
                    all_points.append({
                        "lat": point["lat"],
                        "lng": point["lng"],
                        "speed": point.get("speed"),
                        "timestamp": point["timestamp"],
                        "session_id": str(batch.session_id)
                    })

        return all_points

    def _is_inside_airport(self, lat: float, lng: float) -> bool:
        """Check if point is within airport boundary (circular geofence)."""
        distance = haversine_distance(self.airport_lat, self.airport_lng, lat, lng)
        return distance <= self.airport_radius_meters

    def _identify_dwell_points(self, points: List[Dict]) -> List[Dict]:
        """
        Identify points where user was stationary for extended period.

        A dwell point is a location where:
        - User had low speed (< 0.3 m/s) for at least 45 seconds
        - Stayed within 50m radius during dwell
        """
        # Sort by session and timestamp
        sorted_points = sorted(points, key=lambda p: (p["session_id"], p["timestamp"]))

        dwell_points = []

        i = 0
        while i < len(sorted_points):
            point = sorted_points[i]

            # Check if speed is low
            if point.get("speed") is not None and point["speed"] >= self.min_speed_threshold:
                i += 1
                continue

            # Find how long user stayed in this area
            j = i + 1
            while j < len(sorted_points):
                next_point = sorted_points[j]

                # Must be same session
                if next_point["session_id"] != point["session_id"]:
                    break

                # Check if still in same area (< 50m away)
                distance = haversine_distance(
                    point["lat"], point["lng"],
                    next_point["lat"], next_point["lng"]
                )

                if distance > 50:
                    break

                j += 1

            # Calculate dwell duration
            if j > i + 1:
                try:
                    start_time = datetime.fromisoformat(sorted_points[i]["timestamp"].replace('Z', ''))
                    end_time = datetime.fromisoformat(sorted_points[j-1]["timestamp"].replace('Z', ''))
                    duration = (end_time - start_time).total_seconds()

                    if duration >= self.min_dwell_seconds:
                        # This is a valid dwell point
                        dwell_points.append({
                            "lat": point["lat"],
                            "lng": point["lng"],
                            "dwell_duration": duration,
                            "timestamp": point["timestamp"],
                            "session_id": point["session_id"]
                        })

                except (ValueError, TypeError):
                    pass

            i = max(i + 1, j)

        return dwell_points

    def _cluster_dwell_points(self, dwell_points: List[Dict]) -> List[Dict]:
        """
        Cluster dwell points using DBSCAN to identify zones.
        """
        if len(dwell_points) < self.dbscan_min_samples:
            return []

        # Extract coordinates
        coords = np.array([[p["lat"], p["lng"]] for p in dwell_points])

        # Convert coordinates to radians for haversine metric
        coords_radians = np.radians(coords)

        # DBSCAN epsilon in radians (25 meters / Earth radius)
        epsilon_radians = self.dbscan_epsilon_meters / 6371000

        # Run DBSCAN clustering
        clustering = DBSCAN(
            eps=epsilon_radians,
            min_samples=self.dbscan_min_samples,
            metric='haversine'
        ).fit(coords_radians)

        labels = clustering.labels_

        # Build zone objects from clusters
        zones = []
        for label in set(labels):
            if label == -1:  # Noise
                continue

            # Get all points in this cluster
            cluster_indices = np.where(labels == label)[0]
            cluster_points = [dwell_points[i] for i in cluster_indices]

            # Calculate zone metadata
            zone = self._build_zone_metadata(label, cluster_points)

            zones.append(zone)

        return zones

    def _build_zone_metadata(self, cluster_id: int, cluster_points: List[Dict]) -> Dict:
        """
        Build metadata for discovered zone.
        """
        # Centroid
        lats = [p["lat"] for p in cluster_points]
        lngs = [p["lng"] for p in cluster_points]
        centroid_lat = np.mean(lats)
        centroid_lng = np.mean(lngs)

        # Dwell duration statistics
        durations = [p["dwell_duration"] for p in cluster_points]
        median_duration = np.median(durations)
        mean_duration = np.mean(durations)
        std_duration = np.std(durations)

        # Infer zone type from dwell duration patterns
        zone_type = self._infer_zone_type(median_duration, mean_duration, std_duration)

        # Calculate confidence score
        confidence = self._calculate_confidence(cluster_points, lats, lngs)

        # Unique sessions (how many different users visited)
        unique_sessions = len(set(p["session_id"] for p in cluster_points))

        return {
            "zone_id": f"{self.airport_code}_discovered_{cluster_id}",
            "lat": centroid_lat,
            "lng": centroid_lng,
            "zone_type": zone_type,
            "sample_size": len(cluster_points),
            "unique_visitors": unique_sessions,
            "median_dwell_seconds": int(median_duration),
            "mean_dwell_seconds": int(mean_duration),
            "std_dwell_seconds": int(std_duration),
            "confidence": confidence,
            "discovered_at": datetime.utcnow().isoformat()
        }

    def _infer_zone_type(
        self,
        median_duration: float,
        mean_duration: float,
        std_duration: float
    ) -> str:
        """
        Infer zone type from dwell duration patterns.

        Heuristics:
        - Bag check: 1-3 minutes (60-180s), low variance
        - TSA security: 3-15 minutes (180-900s), moderate variance
        - TSA PreCheck: < 3 minutes (< 180s), very low variance
        - Passport control: 5-20 minutes (300-1200s), high variance
        - Waiting area/gate: > 20 minutes (> 1200s)
        """
        if median_duration < 120:
            # Very short dwell: likely bag check or PreCheck
            if std_duration < 30:
                return "tsa_precheck"
            else:
                return "bag_check"

        elif median_duration < 600:
            # 2-10 minutes: likely regular TSA security
            return "tsa"

        elif median_duration < 1200:
            # 10-20 minutes: likely passport control
            return "passport_control"

        else:
            # Very long dwell: waiting area or gate
            return "waiting_area"

    def _calculate_confidence(
        self,
        cluster_points: List[Dict],
        lats: List[float],
        lngs: List[float]
    ) -> float:
        """
        Calculate confidence score for discovered zone.

        Factors:
        - Sample size (more points = higher confidence)
        - Temporal diversity (observations spread across different times)
        - Spatial tightness (lower variance = higher confidence)
        - Unique visitors (more unique users = higher confidence)
        """
        sample_size = len(cluster_points)

        # Factor 1: Sample size score (0-1)
        size_score = min(sample_size / 100, 1.0)

        # Factor 2: Temporal diversity (how many different hours represented)
        hours = set()
        for point in cluster_points:
            try:
                timestamp = datetime.fromisoformat(point["timestamp"].replace('Z', ''))
                hours.add(timestamp.hour)
            except (ValueError, TypeError):
                pass

        temporal_score = len(hours) / 24  # Fraction of hours covered

        # Factor 3: Spatial tightness (inverse of standard deviation)
        lat_std = np.std(lats)
        lng_std = np.std(lngs)
        spatial_variance = lat_std + lng_std
        spatial_score = 1 / (1 + spatial_variance * 10000)  # Normalize

        # Factor 4: Unique visitors
        unique_sessions = len(set(p["session_id"] for p in cluster_points))
        visitor_score = min(unique_sessions / 20, 1.0)

        # Weighted combination
        confidence = (
            size_score * 0.3 +
            temporal_score * 0.2 +
            spatial_score * 0.3 +
            visitor_score * 0.2
        )

        return round(confidence, 2)


def run_zone_discovery(airport_code: str, lookback_days: int = 30) -> Dict:
    """
    Standalone function to run zone discovery for an airport.
    Can be called from a cron job or API endpoint.
    """
    db = SessionLocal()
    try:
        # Get airport metadata
        from app.models import Checkpoint

        existing_checkpoint = db.query(Checkpoint).filter(
            Checkpoint.airport_code == airport_code.upper()
        ).first()

        if not existing_checkpoint:
            return {
                "status": "error",
                "message": f"Airport {airport_code} not found in database"
            }

        # Use first checkpoint's location as airport center
        # (In production, store airport center separately)
        airport_lat = existing_checkpoint.lat
        airport_lng = existing_checkpoint.lng

        # Run discovery
        discovery = ZoneDiscovery(airport_code, airport_lat, airport_lng)
        zones = discovery.discover_zones(db, lookback_days)

        logger.info(f"Discovered {len(zones)} zones for {airport_code}")

        return {
            "status": "success",
            "airport_code": airport_code,
            "zones_discovered": len(zones),
            "zones": zones
        }

    except Exception as e:
        logger.error(f"Zone discovery failed for {airport_code}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        db.close()
