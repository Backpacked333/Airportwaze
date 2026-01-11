/**
 * Checkpoint Discovery Map Component
 *
 * Visualizes AI-discovered checkpoints and heatmap data on the map.
 * Shows:
 * - Airline-specific check-in counters (discovered from user behavior)
 * - Security checkpoint queues
 * - High-traffic areas (heatmap)
 * - Confidence scores for each discovery
 */
import React, { useEffect, useState } from 'react';
import { Circle, Popup, Tooltip } from 'react-leaflet';
import { apiClient } from '@/lib/api-client';
import { useErrorToast } from '@/hooks/useErrorToast';

interface DiscoveredCheckpoint {
  id: number;
  airport_code: string;
  terminal?: string;
  center_lat: number;
  center_lng: number;
  radius_meters: number;
  checkpoint_type: string;
  airline?: string;
  confidence_score: number;
  sample_size: number;
  avg_dwell_time_seconds?: number;
  is_verified: boolean;
}

interface CheckpointDiscoveryMapProps {
  airportCode: string;
  airline?: string;
  showAll?: boolean;
  minConfidence?: number;
}

const CHECKPOINT_TYPE_COLORS: Record<string, string> = {
  airline_checkin: '#3b82f6', // Blue
  security_queue: '#ef4444', // Red
  gate_waiting: '#22c55e', // Green
  service_counter: '#f59e0b', // Orange
  general_waiting: '#8b5cf6', // Purple
  unknown: '#64748b', // Gray
};

const CHECKPOINT_TYPE_LABELS: Record<string, string> = {
  airline_checkin: 'Check-in Counter',
  security_queue: 'Security Checkpoint',
  gate_waiting: 'Gate Area',
  service_counter: 'Service Counter',
  general_waiting: 'Waiting Area',
  unknown: 'Unknown',
};

export function CheckpointDiscoveryMap({
  airportCode,
  airline,
  showAll = false,
  minConfidence = 0.5,
}: CheckpointDiscoveryMapProps) {
  const [checkpoints, setCheckpoints] = useState<DiscoveredCheckpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const { showError } = useErrorToast();

  useEffect(() => {
    const fetchCheckpoints = async () => {
      if (!airportCode) return;

      try {
        setLoading(true);
        const params = new URLSearchParams({
          min_confidence: minConfidence.toString(),
        });

        if (airline && !showAll) {
          params.append('airline', airline);
        }

        const response = await apiClient.get(
          `/location/checkpoints/${airportCode}?${params.toString()}`
        );

        setCheckpoints(response.data);
      } catch (error) {
        console.error('Failed to fetch discovered checkpoints:', error);
        showError(error as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchCheckpoints();
  }, [airportCode, airline, showAll, minConfidence, showError]);

  if (loading) {
    return null;
  }

  return (
    <>
      {checkpoints.map((checkpoint) => {
        const color =
          CHECKPOINT_TYPE_COLORS[checkpoint.checkpoint_type] ||
          CHECKPOINT_TYPE_COLORS.unknown;

        const opacity = Math.max(0.3, checkpoint.confidence_score);
        const fillOpacity = Math.max(0.1, checkpoint.confidence_score * 0.5);

        return (
          <Circle
            key={checkpoint.id}
            center={[checkpoint.center_lat, checkpoint.center_lng]}
            radius={checkpoint.radius_meters}
            pathOptions={{
              color: color,
              fillColor: color,
              opacity: opacity,
              fillOpacity: fillOpacity,
              weight: checkpoint.is_verified ? 3 : 2,
              dashArray: checkpoint.is_verified ? undefined : '5, 5',
            }}
          >
            <Popup>
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-sm">
                      {CHECKPOINT_TYPE_LABELS[checkpoint.checkpoint_type] ||
                        checkpoint.checkpoint_type}
                    </h3>
                    {checkpoint.airline && (
                      <p className="text-xs text-gray-600">{checkpoint.airline}</p>
                    )}
                  </div>
                  {checkpoint.is_verified && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      Verified
                    </span>
                  )}
                </div>

                <div className="text-xs text-gray-600 space-y-1">
                  {checkpoint.terminal && (
                    <p>
                      <span className="font-medium">Terminal:</span>{' '}
                      {checkpoint.terminal}
                    </p>
                  )}
                  <p>
                    <span className="font-medium">Confidence:</span>{' '}
                    {(checkpoint.confidence_score * 100).toFixed(0)}%
                  </p>
                  <p>
                    <span className="font-medium">Sample Size:</span>{' '}
                    {checkpoint.sample_size} observations
                  </p>
                  {checkpoint.avg_dwell_time_seconds && (
                    <p>
                      <span className="font-medium">Avg. Wait:</span>{' '}
                      {Math.round(checkpoint.avg_dwell_time_seconds / 60)} minutes
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-2">
                    💡 Discovered from crowdsourced user location data
                  </p>
                </div>
              </div>
            </Popup>

            <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
              <span className="text-xs">
                {checkpoint.airline
                  ? `${checkpoint.airline} Check-in`
                  : CHECKPOINT_TYPE_LABELS[checkpoint.checkpoint_type]}
                {' - '}
                {(checkpoint.confidence_score * 100).toFixed(0)}% confidence
              </span>
            </Tooltip>
          </Circle>
        );
      })}
    </>
  );
}

/**
 * Legend component for discovered checkpoints
 */
export function CheckpointDiscoveryLegend() {
  return (
    <div className="bg-white p-3 rounded-lg shadow-md space-y-2">
      <h4 className="font-semibold text-sm mb-2">Discovered Checkpoints</h4>
      {Object.entries(CHECKPOINT_TYPE_LABELS).map(([type, label]) => (
        <div key={type} className="flex items-center gap-2 text-xs">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: CHECKPOINT_TYPE_COLORS[type] }}
          />
          <span>{label}</span>
        </div>
      ))}
      <div className="pt-2 mt-2 border-t border-gray-200 text-xs text-gray-600">
        <p>Solid line = Verified</p>
        <p>Dashed line = AI-discovered</p>
      </div>
    </div>
  );
}

/**
 * Component to show airline checkpoint suggestions
 */
interface AirlineSuggestionsProps {
  airportCode: string;
}

export function AirlineCheckpointSuggestions({ airportCode }: AirlineSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { showError } = useErrorToast();

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!airportCode) return;

      try {
        setLoading(true);
        const response = await apiClient.get(
          `/location/airline-suggestions/${airportCode}`
        );
        setSuggestions(response.data);
      } catch (error) {
        console.error('Failed to fetch airline suggestions:', error);
        showError(error as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchSuggestions();
  }, [airportCode, showError]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return (
      <div className="text-sm text-gray-600">
        No airline check-in suggestions available yet. As more users navigate the
        airport, our AI will discover airline-specific check-in counters.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-lg">AI-Discovered Airline Check-ins</h3>
      <div className="grid gap-3">
        {suggestions.map((suggestion, idx) => (
          <div
            key={idx}
            className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-medium">{suggestion.airline}</h4>
                {suggestion.terminal && (
                  <p className="text-sm text-gray-600">
                    Terminal: {suggestion.terminal}
                  </p>
                )}
              </div>
              <div className="text-right">
                <div className="text-sm font-medium">
                  {(suggestion.confidence_score * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-600">confidence</div>
              </div>
            </div>

            <div className="mt-2 text-xs text-gray-600 space-y-1">
              <p>📍 Location: ({suggestion.suggested_lat.toFixed(6)}, {suggestion.suggested_lng.toFixed(6)})</p>
              <p>⏱️ Avg. wait: {Math.round(suggestion.avg_dwell_time_seconds / 60)} min</p>
              <p>👥 Based on {suggestion.sample_size} observations</p>
            </div>

            {suggestion.should_verify && (
              <div className="mt-2 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                ✓ High confidence - Ready for verification
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
