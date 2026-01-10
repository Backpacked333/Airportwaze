/**
 * Location Tracking Panel Component
 *
 * Displays location tracking status, motion detection, and zone information.
 * Shows real-time updates as the user moves through the airport.
 */

import { useLocationTracking } from '../hooks/useLocationTracking';
import { ZoneDwell } from '../services/locationTracking';
import { useState } from 'react';

interface LocationTrackingPanelProps {
  airportCode: string;
  checkpoints: Array<{
    id: string;
    lat: number;
    lng: number;
    type: string;
    name: string;
  }>;
  onZoneDwell?: (dwell: ZoneDwell) => void;
}

export function LocationTrackingPanel({
  airportCode,
  checkpoints,
  onZoneDwell
}: LocationTrackingPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleZoneDwell = async (dwell: ZoneDwell) => {
    // Auto-report zone dwell to backend
    try {
      const response = await fetch('http://localhost:8000/api/telemetry/zone-dwell', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          zone_id: dwell.zoneId,
          zone_type: dwell.zoneType,
          enter_time: dwell.enterTime.toISOString(),
          exit_time: dwell.exitTime.toISOString(),
          dwell_seconds: dwell.dwellSeconds,
          confidence: dwell.confidence
        })
      });

      if (response.ok) {
        console.log('[LocationTracking] Zone dwell reported successfully');
      }
    } catch (error) {
      console.error('[LocationTracking] Failed to report zone dwell:', error);
    }

    // Call user's callback
    if (onZoneDwell) {
      onZoneDwell(dwell);
    }
  };

  const {
    isTracking,
    locationState,
    stats,
    startTracking,
    stopTracking,
    error
  } = useLocationTracking({
    airportCode,
    checkpoints,
    enabled: true,
    onZoneDwell: handleZoneDwell
  });

  return (
    <div className="fixed top-4 right-4 z-40">
      {/* Collapsed State - Floating Button */}
      {!isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className={`rounded-full p-3 shadow-lg transition-colors ${
            isTracking
              ? 'bg-green-500 hover:bg-green-600 animate-pulse'
              : 'bg-gray-500 hover:bg-gray-600'
          }`}
        >
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>

          {/* Status Badge */}
          {isTracking && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-ping" />
          )}
        </button>
      )}

      {/* Expanded State - Full Panel */}
      {isExpanded && (
        <div className="bg-white rounded-lg shadow-xl p-4 w-80 max-w-[calc(100vw-2rem)]">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Location Tracking
            </h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Tracking Toggle */}
          <div className="mb-4">
            <button
              onClick={() => (isTracking ? stopTracking() : startTracking())}
              className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                isTracking
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              }`}
            >
              {isTracking ? '⏸️ Stop Tracking' : '▶️ Start Tracking'}
            </button>
          </div>

          {/* Status Info */}
          {isTracking && (
            <div className="space-y-3">
              {/* Motion State */}
              <div className="flex items-center gap-2">
                <div className="flex-shrink-0">
                  {locationState.isWalking && (
                    <span className="text-2xl">🚶</span>
                  )}
                  {locationState.isWaiting && (
                    <span className="text-2xl">⏳</span>
                  )}
                  {!locationState.isWalking && !locationState.isWaiting && (
                    <span className="text-2xl">📍</span>
                  )}
                </div>
                <div className="flex-grow">
                  <p className="text-sm font-medium text-gray-900">
                    {locationState.isWalking && 'Walking'}
                    {locationState.isWaiting && 'Waiting in Queue'}
                    {!locationState.isWalking && !locationState.isWaiting && 'Stationary'}
                  </p>
                  <p className="text-xs text-gray-500">
                    Speed: {(locationState.speed * 3.6).toFixed(1)} km/h
                  </p>
                </div>
              </div>

              {/* Zone Info */}
              {locationState.isInZone && locationState.currentZone && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">📍</span>
                    <p className="text-sm font-medium text-blue-900">
                      In Zone
                    </p>
                  </div>
                  <p className="text-xs text-blue-700">
                    {checkpoints.find(c => c.id === locationState.currentZone)?.name || 'Unknown'}
                  </p>
                  {locationState.zoneEntryTime && (
                    <p className="text-xs text-blue-600 mt-1">
                      Entered: {Math.round((Date.now() - locationState.zoneEntryTime.getTime()) / 1000)}s ago
                    </p>
                  )}
                </div>
              )}

              {/* Stats */}
              <div className="border-t pt-3 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Points Collected:</span>
                  <span className="font-medium text-gray-900">{stats.pointsCollected}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Battery:</span>
                  <span className={`font-medium ${
                    stats.batteryLevel > 0.5 ? 'text-green-600' :
                    stats.batteryLevel > 0.2 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {(stats.batteryLevel * 100).toFixed(0)}%
                    {stats.isCharging && ' ⚡'}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Sample Rate:</span>
                  <span className="font-medium text-gray-900">
                    {(stats.sampleInterval / 1000).toFixed(0)}s
                  </span>
                </div>
              </div>

              {/* Privacy Notice */}
              <div className="border-t pt-3">
                <p className="text-xs text-gray-500 leading-relaxed">
                  🔒 Your location data is anonymous and helps improve wait time predictions for all users.
                  K-anonymity protection (min 10 users) ensures privacy.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
