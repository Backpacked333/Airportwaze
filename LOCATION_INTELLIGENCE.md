# 🧠 Location Intelligence & AI-Powered Checkpoint Discovery

## Overview

AirportWaze now features **intelligent location analysis** that learns from crowdsourced user movement data to automatically discover:

✅ **Airline-specific check-in counters** - "If users flying Delta keep standing in this area, it's probably Delta's check-in"
✅ **Security checkpoint queues** - Detect where people wait in security lines
✅ **Gate waiting areas** - Identify gate locations from user behavior
✅ **Movement patterns** - Understand how users navigate through airports
✅ **Heatmaps** - Visualize high-traffic areas

This transforms AirportWaze from a static database into a **self-learning navigation system**.

---

## How It Works

### 1. Location Tracking

As users move through the airport with the app open, we collect GPS breadcrumbs:

```typescript
// Frontend automatically tracks location
const { isTracking, currentLocation } = useLocationTracking({
  enabled: true,
  trackingIntervalMs: 5000, // Every 5 seconds
  flightInfo: {
    airportCode: 'JFK',
    airline: 'Delta',
    terminal: 'Terminal 4',
  }
});
```

**Privacy**: All location data is anonymized and used only for crowd-sourced analytics.

### 2. Movement Analysis

The backend analyzes location traces to detect:

- **Stationary periods**: User standing still for >2 minutes = likely checking in
- **Movement speed**: Walking vs standing still
- **Dwell time**: How long users spend at each location
- **Patterns**: Common paths through the airport

```python
# Backend automatically detects stationary behavior
if all recent locations within 10 meters:
    is_stationary = True
    if standing for 2+ minutes:
        activity_type = "check_in_likely"
```

### 3. DBSCAN Clustering

We use **DBSCAN** (Density-Based Spatial Clustering) to discover checkpoints:

```python
# Discover checkpoints with machine learning
discovered = LocationIntelligenceService.discover_checkpoints_dbscan(
    db=db,
    airport_code="JFK",
    airline="Delta",
    min_samples=10,  # Need 10+ observations
    max_radius_meters=50  # Cluster within 50 meters
)
```

**Algorithm**:
1. Find all locations where users stood still
2. Group nearby locations into clusters (within 50 meters)
3. Calculate cluster centroid (center point)
4. Analyze dwell time to classify type (check-in vs security vs gate)
5. Assign confidence score based on sample size and consistency

### 4. Airline-Specific Detection

The system learns which airlines use which check-in counters:

```
User A (Delta, Flight 123) stands at (40.6437, -73.7820) for 5 minutes
User B (Delta, Flight 456) stands at (40.6438, -73.7821) for 4 minutes
User C (Delta, Flight 789) stands at (40.6436, -73.7819) for 6 minutes

AI Conclusion: This is likely Delta's check-in counter!
Confidence: 85% (based on 50+ observations)
```

---

## API Endpoints

### Submit Location Trace

```http
POST /api/location/trace
Content-Type: application/json

{
  "session_id": "session_abc123",
  "airport_code": "JFK",
  "airline": "Delta",
  "flight_number": "DL123",
  "terminal": "Terminal 4",
  "lat": 40.6437,
  "lng": -73.7820,
  "accuracy": 10.5,
  "speed": 0.2,
  "timestamp": "2026-01-11T12:00:00Z"
}
```

**Response:**
```json
{
  "id": 12345,
  "is_stationary": true,
  "activity_type": "check_in_likely",
  "detected_checkpoint_id": "jfk-t4-delta-checkin"
}
```

### Discover Checkpoints

```http
POST /api/location/discover-checkpoints
Content-Type: application/json

{
  "airport_code": "JFK",
  "airline": "Delta",
  "min_samples": 10,
  "max_radius_meters": 50
}
```

**Response:**
```json
[
  {
    "id": 1,
    "airport_code": "JFK",
    "terminal": "Terminal 4",
    "center_lat": 40.6437,
    "center_lng": -73.7820,
    "radius_meters": 25.3,
    "checkpoint_type": "airline_checkin",
    "airline": "Delta",
    "confidence_score": 0.85,
    "sample_size": 52,
    "avg_dwell_time_seconds": 300,
    "is_verified": false
  }
]
```

### Get Airline Suggestions

```http
GET /api/location/airline-suggestions/JFK?min_confidence=0.5
```

**Response:**
```json
[
  {
    "airline": "Delta",
    "airport_code": "JFK",
    "terminal": "Terminal 4",
    "suggested_lat": 40.6437,
    "suggested_lng": -73.7820,
    "confidence_score": 0.85,
    "sample_size": 52,
    "avg_dwell_time_seconds": 300,
    "should_verify": true,
    "supporting_evidence": {
      "unique_sessions": 15,
      "time_range_hours": 48.5
    }
  }
]
```

### Get Heatmap Data

```http
POST /api/location/heatmap
Content-Type: application/json

{
  "airport_code": "JFK",
  "airline": "Delta",
  "terminal": "Terminal 4",
  "hours_back": 24
}
```

**Response:**
```json
{
  "airport_code": "JFK",
  "points": [
    {
      "lat": 40.6437,
      "lng": -73.7820,
      "intensity": 0.85,
      "count": 150
    }
  ],
  "clusters": [
    {
      "lat": 40.6437,
      "lng": -73.7820,
      "radius": 25.3,
      "type": "airline_checkin",
      "airline": "Delta",
      "confidence": 0.85
    }
  ],
  "total_traces": 1250
}
```

---

## Frontend Integration

### Enable Location Tracking

```tsx
import { useLocationTracking } from '@/hooks/useLocationTracking';

function FlightNavigation() {
  const { isTracking, tracesCollected, tracesSent } = useLocationTracking({
    enabled: true, // Start tracking
    flightInfo: {
      airportCode: 'JFK',
      airline: 'Delta',
      terminal: 'Terminal 4',
    },
    onLocationUpdate: (location) => {
      console.log('Location update:', location);
    }
  });

  return (
    <div>
      {isTracking && (
        <p>Tracking: {tracesCollected} collected, {tracesSent} sent</p>
      )}
    </div>
  );
}
```

### Visualize Discovered Checkpoints

```tsx
import { CheckpointDiscoveryMap, CheckpointDiscoveryLegend } from '@/components/CheckpointDiscoveryMap';
import { MapContainer, TileLayer } from 'react-leaflet';

function AirportMap() {
  return (
    <div className="relative">
      <MapContainer center={[40.6413, -73.7781]} zoom={15}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {/* Show AI-discovered checkpoints */}
        <CheckpointDiscoveryMap
          airportCode="JFK"
          airline="Delta"
          minConfidence={0.5}
        />
      </MapContainer>

      {/* Legend */}
      <div className="absolute top-4 right-4 z-1000">
        <CheckpointDiscoveryLegend />
      </div>
    </div>
  );
}
```

### Show Airline Suggestions

```tsx
import { AirlineCheckpointSuggestions } from '@/components/CheckpointDiscoveryMap';

function AirlineCheckIns() {
  return (
    <div>
      <h2>Find Your Airline's Check-in</h2>
      <AirlineCheckpointSuggestions airportCode="JFK" />
    </div>
  );
}
```

---

## Checkpoint Classification

The system automatically classifies discovered checkpoints:

| Type | Dwell Time | Detection Method |
|------|-----------|------------------|
| **airline_checkin** | 5+ minutes | Users with same airline stand still |
| **security_queue** | 2-5 minutes | Long stationary periods without airline data |
| **gate_waiting** | 1-2 minutes | Moderate waiting near gates |
| **service_counter** | 5+ minutes | Standing without specific airline |
| **general_waiting** | <1 minute | Brief stops |

---

## Confidence Scoring

Confidence scores (0.0 to 1.0) are calculated based on:

### Sample Size (40% weight)
- 100+ samples: 0.4
- 50-99 samples: 0.3
- 20-49 samples: 0.2
- <20 samples: 0.1

### Cluster Tightness (30% weight)
- Radius <10m: 0.3
- Radius 10-20m: 0.2
- Radius 20-50m: 0.1

### Dwell Time Reasonableness (30% weight)
- 1-10 minutes: 0.3 (typical check-in)
- 30s-20min: 0.2 (acceptable range)
- Outside range: 0.1

**Example:**
- Sample size: 52 observations → 0.3
- Cluster radius: 25m → 0.1
- Avg dwell time: 5 minutes → 0.3
- **Total confidence: 0.7 (70%)**

---

## Database Schema

### location_traces

Stores GPS breadcrumbs from users:

```sql
CREATE TABLE location_traces (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(100) NOT NULL,
  airport_code VARCHAR(3) NOT NULL,
  airline VARCHAR(50),
  flight_number VARCHAR(20),
  terminal VARCHAR(50),
  lat DOUBLE PRECISION NOT NULL,
  lng DOUBLE PRECISION NOT NULL,
  accuracy DOUBLE PRECISION,
  speed DOUBLE PRECISION,
  heading DOUBLE PRECISION,
  is_stationary BOOLEAN DEFAULT FALSE,
  activity_type VARCHAR(50),
  detected_checkpoint_id VARCHAR(50),
  timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_airport_airline_timestamp ON location_traces(airport_code, airline, timestamp);
CREATE INDEX idx_session_timestamp ON location_traces(session_id, timestamp);
```

### discovered_checkpoints

Stores AI-discovered checkpoints:

```sql
CREATE TABLE discovered_checkpoints (
  id SERIAL PRIMARY KEY,
  airport_code VARCHAR(3) NOT NULL,
  terminal VARCHAR(50),
  center_lat DOUBLE PRECISION NOT NULL,
  center_lng DOUBLE PRECISION NOT NULL,
  radius_meters DOUBLE PRECISION NOT NULL,
  checkpoint_type VARCHAR(50) NOT NULL,
  airline VARCHAR(50),
  confidence_score DOUBLE PRECISION DEFAULT 0.0,
  sample_size INTEGER DEFAULT 0,
  avg_dwell_time_seconds INTEGER,
  first_detected TIMESTAMP DEFAULT NOW(),
  last_updated TIMESTAMP DEFAULT NOW(),
  is_verified BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_airport_airline ON discovered_checkpoints(airport_code, airline);
```

### airline_checkpoint_mappings

Stores verified airline check-in locations:

```sql
CREATE TABLE airline_checkpoint_mappings (
  id SERIAL PRIMARY KEY,
  airport_code VARCHAR(3) NOT NULL,
  airline VARCHAR(50) NOT NULL,
  terminal VARCHAR(50),
  lat DOUBLE PRECISION NOT NULL,
  lng DOUBLE PRECISION NOT NULL,
  counter_numbers JSONB,
  operating_hours JSONB,
  discovery_method VARCHAR(50) DEFAULT 'crowdsourced',
  confidence_score DOUBLE PRECISION DEFAULT 0.0,
  is_verified BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE
);
```

---

## Privacy & Security

### Data Collection
- **Anonymized**: No personally identifiable information
- **Session-based**: Each session gets a random ID
- **Opt-in**: Users must enable location tracking
- **Purpose-limited**: Used only for navigation improvements

### Data Retention
- Location traces: 30 days
- Discovered checkpoints: Permanent (aggregated)
- User sessions: Not linked to user accounts (unless authenticated)

### Best Practices
1. Always ask permission before tracking
2. Show clear indicators when tracking is active
3. Allow users to stop tracking anytime
4. Explain how data is used
5. Never share raw location data

---

## Performance Considerations

### Backend Optimization

**Batch Processing:**
```python
# Process discoveries in background job (every hour)
@celery.task
def discover_all_airports():
    for airport in AIRPORTS:
        discover_checkpoints_dbscan(airport, hours_back=7)
```

**Caching:**
```python
# Cache discovered checkpoints for 1 hour
@cache_response(ttl=3600)
def get_discovered_checkpoints(airport_code: str):
    return db.query(DiscoveredCheckpoint).filter(...)
```

**Geospatial Indexing:**
```sql
-- Use PostGIS for faster geospatial queries
CREATE EXTENSION postgis;
CREATE INDEX idx_location_gist ON location_traces
  USING GIST(ST_MakePoint(lng, lat));
```

### Frontend Optimization

**Throttle Location Updates:**
```typescript
// Only send updates every 30 seconds to reduce server load
const sendIntervalMs = 30000; // 30 seconds
```

**Batch Traces:**
```typescript
// Send multiple traces in one request
await apiClient.post('/location/trace/batch', {
  traces: pendingTraces  // Array of 5-10 traces
});
```

---

## Machine Learning Improvements

### Future Enhancements

1. **Temporal Patterns**: Learn peak hours for each airline
2. **Seasonal Adjustments**: Account for holidays and events
3. **Real-time Predictions**: Predict current wait times from patterns
4. **Path Optimization**: Suggest fastest route through airport
5. **Anomaly Detection**: Alert when patterns change (construction, closures)

### Advanced Clustering

```python
# Use HDBSCAN for better hierarchical clustering
from hdbscan import HDBSCAN

clusterer = HDBSCAN(
    min_cluster_size=10,
    min_samples=5,
    cluster_selection_epsilon=0.01
)
labels = clusterer.fit_predict(coordinates)
```

---

## Use Cases

### 1. First-Time Travelers
*"I've never been to JFK. Where's Delta's check-in?"*

→ App shows AI-discovered Delta check-in counter with 85% confidence

### 2. Airport Changes
*"They moved United's check-in last week"*

→ System automatically detects new location from recent user behavior

### 3. Crowded Terminals
*"Which security line is fastest?"*

→ Heatmap shows real-time crowding at each checkpoint

### 4. Airline-Specific Navigation
*"Take me to my airline's check-in"*

→ Direct navigation to airline-specific location learned from data

---

## Deployment

### Database Migration

```bash
# Run migration to create location intelligence tables
cd airport-waze-backend
poetry run alembic upgrade head
```

### Install Dependencies

```bash
# Backend - add scikit-learn
poetry add scikit-learn

# Frontend - already included
npm install
```

### Enable Feature

```typescript
// In your main app component
<App>
  <LocationTrackingProvider>
    <YourApp />
  </LocationTrackingProvider>
</App>
```

---

## Monitoring

### Key Metrics

```python
# Track in your analytics
metrics = {
    "total_traces_collected": 1_250_000,
    "active_tracking_sessions": 450,
    "discovered_checkpoints": 125,
    "verified_checkpoints": 42,
    "avg_confidence_score": 0.72,
    "airlines_discovered": 15
}
```

### Alert Thresholds

- Confidence drops below 0.5 → Review checkpoint
- Sample size < 10 → Need more data
- Cluster radius > 100m → Too spread out, might be noise
- No new traces for 24 hours → Check tracking system

---

## Testing

### Unit Tests

```python
def test_dbscan_clustering():
    # Create test traces
    traces = create_test_traces(airport="JFK", count=50)

    # Run clustering
    checkpoints = discover_checkpoints_dbscan(
        db, "JFK", min_samples=10
    )

    assert len(checkpoints) > 0
    assert checkpoints[0].confidence_score > 0.5
```

### Integration Tests

```python
def test_location_trace_detection():
    # Submit 10 traces at same location
    for i in range(10):
        create_location_trace(
            lat=40.6437, lng=-73.7820,
            airline="Delta"
        )

    # Should detect as stationary
    traces = get_recent_traces()
    assert traces[-1].is_stationary == True
```

---

## Summary

🎯 **Goal**: Learn airport layouts from crowdsourced user movement data
🤖 **Method**: DBSCAN clustering + dwell-time analysis
📍 **Result**: Automatically discover airline check-ins, security queues, and more
🔒 **Privacy**: Fully anonymized, purpose-limited data collection
📊 **Accuracy**: 70-90% confidence scores with sufficient data

**This makes AirportWaze a self-improving, intelligent navigation system!** 🚀
