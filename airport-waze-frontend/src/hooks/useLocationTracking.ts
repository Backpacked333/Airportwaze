/**
 * React Hook for Location Tracking
 *
 * Provides easy-to-use React integration for the location tracking service.
 * Handles automatic cleanup and state management.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  locationTracking,
  TelemetryPoint,
  LocationState,
  ZoneDwell
} from '../services/locationTracking';

export interface UseLocationTrackingOptions {
  airportCode: string;
  checkpoints: Array<{
    id: string;
    lat: number;
    lng: number;
    type: string;
    name: string;
  }>;
  enabled: boolean;
  onZoneDwell?: (dwell: ZoneDwell) => void;
}

export interface UseLocationTrackingReturn {
  isTracking: boolean;
  locationState: LocationState;
  stats: {
    pointsCollected: number;
    batteryLevel: number;
    isCharging: boolean;
    sampleInterval: number;
  };
  startTracking: () => Promise<boolean>;
  stopTracking: () => void;
  error: string | null;
}

export function useLocationTracking(
  options: UseLocationTrackingOptions
): UseLocationTrackingReturn {
  const [isTracking, setIsTracking] = useState(false);
  const [locationState, setLocationState] = useState<LocationState>({
    isWalking: false,
    isWaiting: false,
    isInZone: false,
    currentZone: null,
    zoneEntryTime: null,
    speed: 0,
    accuracy: 0
  });
  const [stats, setStats] = useState({
    pointsCollected: 0,
    batteryLevel: 1.0,
    isCharging: false,
    sampleInterval: 5000
  });
  const [error, setError] = useState<string | null>(null);

  const sessionIdRef = useRef<string>(generateSessionId());
  const userIdRef = useRef<string>(getUserId());
  const statsIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Start tracking
  const startTracking = useCallback(async () => {
    if (isTracking) return true;
    if (!options.enabled) {
      setError('Tracking is disabled');
      return false;
    }

    try {
      const success = await locationTracking.startTracking(
        options.airportCode,
        sessionIdRef.current,
        userIdRef.current,
        options.checkpoints
      );

      if (success) {
        setIsTracking(true);
        setError(null);

        // Update stats periodically
        statsIntervalRef.current = setInterval(() => {
          const currentStats = locationTracking.getStats();
          setStats({
            pointsCollected: currentStats.pointsCollected,
            batteryLevel: currentStats.batteryLevel,
            isCharging: currentStats.isCharging,
            sampleInterval: currentStats.sampleInterval
          });
        }, 2000);

        return true;
      } else {
        setError('Failed to start tracking - permission denied');
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return false;
    }
  }, [isTracking, options.enabled, options.airportCode, options.checkpoints]);

  // Stop tracking
  const stopTracking = useCallback(() => {
    if (!isTracking) return;

    locationTracking.stopTracking();
    setIsTracking(false);

    if (statsIntervalRef.current) {
      clearInterval(statsIntervalRef.current);
      statsIntervalRef.current = null;
    }
  }, [isTracking]);

  // Setup callbacks
  useEffect(() => {
    locationTracking.onStateChange((state) => {
      setLocationState(state);
    });

    if (options.onZoneDwell) {
      locationTracking.onZoneDwell(options.onZoneDwell);
    }
  }, [options.onZoneDwell]);

  // Auto-start if enabled
  useEffect(() => {
    if (options.enabled && !isTracking) {
      startTracking();
    }
  }, [options.enabled, isTracking, startTracking]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isTracking) {
        stopTracking();
      }
    };
  }, [isTracking, stopTracking]);

  return {
    isTracking,
    locationState,
    stats,
    startTracking,
    stopTracking,
    error
  };
}

/**
 * Generate unique session ID
 */
function generateSessionId(): string {
  // Check if session already exists in sessionStorage
  let sessionId = sessionStorage.getItem('airportwaze_session_id');

  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('airportwaze_session_id', sessionId);
  }

  return sessionId;
}

/**
 * Get or create anonymous user ID
 */
function getUserId(): string {
  // Check if user ID already exists in localStorage
  let userId = localStorage.getItem('airportwaze_user_id');

  if (!userId) {
    userId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('airportwaze_user_id', userId);
  }

  return userId;
}
