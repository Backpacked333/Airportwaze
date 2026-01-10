/**
 * Intelligence Engine - AI/ML Features for AirportWaze
 *
 * This service provides advanced predictive and analytical capabilities:
 * - Predictive zone entry (know when user will reach checkpoint)
 * - Personal speed profiling (learn user's walking speed)
 * - Route optimization (fastest path through airport)
 * - Crowding detection (density analysis)
 * - Anomaly detection (unusual wait times)
 * - Smart notifications (context-aware alerts)
 */

export interface UserProfile {
  userId: string;
  averageWalkingSpeed: number; // m/s
  averageWaitTolerance: number; // minutes
  mobilityFactor: number; // 0.5 (slow) to 1.5 (fast)
  preCheckEnrolled: boolean;
  globalEntryEnrolled: boolean;
  totalTrips: number;
  lastUpdated: Date;
}

export interface PredictiveAlert {
  id: string;
  type: 'zone_approaching' | 'leave_now' | 'gate_change' | 'wait_spike' | 'route_change';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  actionUrl?: string;
  timestamp: Date;
  expiresAt?: Date;
}

export interface RouteSegment {
  from: { lat: number; lng: number; name: string };
  to: { lat: number; lng: number; name: string };
  distance: number; // meters
  walkTime: number; // seconds
  waitTime: number; // seconds (if checkpoint)
  crowdLevel: 'low' | 'medium' | 'high' | 'very_high';
  checkpointId?: string;
}

export interface OptimizedRoute {
  segments: RouteSegment[];
  totalDistance: number;
  totalWalkTime: number;
  totalWaitTime: number;
  totalTime: number;
  arriveByTime: Date;
  leaveByTime: Date;
  confidence: number; // 0-1
  alternatives: OptimizedRoute[];
}

export interface CrowdingMetrics {
  airportCode: string;
  checkpointId: string;
  currentDensity: number; // users per 100m²
  crowdLevel: 'low' | 'medium' | 'high' | 'very_high';
  trendDirection: 'increasing' | 'stable' | 'decreasing';
  peakHourProbability: number; // 0-1
  estimatedQueueLength: number; // people
}

export interface AnomalyDetection {
  checkpointId: string;
  currentWait: number;
  expectedWait: number;
  deviation: number; // standard deviations
  isAnomaly: boolean;
  possibleReasons: string[];
  confidence: number;
}

class IntelligenceEngine {
  private userProfile: UserProfile | null = null;
  private locationHistory: Array<{ lat: number; lng: number; timestamp: Date }> = [];
  private speedSamples: number[] = [];
  private crowdingCache: Map<string, CrowdingMetrics> = new Map();

  /**
   * Initialize user profile (or load from storage)
   */
  async initializeProfile(userId: string): Promise<UserProfile> {
    // Try to load from localStorage
    const stored = localStorage.getItem(`airportwaze_profile_${userId}`);
    if (stored) {
      this.userProfile = JSON.parse(stored);
      this.userProfile!.lastUpdated = new Date(this.userProfile!.lastUpdated);
      return this.userProfile!;
    }

    // Create new profile
    this.userProfile = {
      userId,
      averageWalkingSpeed: 1.4, // Default: ~5 km/h
      averageWaitTolerance: 15,
      mobilityFactor: 1.0,
      preCheckEnrolled: false,
      globalEntryEnrolled: false,
      totalTrips: 0,
      lastUpdated: new Date()
    };

    this.saveProfile();
    return this.userProfile;
  }

  /**
   * Update user profile with new walking speed data
   */
  updateSpeedProfile(speed: number) {
    if (!this.userProfile) return;

    // Add to samples (keep last 100)
    this.speedSamples.push(speed);
    if (this.speedSamples.length > 100) {
      this.speedSamples.shift();
    }

    // Calculate exponential moving average
    const alpha = 0.1; // smoothing factor
    this.userProfile.averageWalkingSpeed =
      alpha * speed + (1 - alpha) * this.userProfile.averageWalkingSpeed;

    // Update mobility factor (relative to average person: 1.4 m/s)
    this.userProfile.mobilityFactor = this.userProfile.averageWalkingSpeed / 1.4;

    this.saveProfile();
  }

  /**
   * Predict when user will enter a zone
   */
  predictZoneEntry(
    currentLat: number,
    currentLng: number,
    targetLat: number,
    targetLng: number,
    currentSpeed: number
  ): { etaSeconds: number; etaTime: Date; distance: number; confidence: number } {
    const distance = this.calculateDistance(currentLat, currentLng, targetLat, targetLng);

    // Use personal speed if available, otherwise use current speed
    const effectiveSpeed = this.userProfile?.averageWalkingSpeed || currentSpeed || 1.4;

    // Account for slowdown near checkpoints (people slow down when approaching)
    const slowdownFactor = distance < 100 ? 0.8 : 1.0;
    const adjustedSpeed = effectiveSpeed * slowdownFactor;

    const etaSeconds = distance / adjustedSpeed;
    const etaTime = new Date(Date.now() + etaSeconds * 1000);

    // Confidence based on speed consistency
    const speedVariance = this.calculateSpeedVariance();
    const confidence = Math.max(0.5, 1 - speedVariance);

    return {
      etaSeconds,
      etaTime,
      distance,
      confidence
    };
  }

  /**
   * Optimize route through airport
   */
  async optimizeRoute(
    currentLocation: { lat: number; lng: number },
    destination: { lat: number; lng: number; terminal: string; gate: string },
    checkpoints: Array<{ id: string; lat: number; lng: number; type: string; terminal: string }>,
    hasCheckedBags: boolean,
    hasTSAPreCheck: boolean,
    flightDepartureTime: Date
  ): Promise<OptimizedRoute> {
    const segments: RouteSegment[] = [];
    let totalDistance = 0;
    let totalWalkTime = 0;
    let totalWaitTime = 0;

    let currentPos = currentLocation;

    // Step 1: Bag check (if needed)
    if (hasCheckedBags) {
      const bagCheckpoints = checkpoints.filter(
        cp => cp.type === 'bag_check' && cp.terminal === destination.terminal
      );

      if (bagCheckpoints.length > 0) {
        const closest = this.findClosestCheckpoint(currentPos, bagCheckpoints);
        const distance = this.calculateDistance(
          currentPos.lat, currentPos.lng,
          closest.lat, closest.lng
        );
        const walkTime = this.calculateWalkTime(distance);
        const waitTime = await this.estimateWaitTime(closest.id);
        const crowdLevel = await this.estimateCrowdLevel(closest.id);

        segments.push({
          from: { ...currentPos, name: 'Current Location' },
          to: { lat: closest.lat, lng: closest.lng, name: 'Bag Check' },
          distance,
          walkTime,
          waitTime,
          crowdLevel,
          checkpointId: closest.id
        });

        totalDistance += distance;
        totalWalkTime += walkTime;
        totalWaitTime += waitTime;
        currentPos = { lat: closest.lat, lng: closest.lng };
      }
    }

    // Step 2: Security checkpoint
    const securityType = hasTSAPreCheck ? 'tsa_precheck' : 'tsa';
    const securityCheckpoints = checkpoints.filter(
      cp => cp.type === securityType && cp.terminal === destination.terminal
    );

    if (securityCheckpoints.length > 0) {
      // Find checkpoint with shortest total time (walk + wait)
      const checkpointScores = await Promise.all(
        securityCheckpoints.map(async (cp) => {
          const distance = this.calculateDistance(
            currentPos.lat, currentPos.lng,
            cp.lat, cp.lng
          );
          const walkTime = this.calculateWalkTime(distance);
          const waitTime = await this.estimateWaitTime(cp.id);
          const crowdLevel = await this.estimateCrowdLevel(cp.id);

          // Prefer less crowded checkpoints
          const crowdPenalty = {
            'low': 0,
            'medium': 120, // +2 min penalty
            'high': 300,   // +5 min penalty
            'very_high': 600 // +10 min penalty
          }[crowdLevel];

          return {
            checkpoint: cp,
            distance,
            walkTime,
            waitTime,
            crowdLevel,
            totalTime: walkTime + waitTime + crowdPenalty
          };
        })
      );

      // Select checkpoint with lowest total time
      const best = checkpointScores.reduce((a, b) =>
        a.totalTime < b.totalTime ? a : b
      );

      segments.push({
        from: { ...currentPos, name: segments.length > 0 ? 'Bag Check' : 'Current Location' },
        to: { lat: best.checkpoint.lat, lng: best.checkpoint.lng, name: 'Security' },
        distance: best.distance,
        walkTime: best.walkTime,
        waitTime: best.waitTime,
        crowdLevel: best.crowdLevel,
        checkpointId: best.checkpoint.id
      });

      totalDistance += best.distance;
      totalWalkTime += best.walkTime;
      totalWaitTime += best.waitTime;
      currentPos = { lat: best.checkpoint.lat, lng: best.checkpoint.lng };
    }

    // Step 3: Walk to gate
    const gateDistance = this.calculateDistance(
      currentPos.lat, currentPos.lng,
      destination.lat, destination.lng
    );
    const gateWalkTime = this.calculateWalkTime(gateDistance);

    segments.push({
      from: { ...currentPos, name: 'Security' },
      to: { ...destination, name: `Gate ${destination.gate}` },
      distance: gateDistance,
      walkTime: gateWalkTime,
      waitTime: 0,
      crowdLevel: 'low'
    });

    totalDistance += gateDistance;
    totalWalkTime += gateWalkTime;

    const totalTime = totalWalkTime + totalWaitTime;

    // Add 15-minute buffer
    const buffer = 15 * 60;
    const arriveByTime = new Date(flightDepartureTime.getTime() - 30 * 60 * 1000); // 30 min before departure
    const leaveByTime = new Date(arriveByTime.getTime() - (totalTime + buffer) * 1000);

    // Calculate confidence based on data quality
    const confidence = this.calculateRouteConfidence(segments);

    return {
      segments,
      totalDistance,
      totalWalkTime,
      totalWaitTime,
      totalTime,
      arriveByTime,
      leaveByTime,
      confidence,
      alternatives: [] // TODO: Generate alternative routes
    };
  }

  /**
   * Detect crowding at checkpoint
   */
  async detectCrowding(
    checkpointId: string,
    activeSessions: number
  ): Promise<CrowdingMetrics> {
    // Check cache
    const cached = this.crowdingCache.get(checkpointId);
    if (cached && Date.now() - cached.timestamp < 60000) { // 1 minute cache
      return cached;
    }

    // Estimate density (users per 100m²)
    // Assume checkpoint area is ~200m² (20m × 10m)
    const area = 200;
    const density = (activeSessions / area) * 100;

    let crowdLevel: 'low' | 'medium' | 'high' | 'very_high';
    if (density < 2) crowdLevel = 'low';
    else if (density < 5) crowdLevel = 'medium';
    else if (density < 10) crowdLevel = 'high';
    else crowdLevel = 'very_high';

    // Estimate queue length (assume 1 person per meter)
    const estimatedQueueLength = Math.round(activeSessions * 1.5);

    // Detect trend (compare with 5 min ago)
    const trendDirection: 'increasing' | 'stable' | 'decreasing' = 'stable'; // TODO: Historical comparison

    // Peak hour probability (based on time of day)
    const hour = new Date().getHours();
    const peakHourProbability = this.calculatePeakHourProbability(hour);

    const metrics: CrowdingMetrics = {
      airportCode: 'JFK', // TODO: Get from context
      checkpointId,
      currentDensity: density,
      crowdLevel,
      trendDirection,
      peakHourProbability,
      estimatedQueueLength
    };

    this.crowdingCache.set(checkpointId, { ...metrics, timestamp: Date.now() } as any);
    return metrics;
  }

  /**
   * Detect anomalies in wait times
   */
  async detectAnomaly(
    checkpointId: string,
    currentWait: number,
    historicalMean: number,
    historicalStd: number
  ): Promise<AnomalyDetection> {
    const deviation = (currentWait - historicalMean) / (historicalStd || 1);
    const isAnomaly = Math.abs(deviation) > 2; // More than 2 standard deviations

    const possibleReasons = [];
    if (deviation > 2) {
      // Unusually long wait
      const hour = new Date().getHours();
      if (hour >= 6 && hour <= 9) possibleReasons.push('Morning rush hour');
      if (hour >= 16 && hour <= 20) possibleReasons.push('Evening rush hour');
      possibleReasons.push('Possible staffing shortage');
      possibleReasons.push('Equipment malfunction');
      possibleReasons.push('Special security screening in effect');
    } else if (deviation < -2) {
      // Unusually short wait
      possibleReasons.push('Off-peak hours');
      possibleReasons.push('Additional lanes opened');
      possibleReasons.push('Fewer travelers than usual');
    }

    const confidence = Math.min(Math.abs(deviation) / 3, 1);

    return {
      checkpointId,
      currentWait,
      expectedWait: historicalMean,
      deviation,
      isAnomaly,
      possibleReasons,
      confidence
    };
  }

  /**
   * Generate smart notifications
   */
  async generateSmartNotifications(
    currentLocation: { lat: number; lng: number },
    flightTime: Date,
    checkpoints: any[],
    route: OptimizedRoute
  ): Promise<PredictiveAlert[]> {
    const alerts: PredictiveAlert[] = [];
    const now = new Date();
    const minutesUntilFlight = (flightTime.getTime() - now.getTime()) / 60000;

    // Alert: Time to leave
    if (minutesUntilFlight <= route.totalTime / 60 + 30) {
      const minutesUntilLeave = (route.leaveByTime.getTime() - now.getTime()) / 60000;

      if (minutesUntilLeave <= 15 && minutesUntilLeave > 0) {
        alerts.push({
          id: 'leave-now-' + Date.now(),
          type: 'leave_now',
          title: '⏰ Time to Head to Airport!',
          message: `Leave in ${Math.round(minutesUntilLeave)} minutes to make your flight comfortably.`,
          priority: 'high',
          timestamp: now,
          expiresAt: route.leaveByTime
        });
      }
    }

    // Alert: Approaching checkpoint
    for (const segment of route.segments) {
      if (segment.checkpointId) {
        const distance = this.calculateDistance(
          currentLocation.lat,
          currentLocation.lng,
          segment.to.lat,
          segment.to.lng
        );

        if (distance < 100 && distance > 20) {
          alerts.push({
            id: 'approaching-' + segment.checkpointId,
            type: 'zone_approaching',
            title: `📍 Approaching ${segment.to.name}`,
            message: `Current wait: ${Math.round(segment.waitTime / 60)} min | Crowd level: ${segment.crowdLevel}`,
            priority: 'medium',
            timestamp: now
          });
        }
      }
    }

    // Alert: Wait time spike
    for (const segment of route.segments) {
      if (segment.checkpointId && segment.waitTime > 1800) { // > 30 min
        alerts.push({
          id: 'spike-' + segment.checkpointId,
          type: 'wait_spike',
          title: '⚠️ Long Wait Detected',
          message: `${segment.to.name} has a ${Math.round(segment.waitTime / 60)} minute wait. Consider alternative checkpoint if available.`,
          priority: 'high',
          timestamp: now
        });
      }
    }

    return alerts;
  }

  // Helper methods

  private calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const R = 6371e3;
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lng2 - lng1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) *
      Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  }

  private calculateWalkTime(distance: number): number {
    const speed = this.userProfile?.averageWalkingSpeed || 1.4;
    return Math.round(distance / speed);
  }

  private async estimateWaitTime(checkpointId: string): Promise<number> {
    // TODO: Fetch from backend
    return 600; // 10 minutes default
  }

  private async estimateCrowdLevel(checkpointId: string): Promise<'low' | 'medium' | 'high' | 'very_high'> {
    // TODO: Fetch from backend
    return 'medium';
  }

  private findClosestCheckpoint(
    location: { lat: number; lng: number },
    checkpoints: Array<{ lat: number; lng: number; [key: string]: any }>
  ): any {
    return checkpoints.reduce((closest, cp) => {
      const dist = this.calculateDistance(location.lat, location.lng, cp.lat, cp.lng);
      const closestDist = this.calculateDistance(location.lat, location.lng, closest.lat, closest.lng);
      return dist < closestDist ? cp : closest;
    });
  }

  private calculateSpeedVariance(): number {
    if (this.speedSamples.length < 2) return 0;

    const mean = this.speedSamples.reduce((a, b) => a + b, 0) / this.speedSamples.length;
    const variance = this.speedSamples.reduce((sum, speed) =>
      sum + Math.pow(speed - mean, 2), 0
    ) / this.speedSamples.length;

    return Math.sqrt(variance) / mean; // Coefficient of variation
  }

  private calculateRouteConfidence(segments: RouteSegment[]): number {
    // Higher confidence if we have recent data for all checkpoints
    const avgCrowdConfidence = segments
      .filter(s => s.checkpointId)
      .map(s => s.crowdLevel === 'low' ? 0.9 : s.crowdLevel === 'medium' ? 0.7 : 0.5)
      .reduce((a, b) => a + b, 0) / segments.length || 0.5;

    return avgCrowdConfidence;
  }

  private calculatePeakHourProbability(hour: number): number {
    // Peak hours: 6-9 AM and 4-8 PM
    if ((hour >= 6 && hour <= 9) || (hour >= 16 && hour <= 20)) {
      return 0.9;
    } else if ((hour >= 10 && hour <= 15) || (hour >= 21 && hour <= 23)) {
      return 0.5;
    } else {
      return 0.1;
    }
  }

  private saveProfile() {
    if (!this.userProfile) return;
    localStorage.setItem(
      `airportwaze_profile_${this.userProfile.userId}`,
      JSON.stringify(this.userProfile)
    );
  }

  getProfile(): UserProfile | null {
    return this.userProfile;
  }
}

// Export singleton
export const intelligenceEngine = new IntelligenceEngine();
