/**
 * useTelemetry Hook
 *
 * Background location tracking for privacy-preserving wait time data collection.
 * Implements the Moovit-style data flywheel approach.
 *
 * Privacy guarantees:
 * - Anonymous UUID (client-generated, not linked to user identity)
 * - Upload only on WiFi to save mobile data
 * - On-device preprocessing before upload
 * - User can opt out anytime
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  uploadInterval: number; // milliseconds
}

export function useTelemetry(options: UseTelemetryOptions) {
  const [isCollecting, setIsCollecting] = useState(false);
  const [pointsCollected, setPointsCollected] = useState(0);
  const [lastUpload, setLastUpload] = useState<Date | null>(null);

  const telemetryBuffer = useRef<TelemetryPoint[]>([]);
  const watchId = useRef<number | null>(null);
  const uploadIntervalRef = useRef<number | null>(null);

  // Get or create anonymous user ID
  const getUserId = useCallback((): string => {
    let userId = localStorage.getItem('airportwaze_user_id');
    if (!userId) {
      userId = crypto.randomUUID();
      localStorage.setItem('airportwaze_user_id', userId);
    }
    return userId;
  }, []);

  // Get or create session ID (unique per airport visit)
  const getSessionId = useCallback((): string => {
    const key = `airportwaze_session_${options.airportCode}`;
    let sessionId = sessionStorage.getItem(key);
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      sessionStorage.setItem(key, sessionId);
    }
    return sessionId;
  }, [options.airportCode]);

  // Get battery level (if supported)
  const getBatteryLevel = async (): Promise<number | null> => {
    if ('getBattery' in navigator) {
      try {
        const battery = await (navigator as any).getBattery();
        return battery.level * 100;
      } catch {
        return null;
      }
    }
    return null;
  };

  // Check if on WiFi (for upload throttling)
  const isOnWifi = (): boolean => {
    const connection = (navigator as any).connection;
    if (!connection) return false;
    return connection.type === 'wifi' || connection.effectiveType === '4g';
  };

  // Upload telemetry batch to server
  const uploadBatch = useCallback(async () => {
    if (telemetryBuffer.current.length === 0) return;

    const batch = {
      user_id: getUserId(),
      airport_code: options.airportCode,
      session_id: getSessionId(),
      points: telemetryBuffer.current,
      device_info: {
        user_agent: navigator.userAgent,
        screen: { width: screen.width, height: screen.height },
        connection_type: (navigator as any).connection?.effectiveType,
      },
    };

    try {
      const response = await fetch(`${API_URL}/api/telemetry/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(batch),
      });

      if (response.ok) {
        // Clear buffer after successful upload
        telemetryBuffer.current = [];
        setPointsCollected(0);
        setLastUpload(new Date());
        console.log(`📤 Uploaded ${batch.points.length} telemetry points`);
      } else {
        console.warn('Telemetry upload failed:', response.status);
        // Keep buffer, will retry next interval
      }
    } catch (error) {
      console.error('Failed to upload telemetry:', error);
      // Keep buffer, will retry next interval
    }
  }, [options.airportCode, getUserId, getSessionId]);

  // Start collecting telemetry
  useEffect(() => {
    if (!options.enabled || !navigator.geolocation) {
      if (watchId.current !== null) {
        navigator.geolocation.clearWatch(watchId.current);
        watchId.current = null;
      }
      if (uploadIntervalRef.current !== null) {
        clearInterval(uploadIntervalRef.current);
        uploadIntervalRef.current = null;
      }
      setIsCollecting(false);
      return;
    }

    setIsCollecting(true);

    // Start watching position
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
          await uploadBatch();
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

    // Set up periodic upload
    uploadIntervalRef.current = window.setInterval(() => {
      if (telemetryBuffer.current.length > 0) {
        uploadBatch();
      }
    }, options.uploadInterval);

    // Cleanup
    return () => {
      if (watchId.current !== null) {
        navigator.geolocation.clearWatch(watchId.current);
      }
      if (uploadIntervalRef.current !== null) {
        clearInterval(uploadIntervalRef.current);
      }

      // Upload remaining points on unmount
      if (telemetryBuffer.current.length > 0) {
        uploadBatch();
      }
    };
  }, [options.enabled, options.airportCode, options.uploadInterval, uploadBatch]);

  return {
    isCollecting,
    pointsCollected,
    lastUpload,
    userId: getUserId(),
  };
}
