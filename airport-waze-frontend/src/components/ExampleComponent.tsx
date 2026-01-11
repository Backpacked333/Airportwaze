/**
 * Example Component
 *
 * This component demonstrates how to integrate all production-ready features:
 * - API Client for data fetching
 * - Error Toast Hook for error handling
 * - Loading States for better UX
 * - Type-safe API calls
 *
 * You can use this as a reference when building your own components.
 */

import { useState, useEffect } from 'react';
import { airportService } from '../services/airport.service';
import { useErrorToast } from '../hooks/useErrorToast';
import {
  LoadingSpinner,
  CardSkeleton,
  InlineLoading,
} from './LoadingState';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import type { Airport, PredictionResponse } from '../types/api';

/**
 * Example: Airport List Component
 *
 * Demonstrates:
 * - Loading states with skeleton loaders
 * - Error handling with error toast
 * - Type-safe API calls
 * - Success notifications
 */
export function AirportListExample() {
  const [airports, setAirports] = useState<Airport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { showError } = useErrorToast();

  useEffect(() => {
    loadAirports();
  }, []);

  const loadAirports = async () => {
    try {
      setIsLoading(true);
      const data = await airportService.getAirports();
      setAirports(data);
      toast.success('Airports loaded successfully');
    } catch (error) {
      showError(error, {
        title: 'Failed to load airports',
        action: {
          label: 'Retry',
          onClick: loadAirports,
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <CardSkeleton count={3} />
      </div>
    );
  }

  if (airports.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">No airports found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {airports.map((airport) => (
        <Card key={airport.id}>
          <CardHeader>
            <CardTitle>{airport.name}</CardTitle>
            <CardDescription>
              {airport.code} - {airport.city}, {airport.country}
            </CardDescription>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}

/**
 * Example: Prediction Component
 *
 * Demonstrates:
 * - Form submission with loading state
 * - Inline loading indicators
 * - Error handling with specific error types
 * - Success state management
 */
export function PredictionExample() {
  const [airportId, setAirportId] = useState('SFO');
  const [departureTime, setDepartureTime] = useState<Date>(new Date());
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { showError, showValidationError } = useErrorToast();

  const handleGetPrediction = async () => {
    // Validation
    if (!airportId) {
      showValidationError({
        message: 'Please select an airport',
        errors: { airport_id: ['Airport is required'] },
      });
      return;
    }

    try {
      setIsLoading(true);
      const data = await airportService.getPredictions(airportId, departureTime);
      setPrediction(data);
      toast.success('Prediction generated successfully');
    } catch (error) {
      showError(error, {
        title: 'Failed to get prediction',
        action: {
          label: 'Try Again',
          onClick: handleGetPrediction,
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Wait Time Prediction</CardTitle>
        <CardDescription>Get predicted wait times for your flight</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Airport</label>
          <input
            type="text"
            value={airportId}
            onChange={(e) => setAirportId(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="Enter airport code (e.g., SFO)"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Departure Time</label>
          <input
            type="datetime-local"
            value={departureTime.toISOString().slice(0, 16)}
            onChange={(e) => setDepartureTime(new Date(e.target.value))}
            className="w-full p-2 border rounded"
            disabled={isLoading}
          />
        </div>

        <Button onClick={handleGetPrediction} disabled={isLoading} className="w-full">
          {isLoading ? <InlineLoading text="Generating prediction..." /> : 'Get Prediction'}
        </Button>

        {prediction && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <h3 className="font-semibold mb-2">Prediction Results</h3>
            <div className="space-y-2 text-sm">
              <p>
                <span className="font-medium">Recommended Arrival Time:</span>{' '}
                {new Date(prediction.recommended_arrival_time).toLocaleTimeString()}
              </p>
              <p>
                <span className="font-medium">Total Estimated Time:</span>{' '}
                {prediction.total_estimated_time} minutes
              </p>
              <p>
                <span className="font-medium">Confidence:</span>{' '}
                <span className="capitalize">{prediction.confidence_level}</span>
              </p>
            </div>

            <div className="mt-4 space-y-2">
              <h4 className="font-medium text-sm">Checkpoint Predictions:</h4>
              {prediction.predictions.map((pred) => (
                <div
                  key={pred.checkpoint_id}
                  className="p-2 bg-background rounded border"
                >
                  <div className="flex justify-between items-center">
                    <span className="text-sm">{pred.checkpoint_name}</span>
                    <span className="text-sm font-medium">
                      {pred.predicted_wait_time} min
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Confidence: {Math.round(pred.confidence * 100)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Example: Search Component with Debounce
 *
 * Demonstrates:
 * - Debounced API calls
 * - Loading state management
 * - Error handling
 * - Empty state handling
 */
export function SearchExample() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Airport[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const { showError } = useErrorToast();

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timeoutId = setTimeout(() => {
      searchAirports(query);
    }, 500); // Debounce 500ms

    return () => clearTimeout(timeoutId);
  }, [query]);

  const searchAirports = async (searchQuery: string) => {
    try {
      setIsSearching(true);
      const data = await airportService.searchAirports(searchQuery);
      setResults(data);
    } catch (error) {
      showError(error, { title: 'Search failed' });
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Search Airports</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, code, or city..."
            className="w-full p-2 pr-10 border rounded"
          />
          {isSearching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <LoadingSpinner size="sm" />
            </div>
          )}
        </div>

        {results.length > 0 && (
          <div className="space-y-2">
            {results.map((airport) => (
              <div
                key={airport.id}
                className="p-3 border rounded hover:bg-muted cursor-pointer"
              >
                <div className="font-medium">
                  {airport.name} ({airport.code})
                </div>
                <div className="text-sm text-muted-foreground">
                  {airport.city}, {airport.country}
                </div>
              </div>
            ))}
          </div>
        )}

        {query && !isSearching && results.length === 0 && (
          <p className="text-center text-muted-foreground text-sm">No results found</p>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Example: Component with Error Boundary
 *
 * Demonstrates:
 * - Using ErrorBoundary for component-level error handling
 * - Intentional error for testing
 */
export function ErrorBoundaryExample() {
  const [shouldError, setShouldError] = useState(false);

  if (shouldError) {
    throw new Error('Intentional error for testing ErrorBoundary');
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Error Boundary Test</CardTitle>
        <CardDescription>
          Click the button below to trigger an error and see the ErrorBoundary in action
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button onClick={() => setShouldError(true)} variant="destructive">
          Trigger Error
        </Button>
      </CardContent>
    </Card>
  );
}

// Main component combining all examples
export default function ExampleComponents() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Production Features Examples</h1>

      <div className="grid gap-6 md:grid-cols-2">
        <AirportListExample />
        <SearchExample />
      </div>

      <PredictionExample />

      <ErrorBoundaryExample />
    </div>
  );
}
