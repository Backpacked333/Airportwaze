/**
 * Location Tracking Hook
 *
 * Tracks user location throughout their airport journey and sends breadcrumbs
 * to the backend for intelligent checkpoint discovery.
 *
 * This enables crowdsourced learning of:
 * - Airline check-in counter locations
 * - Security checkpoint queues
 * - Gate locations
 * - High-traffic areas
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { useErrorToast } from './useErrorToast';

interface FlightInfo {
  airline?: string;
  flightNumber?: string;
  terminal?: string;
  airportCode: string;
}

interface LocationTraceData {
  lat: number;
  lng: number;
  accuracy?: number;
  speed?: number;
  heading?: number;
  timestamp: string;
}

interface UseLocationTrackingOptions {
  enabled?: boolean;
  trackingIntervalMs?: number; // How often to track location
  sendIntervalMs?: number; // How often to send to server
  flightInfo?: FlightInfo;
  onLocationUpdate?: (location: LocationTraceData) => void;
}

interface LocationTrackingState {
  isTracking: boolean;
  currentLocation: GeolocationPosition | null;
  error: GeolocationPositionError | null;
  tracesCollected: number;
  tracesSent: number;
}

export function useLocationTracking(options: UseLocationTrackingOptions = {}) {
  const {
    enabled = false,
    trackingIntervalMs = 5000, // Track every 5 seconds
    sendIntervalMs = 30000, // Send batch every 30 seconds
    flightInfo,
    onLocationUpdate,
  } = options;

  const [state, setState] = useState<LocationTrackingState>({
    isTracking: false,
    currentLocation: null,
    error: null,
    tracesCollected: 0,
    tracesSent: 0,
  });

  const { showError } = useErrorToast();
  const watchIdRef = useRef<number | null>(null);
  const sessionIdRef = useRef<string>(generateSessionId());
  const pendingTracesRef = useRef<LocationTraceData[]>([]);
  const sendIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Generate unique session ID
  function generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Send pending traces to server
  const sendPendingTraces = useCallback(async () => {
    if (pendingTracesRef.current.length === 0 || !flightInfo) {
      return;
    }

    const traces = [...pendingTracesRef.current];
    pendingTracesRef.current = [];

    try {
      // Send each trace (in production, you might want to batch these)
      for (const trace of traces) {
        await apiClient.post('/location/trace', {
          session_id: sessionIdRef.current,
          airport_code: flightInfo.airportCode,
          airline: flightInfo.airline,
          flight_number: flightInfo.flightNumber,
          terminal: flightInfo.terminal,
          ...trace,
        });
      }

      setState(prev => ({
        ...prev,
        tracesSent: prev.tracesSent + traces.length,
      }));
    } catch (error) {
      console.error('Failed to send location traces:', error);
      // Re-add failed traces to pending queue
      pendingTracesRef.current = [...traces, ...pendingTracesRef.current];
    }
  }, [flightInfo]);

  // Handle location update
  const handleLocationUpdate = useCallback((position: GeolocationPosition) => {
    const trace: LocationTraceData = {
      lat: position.coords.latitude,
      lng: position.coords.longitude,
      accuracy: position.coords.accuracy,
      speed: position.coords.speed ?? undefined,
      heading: position.coords.heading ?? undefined,
      timestamp: new Date().toISOString(),
    };

    // Update state
    setState(prev => ({
      ...prev,
      currentLocation: position,
      error: null,
      tracesCollected: prev.tracesCollected + 1,
    }));

    // Add to pending traces
    pendingTracesRef.current.push(trace);

    // Call callback if provided
    if (onLocationUpdate) {
      onLocationUpdate(trace);
    }
  }, [onLocationUpdate]);

  // Handle location error
  const handleLocationError = useCallback((error: GeolocationPositionError) => {
    console.error('Location error:', error);
    setState(prev => ({ ...prev, error, isTracking: false }));

    switch (error.code) {
      case error.PERMISSION_DENIED:
        showError(new Error('Location permission denied. Please enable location services.'));
        break;
      case error.POSITION_UNAVAILABLE:
        showError(new Error('Location information unavailable.'));
        break;
      case error.TIMEOUT:
        showError(new Error('Location request timed out.'));
        break;
    }
  }, [showError]);

  // Start tracking
  const startTracking = useCallback(() => {
    if (!navigator.geolocation) {
      showError(new Error('Geolocation is not supported by your browser'));
      return;
    }

    if (!flightInfo?.airportCode) {
      console.warn('Cannot start tracking without airport code');
      return;
    }

    // Request high accuracy for airport navigation
    const options: PositionOptions = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    };

    // Start watching position
    watchIdRef.current = navigator.geolocation.watchPosition(
      handleLocationUpdate,
      handleLocationError,
      options
    );

    // Setup interval to send traces
    sendIntervalRef.current = setInterval(sendPendingTraces, sendIntervalMs);

    setState(prev => ({ ...prev, isTracking: true, error: null }));
  }, [flightInfo, handleLocationUpdate, handleLocationError, sendPendingTraces, sendIntervalMs, showError]);

  // Stop tracking
  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }

    if (sendIntervalRef.current) {
      clearInterval(sendIntervalRef.current);
      sendIntervalRef.current = null;
    }

    // Send any remaining traces
    if (pendingTracesRef.current.length > 0) {
      sendPendingTraces();
    }

    setState(prev => ({ ...prev, isTracking: false }));
  }, [sendPendingTraces]);

  // Effect to start/stop tracking based on enabled prop
  useEffect(() => {
    if (enabled) {
      startTracking();
    } else {
      stopTracking();
    }

    return () => {
      stopTracking();
    };
  }, [enabled, startTracking, stopTracking]);

  return {
    ...state,
    startTracking,
    stopTracking,
    sessionId: sessionIdRef.current,
  };
}

/**
 * Hook to get discovered checkpoints for visualization
 */
export function useDiscoveredCheckpoints(airportCode: string, airline?: string) {
  const [checkpoints, setCheckpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { showError } = useErrorToast();

  useEffect(() => {
    if (!airportCode) return;

    const fetchCheckpoints = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams({ airport_code: airportCode });
        if (airline) params.append('airline', airline);

        const response = await apiClient.get(
          `/location/checkpoints/${airportCode}${airline ? `?airline=${airline}` : ''}`
        );
        setCheckpoints(response.data);
        setError(null);
      } catch (err) {
        const error = err as Error;
        setError(error);
        showError(error);
      } finally {
        setLoading(false);
      }
    };

    fetchCheckpoints();
  }, [airportCode, airline, showError]);

  return { checkpoints, loading, error };
}

/**
 * Hook to get airline checkpoint suggestions
 */
export function useAirlineCheckpointSuggestions(airportCode: string) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { showError } = useErrorToast();

  useEffect(() => {
    if (!airportCode) return;

    const fetchSuggestions = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get(
          `/location/airline-suggestions/${airportCode}`
        );
        setSuggestions(response.data);
        setError(null);
      } catch (err) {
        const error = err as Error;
        setError(error);
        showError(error);
      } finally {
        setLoading(false);
      }
    };

    fetchSuggestions();
  }, [airportCode, showError]);

  return { suggestions, loading, error };
}
