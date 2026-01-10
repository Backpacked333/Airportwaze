/**
 * Location Tracking Service
 *
 * Provides comprehensive location tracking for airport telemetry:
 * - Continuous GPS tracking
 * - Motion detection (walking vs waiting)
 * - Zone dwell time calculation
 * - Background tracking support
 * - Battery-optimized sampling
 */

export interface TelemetryPoint {
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

export interface LocationState {
  isWalking: boolean;
  isWaiting: boolean;
  isInZone: boolean;
  currentZone: string | null;
  zoneEntryTime: Date | null;
  speed: number; // m/s
  accuracy: number; // meters
}

export interface ZoneDwell {
  zoneId: string;
  zoneType: string;
  enterTime: Date;
  exitTime: Date;
  dwellSeconds: number;
  confidence: number;
}

class LocationTrackingService {
  private watchId: number | null = null;
  private points: TelemetryPoint[] = [];
  private currentState: LocationState = {
    isWalking: false,
    isWaiting: false,
    isInZone: false,
    currentZone: null,
    zoneEntryTime: null,
    speed: 0,
    accuracy: 0
  };

  private sessionId: string | null = null;
  private airportCode: string | null = null;
  private userId: string | null = null;

  // Motion detection parameters
  private speedHistory: number[] = [];
  private readonly SPEED_THRESHOLD = 0.5; // m/s, ~1.8 km/h
  private readonly WAITING_THRESHOLD = 0.3; // m/s, ~1 km/h
  private readonly HISTORY_SIZE = 10;

  // Zone detection parameters
  private checkpoints: Array<{ id: string; lat: number; lng: number; type: string; name: string }> = [];
  private readonly ZONE_RADIUS = 50; // meters
  private zoneHistory: Array<{ zoneId: string; timestamp: Date }> = [];

  // Battery optimization
  private batteryLevel: number = 1.0;
  private isCharging: boolean = false;
  private sampleInterval: number = 5000; // ms

  // Callbacks
  private onPointCallback: ((point: TelemetryPoint) => void) | null = null;
  private onStateChangeCallback: ((state: LocationState) => void) | null = null;
  private onZoneDwellCallback: ((dwell: ZoneDwell) => void) | null = null;

  constructor() {
    this.initializeBatteryMonitoring();
  }

  /**
   * Start location tracking
   */
  async startTracking(
    airportCode: string,
    sessionId: string,
    userId: string,
    checkpoints: Array<{ id: string; lat: number; lng: number; type: string; name: string }>
  ): Promise<boolean> {
    this.airportCode = airportCode;
    this.sessionId = sessionId;
    this.userId = userId;
    this.checkpoints = checkpoints;

    // Request permissions
    const hasPermission = await this.requestLocationPermission();
    if (!hasPermission) {
      console.error('[LocationTracking] Location permission denied');
      return false;
    }

    // Start watching position
    const options: PositionOptions = {
      enableHighAccuracy: true,
      maximumAge: 0,
      timeout: 10000
    };

    this.watchId = navigator.geolocation.watchPosition(
      (position) => this.handlePosition(position),
      (error) => this.handleError(error),
      options
    );

    // Start motion detection if available
    if (window.DeviceMotionEvent) {
      window.addEventListener('devicemotion', this.handleMotion.bind(this));
    }

    console.log('[LocationTracking] Tracking started');
    return true;
  }

  /**
   * Stop location tracking
   */
  stopTracking() {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }

    if (window.DeviceMotionEvent) {
      window.removeEventListener('devicemotion', this.handleMotion.bind(this));
    }

    // Upload pending points
    if (this.points.length > 0) {
      this.uploadBatch();
    }

    console.log('[LocationTracking] Tracking stopped');
  }

  /**
   * Handle GPS position update
   */
  private handlePosition(position: GeolocationPosition) {
    const point: TelemetryPoint = {
      timestamp: new Date().toISOString(),
      lat: position.coords.latitude,
      lng: position.coords.longitude,
      speed: position.coords.speed,
      heading: position.coords.heading,
      altitude: position.coords.altitude,
      horizontal_accuracy: position.coords.accuracy,
      acceleration: null,
      battery_level: this.batteryLevel * 100
    };

    // Add to collection
    this.points.push(point);

    // Update speed history for motion detection
    if (point.speed !== null) {
      this.speedHistory.push(point.speed);
      if (this.speedHistory.length > this.HISTORY_SIZE) {
        this.speedHistory.shift();
      }
    }

    // Detect motion state
    this.detectMotionState();

    // Detect zones
    this.detectZone(point.lat, point.lng);

    // Callback
    if (this.onPointCallback) {
      this.onPointCallback(point);
    }

    // Auto-upload when batch size reached
    if (this.points.length >= 20) {
      this.uploadBatch();
    }

    // Battery-optimized sampling
    this.adjustSampleRate();
  }

  /**
   * Handle GPS error
   */
  private handleError(error: GeolocationPositionError) {
    console.error('[LocationTracking] GPS error:', error.message);

    // Retry with lower accuracy if high accuracy fails
    if (error.code === error.TIMEOUT) {
      console.log('[LocationTracking] Retrying with lower accuracy');
      // Implementation for fallback
    }
  }

  /**
   * Handle device motion (accelerometer)
   */
  private handleMotion(event: DeviceMotionEvent) {
    if (!event.accelerationIncludingGravity) return;

    const { x, y, z } = event.accelerationIncludingGravity;
    if (x === null || y === null || z === null) return;

    // Calculate total acceleration magnitude
    const magnitude = Math.sqrt(x * x + y * y + z * z);

    // Update last point with acceleration data
    if (this.points.length > 0) {
      this.points[this.points.length - 1].acceleration = magnitude;
    }
  }

  /**
   * Detect motion state (walking vs waiting)
   */
  private detectMotionState() {
    if (this.speedHistory.length < 3) return;

    const avgSpeed = this.speedHistory.reduce((a, b) => a + b, 0) / this.speedHistory.length;

    const wasWalking = this.currentState.isWalking;
    const wasWaiting = this.currentState.isWaiting;

    // Update state
    this.currentState.isWalking = avgSpeed > this.SPEED_THRESHOLD;
    this.currentState.isWaiting = avgSpeed < this.WAITING_THRESHOLD;
    this.currentState.speed = avgSpeed;

    // State changed
    if (this.currentState.isWalking !== wasWalking || this.currentState.isWaiting !== wasWaiting) {
      console.log('[LocationTracking] Motion state:', {
        walking: this.currentState.isWalking,
        waiting: this.currentState.isWaiting,
        speed: avgSpeed.toFixed(2)
      });

      if (this.onStateChangeCallback) {
        this.onStateChangeCallback({ ...this.currentState });
      }
    }
  }

  /**
   * Detect if user is in a checkpoint zone
   */
  private detectZone(lat: number, lng: number) {
    let closestCheckpoint: typeof this.checkpoints[0] | null = null;
    let minDistance = Infinity;

    // Find closest checkpoint
    for (const checkpoint of this.checkpoints) {
      const distance = this.calculateDistance(lat, lng, checkpoint.lat, checkpoint.lng);
      if (distance < minDistance) {
        minDistance = distance;
        closestCheckpoint = checkpoint;
      }
    }

    // Check if within zone radius
    const wasInZone = this.currentState.isInZone;
    const oldZone = this.currentState.currentZone;

    if (closestCheckpoint && minDistance <= this.ZONE_RADIUS) {
      this.currentState.isInZone = true;
      this.currentState.currentZone = closestCheckpoint.id;

      // Entered new zone
      if (!wasInZone || oldZone !== closestCheckpoint.id) {
        console.log('[LocationTracking] Entered zone:', closestCheckpoint.name);
        this.currentState.zoneEntryTime = new Date();
        this.zoneHistory.push({
          zoneId: closestCheckpoint.id,
          timestamp: new Date()
        });
      }
    } else {
      // Exited zone
      if (wasInZone && oldZone && this.currentState.zoneEntryTime) {
        const exitTime = new Date();
        const dwellSeconds = (exitTime.getTime() - this.currentState.zoneEntryTime.getTime()) / 1000;

        // Only report dwells > 30 seconds (filter out false positives)
        if (dwellSeconds > 30) {
          const checkpoint = this.checkpoints.find(c => c.id === oldZone);
          if (checkpoint) {
            const zoneDwell: ZoneDwell = {
              zoneId: oldZone,
              zoneType: checkpoint.type,
              enterTime: this.currentState.zoneEntryTime,
              exitTime: exitTime,
              dwellSeconds: Math.round(dwellSeconds),
              confidence: this.calculateDwellConfidence(dwellSeconds, minDistance)
            };

            console.log('[LocationTracking] Zone dwell detected:', {
              zone: checkpoint.name,
              duration: `${Math.round(dwellSeconds / 60)} minutes`
            });

            if (this.onZoneDwellCallback) {
              this.onZoneDwellCallback(zoneDwell);
            }
          }
        }

        this.currentState.isInZone = false;
        this.currentState.currentZone = null;
        this.currentState.zoneEntryTime = null;
      }
    }
  }

  /**
   * Calculate confidence in zone dwell detection
   */
  private calculateDwellConfidence(dwellSeconds: number, exitDistance: number): number {
    let confidence = 0.5; // base

    // Longer dwell = higher confidence
    if (dwellSeconds > 300) confidence += 0.3; // 5+ minutes
    else if (dwellSeconds > 120) confidence += 0.2; // 2+ minutes
    else if (dwellSeconds > 60) confidence += 0.1; // 1+ minute

    // Clean exit (far from zone) = higher confidence
    if (exitDistance > this.ZONE_RADIUS * 2) confidence += 0.2;
    else if (exitDistance > this.ZONE_RADIUS * 1.5) confidence += 0.1;

    return Math.min(confidence, 1.0);
  }

  /**
   * Calculate distance between two GPS coordinates (Haversine formula)
   */
  private calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const R = 6371e3; // Earth radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lng2 - lng1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) *
      Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // Distance in meters
  }

  /**
   * Upload telemetry batch to backend
   */
  private async uploadBatch() {
    if (this.points.length === 0) return;
    if (!this.sessionId || !this.airportCode || !this.userId) return;

    const batch = {
      user_id: this.userId,
      airport_code: this.airportCode,
      session_id: this.sessionId,
      points: [...this.points],
      device_info: {
        platform: navigator.platform,
        userAgent: navigator.userAgent,
        battery: this.batteryLevel,
        charging: this.isCharging
      }
    };

    try {
      const response = await fetch('http://localhost:8000/api/telemetry/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(batch)
      });

      if (response.ok) {
        console.log(`[LocationTracking] Uploaded ${this.points.length} points`);
        this.points = []; // Clear uploaded points
      } else {
        console.error('[LocationTracking] Upload failed:', response.status);
        // Queue for background sync
        this.queueForBackgroundSync(batch);
      }
    } catch (error) {
      console.error('[LocationTracking] Upload error:', error);
      // Queue for background sync
      this.queueForBackgroundSync(batch);
    }
  }

  /**
   * Queue telemetry for background sync when offline
   */
  private async queueForBackgroundSync(batch: any) {
    try {
      const db = await this.openDB();
      const tx = db.transaction('pending', 'readwrite');
      const store = tx.objectStore('pending');

      await store.add({
        timestamp: Date.now(),
        data: batch
      });

      console.log('[LocationTracking] Queued for background sync');

      // Register background sync
      if ('serviceWorker' in navigator && 'sync' in (self as any).registration) {
        const registration = await navigator.serviceWorker.ready;
        await (registration as any).sync.register('upload-telemetry');
      }
    } catch (error) {
      console.error('[LocationTracking] Failed to queue for sync:', error);
    }
  }

  /**
   * Initialize battery monitoring for power optimization
   */
  private async initializeBatteryMonitoring() {
    if ('getBattery' in navigator) {
      try {
        const battery: any = await (navigator as any).getBattery();

        this.batteryLevel = battery.level;
        this.isCharging = battery.charging;

        battery.addEventListener('levelchange', () => {
          this.batteryLevel = battery.level;
          this.adjustSampleRate();
        });

        battery.addEventListener('chargingchange', () => {
          this.isCharging = battery.charging;
          this.adjustSampleRate();
        });
      } catch (error) {
        console.warn('[LocationTracking] Battery API not available');
      }
    }
  }

  /**
   * Adjust GPS sample rate based on battery level
   */
  private adjustSampleRate() {
    let newInterval = 5000; // Default: 5 seconds

    if (this.isCharging) {
      newInterval = 3000; // More frequent when charging
    } else if (this.batteryLevel < 0.2) {
      newInterval = 15000; // Less frequent when low battery
    } else if (this.batteryLevel < 0.5) {
      newInterval = 8000;
    }

    if (newInterval !== this.sampleInterval) {
      this.sampleInterval = newInterval;
      console.log(`[LocationTracking] Sample rate adjusted to ${newInterval}ms`);
      // Would restart watch with new interval in production
    }
  }

  /**
   * Request location permission
   */
  private async requestLocationPermission(): Promise<boolean> {
    try {
      const result = await navigator.permissions.query({ name: 'geolocation' as PermissionName });
      return result.state === 'granted' || result.state === 'prompt';
    } catch (error) {
      // Permissions API not supported, try direct request
      return new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          () => resolve(true),
          () => resolve(false)
        );
      });
    }
  }

  /**
   * Open IndexedDB for local storage
   */
  private openDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('AirportWazeTelemetry', 1);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('pending')) {
          const store = db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  /**
   * Register callbacks
   */
  onPoint(callback: (point: TelemetryPoint) => void) {
    this.onPointCallback = callback;
  }

  onStateChange(callback: (state: LocationState) => void) {
    this.onStateChangeCallback = callback;
  }

  onZoneDwell(callback: (dwell: ZoneDwell) => void) {
    this.onZoneDwellCallback = callback;
  }

  /**
   * Get current state
   */
  getState(): LocationState {
    return { ...this.currentState };
  }

  /**
   * Get current session stats
   */
  getStats() {
    return {
      pointsCollected: this.points.length,
      sessionId: this.sessionId,
      airportCode: this.airportCode,
      batteryLevel: this.batteryLevel,
      isCharging: this.isCharging,
      sampleInterval: this.sampleInterval,
      currentState: this.currentState
    };
  }
}

// Export singleton instance
export const locationTracking = new LocationTrackingService();
