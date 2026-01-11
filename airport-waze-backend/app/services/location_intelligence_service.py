"""
Location Intelligence Service - Advanced geospatial analysis and checkpoint discovery.

This service implements:
- DBSCAN clustering for checkpoint discovery
- Dwell-time analysis to detect check-in counters
- Movement pattern recognition
- Airline-specific location mapping
- Heatmap generation
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict

from app.models.location_tracking import (
    LocationTrace,
    DiscoveredCheckpoint,
    AirlineCheckpointMapping
)
from app.schemas.location_tracking import (
    LocationTraceCreate,
    DiscoveredCheckpointResponse,
    AirlineCheckpointSuggestion,
    DwellTimeAnalysis,
    HeatmapResponse
)
from app.utils.calculations import haversine_distance

logger = logging.getLogger(__name__)


class LocationIntelligenceService:
    """Service for intelligent location analysis and checkpoint discovery."""

    @staticmethod
    def create_location_trace(db: Session, trace_data: LocationTraceCreate, user_id: Optional[int] = None) -> LocationTrace:
        """
        Create a location trace and analyze for stationary behavior.

        This automatically detects if the user is standing still by comparing
        with recent traces from the same session.
        """
        # Get recent traces from this session
        recent_traces = db.query(LocationTrace).filter(
            LocationTrace.session_id == trace_data.session_id,
            LocationTrace.timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ).order_by(LocationTrace.timestamp.desc()).limit(10).all()

        # Detect if user is stationary
        is_stationary = False
        activity_type = "moving"

        if len(recent_traces) >= 3:
            # Check if all recent locations are within 10 meters
            distances = [
                haversine_distance(trace_data.lat, trace_data.lng, t.lat, t.lng)
                for t in recent_traces[:3]
            ]
            if all(d < 10 for d in distances):  # Within 10 meters
                is_stationary = True
                activity_type = "standing"

                # If standing for a while, might be checking in
                if len(recent_traces) >= 5:
                    time_span = (recent_traces[0].timestamp - recent_traces[-1].timestamp).total_seconds()
                    if time_span > 120:  # Standing for 2+ minutes
                        activity_type = "check_in_likely"

        # Create trace
        db_trace = LocationTrace(
            user_id=user_id,
            session_id=trace_data.session_id,
            airport_code=trace_data.airport_code.upper(),
            airline=trace_data.airline,
            flight_number=trace_data.flight_number,
            terminal=trace_data.terminal,
            lat=trace_data.lat,
            lng=trace_data.lng,
            accuracy=trace_data.accuracy,
            speed=trace_data.speed,
            heading=trace_data.heading,
            is_stationary=is_stationary,
            activity_type=activity_type,
            timestamp=trace_data.timestamp or datetime.utcnow(),
            metadata=trace_data.metadata
        )

        db.add(db_trace)
        db.commit()
        db.refresh(db_trace)

        logger.info(f"Created location trace for {trace_data.airport_code} - {trace_data.airline} - {activity_type}")
        return db_trace

    @staticmethod
    def discover_checkpoints_dbscan(
        db: Session,
        airport_code: str,
        airline: Optional[str] = None,
        min_samples: int = 10,
        max_radius_meters: float = 50,
        hours_back: int = 168
    ) -> List[DiscoveredCheckpointResponse]:
        """
        Use DBSCAN clustering to discover checkpoints from stationary locations.

        This identifies areas where users frequently stand still (likely check-in counters,
        security lines, gates, etc.)

        Args:
            db: Database session
            airport_code: Airport to analyze
            airline: Filter by specific airline (None for all)
            min_samples: Minimum samples to form a cluster
            max_radius_meters: Maximum cluster radius in meters
            hours_back: How far back to look for data

        Returns:
            List of discovered checkpoints
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        # Query stationary traces
        query = db.query(LocationTrace).filter(
            LocationTrace.airport_code == airport_code.upper(),
            LocationTrace.is_stationary == True,
            LocationTrace.timestamp >= cutoff_time
        )

        if airline:
            query = query.filter(LocationTrace.airline == airline)

        traces = query.all()

        if len(traces) < min_samples:
            logger.warning(f"Not enough stationary traces for {airport_code}: {len(traces)}")
            return []

        # Prepare data for DBSCAN
        coordinates = np.array([[t.lat, t.lng] for t in traces])

        # Convert max_radius from meters to approximate degrees
        # At equator: 1 degree ≈ 111km, so we use this approximation
        epsilon = max_radius_meters / 111000  # Convert meters to degrees

        # Run DBSCAN clustering
        clustering = DBSCAN(eps=epsilon, min_samples=min_samples, metric='haversold').fit(coordinates)

        # Process clusters
        discovered = []
        labels = clustering.labels_
        unique_labels = set(labels)

        for label in unique_labels:
            if label == -1:  # Noise points
                continue

            # Get all traces in this cluster
            cluster_mask = labels == label
            cluster_traces = [t for t, mask in zip(traces, cluster_mask) if mask]

            if len(cluster_traces) < min_samples:
                continue

            # Calculate cluster centroid
            cluster_lats = [t.lat for t in cluster_traces]
            cluster_lngs = [t.lng for t in cluster_traces]
            center_lat = np.mean(cluster_lats)
            center_lng = np.mean(cluster_lngs)

            # Calculate cluster radius (max distance from centroid)
            distances = [
                haversine_distance(center_lat, center_lng, t.lat, t.lng)
                for t in cluster_traces
            ]
            radius_meters = max(distances)

            # Calculate average dwell time
            session_dwell_times = {}
            for trace in cluster_traces:
                if trace.session_id not in session_dwell_times:
                    session_dwell_times[trace.session_id] = []
                session_dwell_times[trace.session_id].append(trace.timestamp)

            dwell_times = []
            for session_id, timestamps in session_dwell_times.items():
                if len(timestamps) >= 2:
                    timestamps_sorted = sorted(timestamps)
                    duration = (timestamps_sorted[-1] - timestamps_sorted[0]).total_seconds()
                    dwell_times.append(duration)

            avg_dwell_time = int(np.mean(dwell_times)) if dwell_times else None

            # Classify checkpoint type based on dwell time and airline presence
            checkpoint_type = LocationIntelligenceService._classify_checkpoint_type(
                avg_dwell_time, airline, cluster_traces
            )

            # Calculate confidence score
            confidence = LocationIntelligenceService._calculate_confidence(
                len(cluster_traces), radius_meters, avg_dwell_time
            )

            # Determine terminal from most common terminal in cluster
            terminals = [t.terminal for t in cluster_traces if t.terminal]
            terminal = max(set(terminals), key=terminals.count) if terminals else None

            # Check if checkpoint already exists
            existing = db.query(DiscoveredCheckpoint).filter(
                DiscoveredCheckpoint.airport_code == airport_code.upper(),
                DiscoveredCheckpoint.checkpoint_type == checkpoint_type,
                func.sqrt(
                    func.pow(DiscoveredCheckpoint.center_lat - center_lat, 2) +
                    func.pow(DiscoveredCheckpoint.center_lng - center_lng, 2)
                ) < 0.001  # ~100 meters
            ).first()

            if existing:
                # Update existing
                existing.center_lat = center_lat
                existing.center_lng = center_lng
                existing.radius_meters = radius_meters
                existing.sample_size = len(cluster_traces)
                existing.avg_dwell_time_seconds = avg_dwell_time
                existing.confidence_score = confidence
                existing.last_updated = datetime.utcnow()
                checkpoint = existing
            else:
                # Create new
                checkpoint = DiscoveredCheckpoint(
                    airport_code=airport_code.upper(),
                    terminal=terminal,
                    center_lat=center_lat,
                    center_lng=center_lng,
                    radius_meters=radius_meters,
                    checkpoint_type=checkpoint_type,
                    airline=airline,
                    confidence_score=confidence,
                    sample_size=len(cluster_traces),
                    avg_dwell_time_seconds=avg_dwell_time,
                    cluster_data={
                        "epsilon": epsilon,
                        "min_samples": min_samples,
                        "label": int(label)
                    }
                )
                db.add(checkpoint)

            discovered.append(checkpoint)

        db.commit()

        logger.info(f"Discovered {len(discovered)} checkpoints for {airport_code}")

        return [
            DiscoveredCheckpointResponse.from_orm(cp) for cp in discovered
        ]

    @staticmethod
    def _classify_checkpoint_type(
        avg_dwell_time: Optional[int],
        airline: Optional[str],
        traces: List[LocationTrace]
    ) -> str:
        """Classify checkpoint type based on behavior patterns."""
        if not avg_dwell_time:
            return "unknown"

        # Check if most traces have activity_type hints
        activity_types = [t.activity_type for t in traces if t.activity_type]
        if activity_types:
            most_common = max(set(activity_types), key=activity_types.count)
            if "check_in" in most_common:
                return "airline_checkin"

        # Classify based on dwell time
        if avg_dwell_time > 300:  # 5+ minutes
            if airline:
                return "airline_checkin"  # Airline-specific check-in
            return "service_counter"
        elif avg_dwell_time > 120:  # 2-5 minutes
            return "security_queue"
        elif avg_dwell_time > 60:  # 1-2 minutes
            return "gate_waiting"
        else:
            return "general_waiting"

    @staticmethod
    def _calculate_confidence(sample_size: int, radius_meters: float, avg_dwell_time: Optional[int]) -> float:
        """Calculate confidence score for discovered checkpoint."""
        confidence = 0.0

        # Sample size contribution (0-0.4)
        if sample_size >= 100:
            confidence += 0.4
        elif sample_size >= 50:
            confidence += 0.3
        elif sample_size >= 20:
            confidence += 0.2
        else:
            confidence += 0.1

        # Radius contribution (0-0.3) - tighter clusters are better
        if radius_meters < 10:
            confidence += 0.3
        elif radius_meters < 20:
            confidence += 0.2
        elif radius_meters < 50:
            confidence += 0.1

        # Dwell time contribution (0-0.3) - reasonable dwell times are better
        if avg_dwell_time:
            if 60 <= avg_dwell_time <= 600:  # 1-10 minutes is reasonable
                confidence += 0.3
            elif 30 <= avg_dwell_time <= 1200:  # 30s-20min is acceptable
                confidence += 0.2
            else:
                confidence += 0.1

        return min(confidence, 1.0)

    @staticmethod
    def generate_airline_checkpoint_suggestions(
        db: Session,
        airport_code: str,
        min_confidence: float = 0.5
    ) -> List[AirlineCheckpointSuggestion]:
        """
        Generate suggestions for airline check-in counter locations based on user behavior.

        This analyzes where users with specific airlines spend time standing still.
        """
        # Get all traces with airline info from last 7 days
        cutoff_time = datetime.utcnow() - timedelta(days=7)

        traces = db.query(LocationTrace).filter(
            LocationTrace.airport_code == airport_code.upper(),
            LocationTrace.airline.isnot(None),
            LocationTrace.is_stationary == True,
            LocationTrace.activity_type.in_(["check_in_likely", "standing"]),
            LocationTrace.timestamp >= cutoff_time
        ).all()

        if not traces:
            return []

        # Group by airline
        airline_groups = defaultdict(list)
        for trace in traces:
            airline_groups[trace.airline].append(trace)

        suggestions = []

        for airline, airline_traces in airline_groups.items():
            if len(airline_traces) < 10:  # Need at least 10 samples
                continue

            # Run mini DBSCAN for this airline
            coordinates = np.array([[t.lat, t.lng] for t in airline_traces])
            epsilon = 30 / 111000  # 30 meters
            clustering = DBSCAN(eps=epsilon, min_samples=5, metric='haversine').fit(coordinates)

            labels = clustering.labels_
            unique_labels = set(labels)

            for label in unique_labels:
                if label == -1:
                    continue

                cluster_mask = labels == label
                cluster_traces = [t for t, mask in zip(airline_traces, cluster_mask) if mask]

                if len(cluster_traces) < 5:
                    continue

                # Calculate centroid
                center_lat = np.mean([t.lat for t in cluster_traces])
                center_lng = np.mean([t.lng for t in cluster_traces])

                # Calculate dwell time
                session_times = defaultdict(list)
                for trace in cluster_traces:
                    session_times[trace.session_id].append(trace.timestamp)

                dwell_times = []
                for timestamps in session_times.values():
                    if len(timestamps) >= 2:
                        duration = (max(timestamps) - min(timestamps)).total_seconds()
                        dwell_times.append(duration)

                avg_dwell = int(np.mean(dwell_times)) if dwell_times else 0

                # Calculate confidence
                confidence = LocationIntelligenceService._calculate_confidence(
                    len(cluster_traces), 30, avg_dwell
                )

                if confidence < min_confidence:
                    continue

                # Determine terminal
                terminals = [t.terminal for t in cluster_traces if t.terminal]
                terminal = max(set(terminals), key=terminals.count) if terminals else None

                suggestion = AirlineCheckpointSuggestion(
                    airline=airline,
                    airport_code=airport_code.upper(),
                    terminal=terminal,
                    suggested_lat=center_lat,
                    suggested_lng=center_lng,
                    confidence_score=confidence,
                    sample_size=len(cluster_traces),
                    avg_dwell_time_seconds=avg_dwell,
                    should_verify=confidence >= 0.7,
                    supporting_evidence={
                        "unique_sessions": len(session_times),
                        "time_range_hours": (
                            (max([t.timestamp for t in cluster_traces]) -
                             min([t.timestamp for t in cluster_traces])).total_seconds() / 3600
                        )
                    }
                )

                suggestions.append(suggestion)

        logger.info(f"Generated {len(suggestions)} airline checkpoint suggestions for {airport_code}")
        return suggestions

    @staticmethod
    def generate_heatmap_data(
        db: Session,
        airport_code: str,
        airline: Optional[str] = None,
        terminal: Optional[str] = None,
        hours_back: int = 24
    ) -> Dict:
        """
        Generate heatmap data for visualization.

        Returns density of location traces for heatmap rendering.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        query = db.query(LocationTrace).filter(
            LocationTrace.airport_code == airport_code.upper(),
            LocationTrace.timestamp >= cutoff_time
        )

        if airline:
            query = query.filter(LocationTrace.airline == airline)
        if terminal:
            query = query.filter(LocationTrace.terminal == terminal)

        traces = query.all()

        if not traces:
            return {
                "points": [],
                "clusters": [],
                "total_traces": 0
            }

        # Grid-based density calculation
        grid_size = 0.0001  # ~10 meters
        density_grid = defaultdict(int)

        for trace in traces:
            grid_lat = round(trace.lat / grid_size) * grid_size
            grid_lng = round(trace.lng / grid_size) * grid_size
            density_grid[(grid_lat, grid_lng)] += 1

        # Convert to heatmap points
        max_density = max(density_grid.values())
        points = [
            {
                "lat": lat,
                "lng": lng,
                "intensity": count / max_density,  # Normalized 0-1
                "count": count
            }
            for (lat, lng), count in density_grid.items()
            if count >= 3  # Filter out noise
        ]

        # Get discovered clusters
        clusters_query = db.query(DiscoveredCheckpoint).filter(
            DiscoveredCheckpoint.airport_code == airport_code.upper(),
            DiscoveredCheckpoint.is_active == True
        )

        if airline:
            clusters_query = clusters_query.filter(DiscoveredCheckpoint.airline == airline)

        clusters = [
            {
                "lat": c.center_lat,
                "lng": c.center_lng,
                "radius": c.radius_meters,
                "type": c.checkpoint_type,
                "airline": c.airline,
                "confidence": c.confidence_score
            }
            for c in clusters_query.all()
        ]

        return {
            "airport_code": airport_code,
            "points": points,
            "clusters": clusters,
            "total_traces": len(traces),
            "time_range": {
                "start": cutoff_time,
                "end": datetime.utcnow()
            }
        }
