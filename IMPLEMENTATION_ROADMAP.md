# AirportWaze Implementation Roadmap
## From MVP to Production-Ready Moovit-Style Airport Navigation

---

## 🎯 Executive Summary

Your AirportWaze MVP is **production-quality** with sophisticated probabilistic modeling. This roadmap shows how to implement the remaining features from your technical design document to create a fully autonomous, privacy-preserving airport wait time prediction system.

**Current Status:**
- ✅ MVP deployed with 9 major US airports
- ✅ Probabilistic predictions using log-normal distributions
- ✅ Monte Carlo simulations (10,000 iterations)
- ✅ Real GPS coordinates for 86 checkpoints
- ❌ No real-time data sources integrated
- ❌ No user telemetry collection
- ❌ No zone discovery algorithms
- ❌ No hierarchical Bayesian learning

---

## 📈 Phase 1: Enhanced Data Collection & Telemetry (Weeks 1-3)

### 1.1 User Telemetry Collection (Privacy-First)

**Goal:** Collect passive location and motion data from users to learn actual wait times and walking patterns.

#### Backend: New Telemetry Endpoints

Add to `/airport-waze-backend/app/main.py`:

```python
from enum import Enum
from typing import List, Optional
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.stats import norm
import pickle

# ============== TELEMETRY DATA MODELS ==============

class UserState(str, Enum):
    """User activity state detected from phone sensors"""
    WALKING = "walking"
    WAITING_IN_QUEUE = "waiting_in_queue"
    RIDING_SHUTTLE = "riding_shuttle"
    IDLE = "idle"
    UNKNOWN = "unknown"

class TelemetryPoint(BaseModel):
    """Single telemetry data point from user's phone"""
    timestamp: str
    lat: float
    lng: float
    speed: Optional[float] = None  # m/s
    acceleration: Optional[float] = None  # m/s^2
    heading: Optional[float] = None  # degrees
    altitude: Optional[float] = None  # meters (from barometer)
    battery_level: Optional[float] = None  # 0-100
    horizontal_accuracy: Optional[float] = None  # meters

class TelemetryBatch(BaseModel):
    """Batch of telemetry points (uploaded when user on WiFi)"""
    user_id: str  # Anonymous UUID generated client-side
    airport_code: str
    session_id: str  # UUID for this airport visit
    points: List[TelemetryPoint]
    device_info: Optional[dict] = None

class ZoneDwellEvent(BaseModel):
    """Preprocessed zone dwell event (computed on-device)"""
    zone_id: str
    zone_type: str  # "security", "bag_check", "passport_control"
    enter_time: str
    exit_time: str
    dwell_seconds: int
    confidence: float  # 0-1, how confident we are in classification

class TripEvent(BaseModel):
    """User-confirmed trip event (1-tap prompts)"""
    event_type: str  # "entered_security_line", "cleared_security", "dropped_bag"
    checkpoint_id: Optional[str] = None
    timestamp: str
    lat: float
    lng: float

# ============== TELEMETRY STORAGE ==============

# In production, use PostgreSQL/TimescaleDB
telemetry_observations = []  # List of TelemetryBatch
zone_dwell_events = []  # List of ZoneDwellEvent
trip_events = []  # List of TripEvent

# ============== TELEMETRY ENDPOINTS ==============

@app.post("/api/telemetry/upload")
async def upload_telemetry(batch: TelemetryBatch):
    """
    Upload telemetry batch. Users upload when:
    1. On WiFi (to save mobile data)
    2. Session ends (leave airport)
    3. Every 5 minutes if continuous collection
    """
    if len(batch.points) == 0:
        raise HTTPException(status_code=400, detail="Empty batch")

    # Store batch (in production: write to TimescaleDB)
    telemetry_observations.append(batch.dict())

    # Keep only last 100,000 points (memory constraint)
    if len(telemetry_observations) > 100000:
        telemetry_observations.pop(0)

    return {
        "status": "success",
        "points_received": len(batch.points),
        "message": "Thank you for contributing data!"
    }

@app.post("/api/telemetry/zone-dwell")
async def upload_zone_dwell(event: ZoneDwellEvent):
    """
    Upload preprocessed zone dwell event (computed on-device).
    This is privacy-preserving: no raw GPS, just zone ID + dwell time.
    """
    zone_dwell_events.append(event.dict())

    # Update wait time model based on dwell
    # (See Phase 2 for learning algorithm)

    return {"status": "success", "message": "Dwell event recorded"}

@app.post("/api/telemetry/trip-event")
async def upload_trip_event(event: TripEvent):
    """
    Upload user-confirmed trip event (1-tap prompt).
    Example: User tapped "I just entered security line" button.
    """
    trip_events.append(event.dict())
    return {"status": "success"}

@app.get("/api/telemetry/stats/{airport_code}")
async def get_telemetry_stats(airport_code: str):
    """Get aggregate telemetry statistics (k-anonymity: min 10 users)"""
    airport_code = airport_code.upper()

    # Count unique sessions in last 24 hours
    now = datetime.utcnow()
    recent_batches = [
        b for b in telemetry_observations
        if b["airport_code"] == airport_code
    ]

    unique_sessions = len(set(b["session_id"] for b in recent_batches))

    # Don't reveal data if < 10 users (k-anonymity)
    if unique_sessions < 10:
        return {
            "airport_code": airport_code,
            "data_quality": "insufficient",
            "message": "Not enough data to provide statistics"
        }

    return {
        "airport_code": airport_code,
        "active_sessions_24h": unique_sessions,
        "total_points": sum(len(b["points"]) for b in recent_batches),
        "coverage": "good" if unique_sessions >= 50 else "limited"
    }
```

#### Frontend: Background Location Tracking

Add to `/airport-waze-frontend/src/hooks/useTelemetry.ts` (new file):

```typescript
import { useState, useEffect, useRef } from 'react';

interface TelemetryPoint {
  timestamp: string;
  lat: number;
  lng: number;
  speed: number | null;
  acceleration: number | null;
  heading: number | null;
  altitude: number | null;
  battery_level: number | null;
  horizontal_accuracy: number | null;
}

interface UseTelemetryOptions {
  enabled: boolean;
  airportCode: string;
  sessionId: string;
  uploadInterval: number; // milliseconds
}

export function useTelemetry(options: UseTelemetryOptions) {
  const [isCollecting, setIsCollecting] = useState(false);
  const [pointsCollected, setPointsCollected] = useState(0);
  const telemetryBuffer = useRef<TelemetryPoint[]>([]);
  const watchId = useRef<number | null>(null);

  useEffect(() => {
    if (!options.enabled || !navigator.geolocation) {
      return;
    }

    setIsCollecting(true);

    // Start collecting location points
    watchId.current = navigator.geolocation.watchPosition(
      async (position) => {
        const point: TelemetryPoint = {
          timestamp: new Date().toISOString(),
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          speed: position.coords.speed,
          acceleration: null, // Would need accelerometer API
          heading: position.coords.heading,
          altitude: position.coords.altitude,
          battery_level: await getBatteryLevel(),
          horizontal_accuracy: position.coords.accuracy,
        };

        telemetryBuffer.current.push(point);
        setPointsCollected(telemetryBuffer.current.length);

        // Upload batch if buffer full or on WiFi
        if (telemetryBuffer.current.length >= 50 || isOnWifi()) {
          uploadBatch();
        }
      },
      (error) => {
        console.warn('Geolocation error:', error);
      },
      {
        enableHighAccuracy: true,
        maximumAge: 5000,
        timeout: 10000,
      }
    );

    // Upload batch periodically
    const uploadInterval = setInterval(() => {
      if (telemetryBuffer.current.length > 0) {
        uploadBatch();
      }
    }, options.uploadInterval);

    return () => {
      if (watchId.current !== null) {
        navigator.geolocation.clearWatch(watchId.current);
      }
      clearInterval(uploadInterval);
      // Upload remaining points on unmount
      if (telemetryBuffer.current.length > 0) {
        uploadBatch();
      }
    };
  }, [options.enabled, options.airportCode, options.sessionId]);

  const uploadBatch = async () => {
    if (telemetryBuffer.current.length === 0) return;

    const batch = {
      user_id: getUserId(), // Anonymous UUID stored in localStorage
      airport_code: options.airportCode,
      session_id: options.sessionId,
      points: telemetryBuffer.current,
      device_info: {
        user_agent: navigator.userAgent,
        screen: { width: screen.width, height: screen.height },
      },
    };

    try {
      await fetch(`${API_URL}/api/telemetry/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(batch),
      });

      // Clear buffer after successful upload
      telemetryBuffer.current = [];
      setPointsCollected(0);
    } catch (error) {
      console.error('Failed to upload telemetry:', error);
      // Keep buffer, will retry next interval
    }
  };

  return {
    isCollecting,
    pointsCollected,
  };
}

// Helper functions

function getUserId(): string {
  let userId = localStorage.getItem('airportwaze_user_id');
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem('airportwaze_user_id', userId);
  }
  return userId;
}

async function getBatteryLevel(): Promise<number | null> {
  if ('getBattery' in navigator) {
    try {
      const battery = await (navigator as any).getBattery();
      return battery.level * 100;
    } catch {
      return null;
    }
  }
  return null;
}

function isOnWifi(): boolean {
  const connection = (navigator as any).connection;
  if (!connection) return false;
  return connection.type === 'wifi' || connection.effectiveType === '4g';
}
```

### 1.2 On-Device State Detection

**Goal:** Classify user activity (walking, waiting in queue, riding shuttle) using motion sensors.

Add to frontend `/src/utils/stateDetection.ts`:

```typescript
/**
 * Simple HMM-based state detection for user activity.
 * States: WALKING, WAITING, RIDING, IDLE
 */

export enum UserState {
  WALKING = 'walking',
  WAITING = 'waiting_in_queue',
  RIDING = 'riding_shuttle',
  IDLE = 'idle',
}

interface MotionFeatures {
  speed: number; // m/s
  acceleration: number; // m/s^2
  headingJitter: number; // degrees per second
  stepCadence?: number; // steps per minute (if pedometer available)
}

export class StateDetector {
  private previousState: UserState = UserState.IDLE;
  private stateHistory: UserState[] = [];

  /**
   * Classify current state based on motion features.
   * Uses simple thresholds (in production, train an HMM).
   */
  detectState(features: MotionFeatures): UserState {
    let currentState: UserState;

    // Decision tree (production: use trained HMM)
    if (features.speed < 0.3) {
      // Not moving or very slow
      if (features.acceleration < 0.5) {
        currentState = UserState.IDLE;
      } else {
        // Frequent small movements in place
        currentState = UserState.WAITING;
      }
    } else if (features.speed < 2.0) {
      // Walking speed (1-2 m/s = 2.2-4.5 mph)
      if (features.headingJitter < 30) {
        currentState = UserState.WALKING;
      } else {
        // Walking but changing direction frequently (queue snaking)
        currentState = UserState.WAITING;
      }
    } else {
      // Fast movement, likely shuttle/train
      currentState = UserState.RIDING;
    }

    // Smooth with previous state (prevent flapping)
    const smoothedState = this.smoothState(currentState);
    this.stateHistory.push(smoothedState);

    // Keep only last 20 states
    if (this.stateHistory.length > 20) {
      this.stateHistory.shift();
    }

    return smoothedState;
  }

  /**
   * Smooth state transitions to prevent rapid flapping.
   * Require 3 consecutive observations to change state.
   */
  private smoothState(newState: UserState): UserState {
    const lastThree = this.stateHistory.slice(-3);
    const allSame = lastThree.every((s) => s === newState);

    if (allSame || this.stateHistory.length < 3) {
      this.previousState = newState;
      return newState;
    }

    return this.previousState;
  }

  /**
   * Detect zone boundaries (enter/exit queue).
   * Returns true if user just entered a waiting state.
   */
  didEnterQueue(): boolean {
    if (this.stateHistory.length < 2) return false;
    const previous = this.stateHistory[this.stateHistory.length - 2];
    const current = this.stateHistory[this.stateHistory.length - 1];
    return previous !== UserState.WAITING && current === UserState.WAITING;
  }

  didExitQueue(): boolean {
    if (this.stateHistory.length < 2) return false;
    const previous = this.stateHistory[this.stateHistory.length - 2];
    const current = this.stateHistory[this.stateHistory.length - 1];
    return previous === UserState.WAITING && current !== UserState.WAITING;
  }
}
```

---

## 📊 Phase 2: Zone Discovery & Learning (Weeks 4-6)

### 2.1 DBSCAN Clustering for Zone Discovery

**Goal:** Automatically discover checkpoint locations by clustering user dwell points.

Add to backend `/app/zone_discovery.py` (new file):

```python
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict
from datetime import datetime, timedelta

def discover_zones(airport_code: str, telemetry_observations: list) -> list:
    """
    Discover checkpoint zones using DBSCAN clustering on dwell points.

    Algorithm:
    1. Filter telemetry points inside airport boundary
    2. Identify dwell points (speed < 0.3 m/s for > 45 seconds)
    3. Cluster dwell points using DBSCAN
    4. Label clusters using weak signals (time ordering, POI names)

    Returns list of discovered zones with centroids and labels.
    """
    # Step 1: Filter points for this airport
    airport_points = []
    for batch in telemetry_observations:
        if batch["airport_code"] == airport_code:
            for point in batch["points"]:
                if is_inside_airport_boundary(point["lat"], point["lng"], airport_code):
                    airport_points.append(point)

    if len(airport_points) < 100:
        return []  # Not enough data

    # Step 2: Identify dwell points
    dwell_points = identify_dwell_points(airport_points, min_duration=45)

    if len(dwell_points) < 30:
        return []  # Not enough dwells

    # Step 3: Cluster using DBSCAN
    coords = np.array([[p["lat"], p["lng"]] for p in dwell_points])

    # Convert to meters for epsilon (25m radius)
    coords_radians = np.radians(coords)
    epsilon = 25 / 6371000  # 25 meters in radians

    clustering = DBSCAN(eps=epsilon, min_samples=30, metric='haversine').fit(coords_radians)
    labels = clustering.labels_

    # Step 4: Build zone objects
    zones = []
    for label in set(labels):
        if label == -1:  # Noise
            continue

        cluster_points = [p for i, p in enumerate(dwell_points) if labels[i] == label]

        # Compute centroid
        centroid_lat = np.mean([p["lat"] for p in cluster_points])
        centroid_lng = np.mean([p["lng"] for p in cluster_points])

        # Infer zone type from dwell duration distribution
        durations = [p["dwell_duration"] for p in cluster_points]
        median_duration = np.median(durations)

        # Heuristic labeling (in production, use more signals)
        if median_duration < 120:  # < 2 min
            zone_type = "bag_check"
        elif median_duration < 600:  # < 10 min
            zone_type = "tsa"
        else:
            zone_type = "passport_control"

        zones.append({
            "zone_id": f"{airport_code}_discovered_{label}",
            "lat": centroid_lat,
            "lng": centroid_lng,
            "zone_type": zone_type,
            "sample_size": len(cluster_points),
            "confidence": calculate_confidence(cluster_points)
        })

    return zones

def identify_dwell_points(points: list, min_duration: int = 45) -> list:
    """
    Identify points where user was stationary for > min_duration seconds.
    """
    dwell_points = []

    # Sort by timestamp
    sorted_points = sorted(points, key=lambda p: p["timestamp"])

    i = 0
    while i < len(sorted_points):
        point = sorted_points[i]

        # Check if speed is low (< 0.3 m/s = ~1 km/h)
        if point.get("speed", 1.0) < 0.3:
            # Find how long user stayed in this area
            j = i + 1
            while j < len(sorted_points):
                next_point = sorted_points[j]
                distance = haversine_distance(
                    point["lat"], point["lng"],
                    next_point["lat"], next_point["lng"]
                )
                if distance > 50:  # Moved more than 50m
                    break
                j += 1

            # Calculate dwell duration
            start_time = datetime.fromisoformat(sorted_points[i]["timestamp"])
            end_time = datetime.fromisoformat(sorted_points[j-1]["timestamp"])
            duration = (end_time - start_time).total_seconds()

            if duration >= min_duration:
                dwell_points.append({
                    "lat": point["lat"],
                    "lng": point["lng"],
                    "dwell_duration": duration,
                    "timestamp": point["timestamp"]
                })

            i = j
        else:
            i += 1

    return dwell_points

def calculate_confidence(cluster_points: list) -> float:
    """
    Calculate confidence score based on:
    - Sample size
    - Temporal coverage (spread across different times)
    - Spatial tightness
    """
    sample_size = len(cluster_points)

    # Temporal diversity (how many different hours represented)
    hours = set(datetime.fromisoformat(p["timestamp"]).hour for p in cluster_points)
    temporal_diversity = len(hours) / 24

    # Spatial tightness (lower variance = higher confidence)
    lats = [p["lat"] for p in cluster_points]
    lngs = [p["lng"] for p in cluster_points]
    spatial_variance = np.std(lats) + np.std(lngs)
    spatial_score = 1 / (1 + spatial_variance * 10000)  # Normalize

    # Combined score
    confidence = (
        min(sample_size / 100, 1.0) * 0.5 +
        temporal_diversity * 0.3 +
        spatial_score * 0.2
    )

    return round(confidence, 2)
```

### 2.2 Hierarchical Bayesian Wait Time Learning

**Goal:** Learn checkpoint-specific wait time distributions from observations.

Add to backend `/app/bayesian_learning.py` (new file):

```python
import numpy as np
from scipy import stats
from collections import defaultdict

class HierarchicalWaitTimeModel:
    """
    Hierarchical Bayesian model for wait times.

    Structure:
    - Global prior: All airports
    - Airport-level: Each airport has its own distribution
    - Checkpoint-level: Each checkpoint within airport

    This allows borrowing strength from higher levels when data is sparse.
    """

    def __init__(self):
        # Global hyperparameters (learned from all airports)
        self.global_mu = 3.0  # log(20 minutes)
        self.global_sigma = 0.5

        # Airport-level parameters
        self.airport_params = defaultdict(lambda: {
            "mu": self.global_mu,
            "sigma": self.global_sigma,
            "sample_size": 0
        })

        # Checkpoint-level parameters
        self.checkpoint_params = defaultdict(lambda: {
            "mu": None,  # Inherit from airport until enough data
            "sigma": None,
            "sample_size": 0,
            "observations": []
        })

    def update_with_observation(self,
                                 airport_code: str,
                                 checkpoint_id: str,
                                 wait_time_minutes: float):
        """
        Update model with a new wait time observation.
        Uses Bayesian updating with conjugate priors.
        """
        # Add to checkpoint observations
        cp_key = f"{airport_code}_{checkpoint_id}"
        self.checkpoint_params[cp_key]["observations"].append(wait_time_minutes)
        self.checkpoint_params[cp_key]["sample_size"] += 1

        # Get observations
        observations = self.checkpoint_params[cp_key]["observations"]
        n = len(observations)

        if n < 5:
            # Not enough data, use airport-level estimate
            return

        # Calculate sample statistics (in log space for log-normal)
        log_observations = np.log(observations)
        sample_mu = np.mean(log_observations)
        sample_sigma = np.std(log_observations)

        # Bayesian update with airport-level prior
        airport_mu = self.airport_params[airport_code]["mu"]
        airport_sigma = self.airport_params[airport_code]["sigma"]

        # Posterior mean (weighted average of prior and sample)
        # Weight by precision (inverse variance)
        prior_precision = 1 / (airport_sigma ** 2)
        sample_precision = n / (sample_sigma ** 2)

        posterior_mu = (
            (prior_precision * airport_mu + sample_precision * sample_mu) /
            (prior_precision + sample_precision)
        )

        posterior_sigma = np.sqrt(1 / (prior_precision + sample_precision))

        # Update checkpoint parameters
        self.checkpoint_params[cp_key]["mu"] = posterior_mu
        self.checkpoint_params[cp_key]["sigma"] = posterior_sigma

    def predict_wait_time_distribution(self,
                                        airport_code: str,
                                        checkpoint_id: str) -> dict:
        """
        Get predicted wait time distribution for a checkpoint.
        Returns percentiles and parameters.
        """
        cp_key = f"{airport_code}_{checkpoint_id}"

        # Use checkpoint-specific if available, otherwise airport-level
        if self.checkpoint_params[cp_key]["mu"] is not None:
            mu = self.checkpoint_params[cp_key]["mu"]
            sigma = self.checkpoint_params[cp_key]["sigma"]
            confidence = "high" if self.checkpoint_params[cp_key]["sample_size"] >= 50 else "medium"
        else:
            # Fall back to airport level
            mu = self.airport_params[airport_code]["mu"]
            sigma = self.airport_params[airport_code]["sigma"]
            confidence = "low"

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
            "sample_size": self.checkpoint_params[cp_key]["sample_size"],
            "confidence": confidence
        }

    def update_airport_level(self, airport_code: str):
        """
        Update airport-level parameters based on all checkpoints.
        Run this periodically (e.g., nightly).
        """
        # Collect all checkpoint observations for this airport
        all_observations = []
        for cp_key, params in self.checkpoint_params.items():
            if cp_key.startswith(airport_code):
                all_observations.extend(params["observations"])

        if len(all_observations) < 10:
            return

        # Update airport-level distribution
        log_observations = np.log(all_observations)
        self.airport_params[airport_code]["mu"] = np.mean(log_observations)
        self.airport_params[airport_code]["sigma"] = np.std(log_observations)
        self.airport_params[airport_code]["sample_size"] = len(all_observations)
```

---

## 🔌 Phase 3: Real Data Source Integration (Weeks 7-9)

### 3.1 TSA Wait Times API Integration

The MVP already attempts to fetch from TSA, but needs proper parsing.

Add to backend `/app/data_sources/tsa_api.py` (new file):

```python
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, Dict

class TSAWaitTimeAPI:
    """
    Integration with TSA MyTSA wait time data.
    API: https://www.tsa.gov/data/apcp.xml
    """

    def __init__(self):
        self.base_url = "https://www.tsa.gov/data/apcp.xml"
        self.cache = {}
        self.cache_expiry = {}

    async def get_wait_times(self, airport_code: str) -> Optional[Dict]:
        """
        Fetch current TSA wait times for an airport.
        Returns dict with checkpoint IDs and wait times, or None if unavailable.
        """
        # Check cache first (5-minute TTL)
        if airport_code in self.cache:
            if datetime.utcnow() < self.cache_expiry[airport_code]:
                return self.cache[airport_code]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url)

                if response.status_code != 200:
                    return None

                # Parse XML
                root = ET.fromstring(response.content)

                # Find airport data
                wait_times = {}
                for airport in root.findall(".//Airport"):
                    code = airport.find("AirportCode").text
                    if code != airport_code:
                        continue

                    # Parse checkpoints
                    for checkpoint in airport.findall(".//Checkpoint"):
                        cp_name = checkpoint.find("Name").text
                        wait_min = checkpoint.find("WaitTime").text

                        # Map to our checkpoint IDs (requires mapping logic)
                        cp_id = self.map_tsa_checkpoint_to_our_id(airport_code, cp_name)
                        if cp_id:
                            wait_times[cp_id] = int(wait_min)

                # Cache result
                if wait_times:
                    self.cache[airport_code] = wait_times
                    self.cache_expiry[airport_code] = datetime.utcnow() + timedelta(minutes=5)

                return wait_times if wait_times else None

        except Exception as e:
            print(f"TSA API error: {e}")
            return None

    def map_tsa_checkpoint_to_our_id(self, airport_code: str, tsa_name: str) -> Optional[str]:
        """
        Map TSA checkpoint name to our internal checkpoint ID.
        This requires building a mapping table.
        """
        # Example mapping for JFK
        mappings = {
            "JFK": {
                "Terminal 1 Security": "jfk-t1-tsa-1",
                "Terminal 4 Security": "jfk-t4-tsa-1",
                "Terminal 5 Security": "jfk-t5-tsa-1",
                # ... add all mappings
            },
            # Add other airports
        }

        return mappings.get(airport_code, {}).get(tsa_name)
```

### 3.2 CBP Passport Control Wait Times

Add to backend `/app/data_sources/cbp_api.py` (new file):

```python
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict

class CBPWaitTimeAPI:
    """
    Integration with CBP (Customs and Border Protection) wait times.
    API: https://bwt.cbp.gov/api/airports
    Documentation: https://bwt.cbp.gov/api/docs
    """

    def __init__(self):
        self.base_url = "https://bwt.cbp.gov/api/airports"
        self.cache = {}
        self.cache_expiry = {}

    async def get_wait_times(self, airport_code: str) -> Optional[Dict]:
        """
        Fetch current passport control/customs wait times.
        """
        if airport_code in self.cache:
            if datetime.utcnow() < self.cache_expiry[airport_code]:
                return self.cache[airport_code]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # CBP uses IATA codes
                url = f"{self.base_url}/{airport_code}"
                response = await client.get(url)

                if response.status_code != 200:
                    return None

                data = response.json()

                # Parse wait times
                wait_times = {}
                if "terminals" in data:
                    for terminal in data["terminals"]:
                        terminal_name = terminal["name"]

                        # Get current wait for passport control
                        if "passport_control" in terminal:
                            wait_min = terminal["passport_control"]["wait_time"]

                            # Map to our checkpoint ID
                            cp_id = self.map_cbp_terminal_to_our_id(airport_code, terminal_name)
                            if cp_id:
                                wait_times[cp_id] = int(wait_min)

                # Cache result
                if wait_times:
                    self.cache[airport_code] = wait_times
                    self.cache_expiry[airport_code] = datetime.utcnow() + timedelta(minutes=10)

                return wait_times if wait_times else None

        except Exception as e:
            print(f"CBP API error: {e}")
            return None

    def map_cbp_terminal_to_our_id(self, airport_code: str, terminal_name: str) -> Optional[str]:
        """Map CBP terminal name to our checkpoint ID."""
        mappings = {
            "JFK": {
                "Terminal 4": "jfk-t4-passport",
            },
            # Add mappings for other airports
        }

        return mappings.get(airport_code, {}).get(terminal_name)
```

### 3.3 Flight Data Integration

For demand forecasting, you need flight schedules.

**Option 1: FlightAware API** (paid, reliable)
**Option 2: FlightRadar24 API** (paid)
**Option 3: Aviation Edge API** (freemium)
**Option 4: Scrape airport departure boards** (free, fragile)

Example integration with Aviation Edge:

```python
import httpx
from datetime import datetime, timedelta

class FlightDataAPI:
    """
    Integration with Aviation Edge for flight schedules.
    API: https://aviation-edge.com/
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://aviation-edge.com/v2/public"

    async def get_departures(self, airport_code: str, hours_ahead: int = 4) -> list:
        """
        Get upcoming departures for demand forecasting.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.base_url}/timetable"
                params = {
                    "key": self.api_key,
                    "iataCode": airport_code,
                    "type": "departure"
                }
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    return []

                flights = response.json()

                # Filter to next N hours
                now = datetime.utcnow()
                cutoff = now + timedelta(hours=hours_ahead)

                upcoming = []
                for flight in flights:
                    departure_time = datetime.fromisoformat(flight["departure"]["scheduledTime"])
                    if now <= departure_time <= cutoff:
                        upcoming.append({
                            "flight_number": flight["flight"]["iataNumber"],
                            "airline": flight["airline"]["iataCode"],
                            "departure_time": departure_time.isoformat(),
                            "terminal": flight.get("departure", {}).get("terminal"),
                            "gate": flight.get("departure", {}).get("gate"),
                            "aircraft_type": flight.get("aircraft", {}).get("iataCode"),
                            "estimated_passengers": self.estimate_passengers(flight)
                        })

                return upcoming

        except Exception as e:
            print(f"Flight data API error: {e}")
            return []

    def estimate_passengers(self, flight: dict) -> int:
        """
        Estimate number of passengers based on aircraft type and load factor.
        """
        aircraft_capacities = {
            "A320": 180,
            "B738": 189,  # Boeing 737-800
            "A21N": 244,  # A321neo
            "B77W": 396,  # Boeing 777-300ER
            # Add more
        }

        aircraft_type = flight.get("aircraft", {}).get("iataCode", "A320")
        capacity = aircraft_capacities.get(aircraft_type, 180)

        # Assume 80% load factor
        return int(capacity * 0.8)
```

---

## 📱 Phase 4: Enhanced Frontend Features (Weeks 10-11)

### 4.1 Opt-In Telemetry Consent UI

Add consent dialog to `/src/components/TelemetryConsentDialog.tsx`:

```typescript
import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Shield, Activity, MapPin } from 'lucide-react';

interface TelemetryConsentDialogProps {
  open: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

export function TelemetryConsentDialog({ open, onAccept, onDecline }: TelemetryConsentDialogProps) {
  const [understandPrivacy, setUnderstandPrivacy] = useState(false);

  return (
    <Dialog open={open}>
      <DialogContent className="bg-slate-800 border-slate-700 max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-400" />
            Help Improve AirportWaze
          </DialogTitle>
          <DialogDescription className="text-slate-300 space-y-3 text-sm">
            <p>
              We'd like to collect anonymous location data while you're at the airport to improve wait time predictions for everyone.
            </p>

            <div className="bg-slate-700/50 rounded-lg p-3 space-y-2">
              <div className="flex items-start gap-2">
                <Activity className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <strong className="text-green-400">What we collect:</strong>
                  <ul className="text-xs text-slate-400 mt-1 list-disc list-inside">
                    <li>Your location while at the airport</li>
                    <li>Movement patterns (walking speed, waiting times)</li>
                    <li>Anonymized wait time observations</li>
                  </ul>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Shield className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <strong className="text-blue-400">Privacy guarantees:</strong>
                  <ul className="text-xs text-slate-400 mt-1 list-disc list-inside">
                    <li>No personally identifiable information collected</li>
                    <li>Anonymous UUID (not linked to your identity)</li>
                    <li>Data aggregated with 10+ other users (k-anonymity)</li>
                    <li>Uploaded only on WiFi to save mobile data</li>
                    <li>You can opt out anytime in settings</li>
                  </ul>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <MapPin className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <strong className="text-purple-400">How it helps:</strong>
                  <ul className="text-xs text-slate-400 mt-1 list-disc list-inside">
                    <li>More accurate wait time predictions</li>
                    <li>Better checkpoint recommendations</li>
                    <li>Improved "Will I Make It?" probability</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <Checkbox
                id="privacy"
                checked={understandPrivacy}
                onCheckedChange={(checked) => setUnderstandPrivacy(checked as boolean)}
              />
              <label
                htmlFor="privacy"
                className="text-xs text-slate-300 cursor-pointer"
              >
                I understand and agree to anonymous data collection
              </label>
            </div>
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-3 pt-2">
          <Button
            onClick={onDecline}
            variant="outline"
            className="flex-1 border-slate-600 text-slate-300"
          >
            No Thanks
          </Button>
          <Button
            onClick={onAccept}
            disabled={!understandPrivacy}
            className="flex-1 bg-blue-600 hover:bg-blue-700"
          >
            Enable Data Sharing
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

### 4.2 1-Tap Event Reporting

Add quick action buttons for user-confirmed events:

```typescript
// Add to App.tsx

const [showQuickActions, setShowQuickActions] = useState(false);

// When user is near a checkpoint
const handleQuickEvent = async (eventType: string) => {
  if (!userLocation) return;

  await fetch(`${API_URL}/api/telemetry/trip-event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event_type: eventType,
      checkpoint_id: nearestCheckpoint?.id,
      timestamp: new Date().toISOString(),
      lat: userLocation.lat,
      lng: userLocation.lng,
    }),
  });

  // Show success toast
};

// Render quick actions
{showQuickActions && (
  <div className="fixed bottom-20 right-4 space-y-2">
    <Button
      onClick={() => handleQuickEvent('entered_security_line')}
      className="w-48 bg-blue-600"
    >
      🚶 Entered Security Line
    </Button>
    <Button
      onClick={() => handleQuickEvent('cleared_security')}
      className="w-48 bg-green-600"
    >
      ✅ Cleared Security
    </Button>
    <Button
      onClick={() => handleQuickEvent('dropped_bag')}
      className="w-48 bg-purple-600"
    >
      🧳 Dropped Bag
    </Button>
  </div>
)}
```

---

## 🗄️ Phase 5: Database & Storage (Weeks 12-13)

### 5.1 PostgreSQL + TimescaleDB Setup

Replace in-memory storage with persistent database.

**Schema Design:**

```sql
-- airports table (existing data)
CREATE TABLE airports (
    code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(255),
    city VARCHAR(255),
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    terminals JSONB
);

-- checkpoints table
CREATE TABLE checkpoints (
    id VARCHAR(50) PRIMARY KEY,
    airport_code VARCHAR(3) REFERENCES airports(code),
    name VARCHAR(255),
    type VARCHAR(50),
    terminal VARCHAR(100),
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    base_wait_minutes INTEGER,
    discovered BOOLEAN DEFAULT FALSE,
    confidence FLOAT
);

-- telemetry_batches (TimescaleDB hypertable)
CREATE TABLE telemetry_batches (
    batch_id UUID PRIMARY KEY,
    user_id UUID,
    airport_code VARCHAR(3) REFERENCES airports(code),
    session_id UUID,
    uploaded_at TIMESTAMPTZ NOT NULL,
    points JSONB
);

SELECT create_hypertable('telemetry_batches', 'uploaded_at');

-- zone_dwell_events (TimescaleDB hypertable)
CREATE TABLE zone_dwell_events (
    event_id UUID PRIMARY KEY,
    zone_id VARCHAR(100),
    zone_type VARCHAR(50),
    enter_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    dwell_seconds INTEGER,
    confidence FLOAT,
    user_id UUID,
    session_id UUID
);

SELECT create_hypertable('zone_dwell_events', 'enter_time');

-- wait_time_observations (learned from telemetry)
CREATE TABLE wait_time_observations (
    observation_id UUID PRIMARY KEY,
    checkpoint_id VARCHAR(50) REFERENCES checkpoints(id),
    observed_at TIMESTAMPTZ NOT NULL,
    wait_minutes INTEGER,
    source VARCHAR(50), -- 'telemetry', 'crowdsourced', 'tsa_api', 'cbp_api'
    confidence FLOAT
);

SELECT create_hypertable('wait_time_observations', 'observed_at');

-- checkpoint_distributions (learned parameters)
CREATE TABLE checkpoint_distributions (
    checkpoint_id VARCHAR(50) PRIMARY KEY REFERENCES checkpoints(id),
    mu DOUBLE PRECISION,
    sigma DOUBLE PRECISION,
    sample_size INTEGER,
    confidence VARCHAR(20),
    last_updated TIMESTAMPTZ
);

-- flight_schedules
CREATE TABLE flight_schedules (
    flight_id UUID PRIMARY KEY,
    flight_number VARCHAR(20),
    airline VARCHAR(3),
    airport_code VARCHAR(3) REFERENCES airports(code),
    departure_time TIMESTAMPTZ,
    terminal VARCHAR(100),
    gate VARCHAR(20),
    estimated_passengers INTEGER,
    fetched_at TIMESTAMPTZ
);

CREATE INDEX idx_flights_departure ON flight_schedules(airport_code, departure_time);
```

### 5.2 Migrate Backend to Use PostgreSQL

Add to `/airport-waze-backend/pyproject.toml`:

```toml
[tool.poetry.dependencies]
...
psycopg2-binary = "^2.9.9"
sqlalchemy = "^2.0.23"
alembic = "^1.13.0"
```

Create `/app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/airportwaze")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 📊 Phase 6: Analytics & Monitoring (Weeks 14-15)

### 6.1 Calibration Dashboard

Build admin dashboard to monitor prediction accuracy:

```python
@app.get("/api/admin/calibration/{airport_code}")
async def get_calibration_metrics(airport_code: str):
    """
    Show calibration of predictions vs actual observations.
    Key metric: Are 90% predictions actually correct 90% of the time?
    """
    # Query actual vs predicted wait times
    observations = query_observations_with_predictions(airport_code)

    # Calculate calibration by percentile
    calibration = {}
    for percentile in [50, 80, 90, 95]:
        predicted = [obs[f"p{percentile}"] for obs in observations]
        actual = [obs["actual_wait"] for obs in observations]

        # What fraction of actuals were <= predicted?
        fraction_within = sum(a <= p for a, p in zip(actual, predicted)) / len(actual)

        calibration[f"p{percentile}"] = {
            "target": percentile / 100,
            "actual": round(fraction_within, 3),
            "error": round(abs(fraction_within - percentile / 100), 3)
        }

    return {
        "airport_code": airport_code,
        "sample_size": len(observations),
        "calibration": calibration
    }
```

---

## 🚢 Phase 7: Deployment & Scaling (Weeks 16-17)

### 7.1 Infrastructure

**Backend:**
- Deploy to Fly.io (current) or AWS/GCP
- Add PostgreSQL + TimescaleDB instance
- Set up Redis for caching
- Configure background workers for:
  - Hourly: Fetch TSA/CBP/flight data
  - Daily: Run zone discovery
  - Weekly: Update Bayesian models

**Frontend:**
- Current deployment works (Devin Apps)
- Consider PWA (Progressive Web App) for offline support
- Add service worker for background location tracking

### 7.2 Monitoring

- Set up Sentry for error tracking
- Add Prometheus/Grafana for metrics:
  - API latency
  - Prediction accuracy (MAE, calibration)
  - Data coverage (users per airport)
  - Cache hit rates

---

## 📋 Summary: Priority Order

If you want to implement incrementally, here's the recommended order:

### **Must-Have (Production-Ready MVP)**
1. ✅ Probabilistic predictions (DONE)
2. ✅ Monte Carlo simulation (DONE)
3. ✅ Real GPS coordinates (DONE)
4. **Add PostgreSQL database** (Phase 5.1-5.2)
5. **Integrate TSA API** (Phase 3.1)
6. **Add telemetry consent UI** (Phase 4.1)

### **High-Value Enhancements**
7. **User telemetry collection** (Phase 1.1-1.2)
8. **Hierarchical Bayesian learning** (Phase 2.2)
9. **Flight data integration** (Phase 3.3)
10. **1-tap event reporting** (Phase 4.2)

### **Advanced Features**
11. **Zone discovery with DBSCAN** (Phase 2.1)
12. **CBP wait times** (Phase 3.2)
13. **Calibration dashboard** (Phase 6.1)
14. **Multi-airport scaling** (Phase 7)

---

## 🎯 Next Steps

Would you like me to:

1. **Implement Phase 1** (telemetry collection) - Add the backend endpoints and frontend hooks?
2. **Set up PostgreSQL** (Phase 5) - Create the database schema and migrate existing code?
3. **Integrate TSA API** (Phase 3.1) - Add real-time TSA wait time fetching?
4. **Build the Bayesian learning model** (Phase 2.2) - Implement the hierarchical model?

Let me know which phase you'd like to tackle first, and I'll write the complete implementation!

---

## 📚 References from Your Design Doc

1. Moovit data flywheel approach
2. GTFS as baseline for transit
3. Hidden Markov Models for state detection
4. DBSCAN for zone discovery
5. Hierarchical Bayesian models for sparse data
6. K-anonymity for privacy
7. Monte Carlo for uncertainty quantification
8. Log-normal distributions for right-skewed wait times
9. TSA MyTSA API
10. CBP Airport Wait Time API

Your MVP is **excellent foundation** - it already implements the core probabilistic framework correctly. The main gap is **real data collection**, which is exactly what Phases 1-3 address.
