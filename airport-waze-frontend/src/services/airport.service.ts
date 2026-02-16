/**
 * Airport Service
 *
 * Example service demonstrating how to use the API client with TypeScript types
 * for type-safe API calls.
 *
 * Usage:
 * ```ts
 * import { airportService } from '@/services/airport.service';
 *
 * const airports = await airportService.getAirports();
 * const predictions = await airportService.getPredictions('SFO', new Date());
 * ```
 */

import { apiClient } from '../lib/api-client';
import type {
  Airport,
  AirportDetails,
  PredictionRequest,
  PredictionResponse,
  CheckpointAnalytics,
  FeedbackRequest,
  FeedbackResponse,
} from '../types/api';

class AirportService {
  /**
   * Get list of all airports
   */
  async getAirports(): Promise<Airport[]> {
    const response = await apiClient.get<Airport[]>('/airports');
    return response.data;
  }

  /**
   * Get airport details by ID or code
   */
  async getAirportDetails(airportIdOrCode: string): Promise<AirportDetails> {
    const response = await apiClient.get<AirportDetails>(`/airports/${airportIdOrCode}`);
    return response.data;
  }

  /**
   * Search airports by query
   */
  async searchAirports(query: string): Promise<Airport[]> {
    const response = await apiClient.get<Airport[]>('/airports/search', {
      params: { q: query },
    });
    return response.data;
  }

  /**
   * Get wait time predictions for an airport
   */
  async getPredictions(
    airportId: string,
    departureTime: Date,
    terminalId?: string
  ): Promise<PredictionResponse> {
    const request: PredictionRequest = {
      airport_id: airportId,
      departure_time: departureTime.toISOString(),
      current_time: new Date().toISOString(),
      terminal_id: terminalId,
    };

    const response = await apiClient.post<PredictionResponse>('/predictions', request);
    return response.data;
  }

  /**
   * Get checkpoint-specific prediction
   */
  async getCheckpointPrediction(
    checkpointId: string,
    departureTime: Date
  ): Promise<PredictionResponse> {
    const request: PredictionRequest = {
      airport_id: '', // Will be inferred from checkpoint
      checkpoint_id: checkpointId,
      departure_time: departureTime.toISOString(),
      current_time: new Date().toISOString(),
    };

    const response = await apiClient.post<PredictionResponse>(
      `/checkpoints/${checkpointId}/predictions`,
      request
    );
    return response.data;
  }

  /**
   * Get checkpoint analytics
   */
  async getCheckpointAnalytics(
    checkpointId: string,
    startDate: Date,
    endDate: Date
  ): Promise<CheckpointAnalytics> {
    const response = await apiClient.get<CheckpointAnalytics>(
      `/checkpoints/${checkpointId}/analytics`,
      {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
        },
      }
    );
    return response.data;
  }

  /**
   * Submit feedback for prediction accuracy
   */
  async submitFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse> {
    const response = await apiClient.post<FeedbackResponse>('/feedback', feedback);
    return response.data;
  }

  /**
   * Get nearby airports by coordinates
   */
  async getNearbyAirports(
    latitude: number,
    longitude: number,
    radius: number = 50
  ): Promise<Airport[]> {
    const response = await apiClient.get<Airport[]>('/airports/nearby', {
      params: {
        lat: latitude,
        lng: longitude,
        radius,
      },
    });
    return response.data;
  }

  /**
   * Get current wait times for an airport
   */
  async getCurrentWaitTimes(airportId: string): Promise<any> {
    const response = await apiClient.get(`/airports/${airportId}/wait-times`);
    return response.data;
  }
}

// Export singleton instance
export const airportService = new AirportService();

// Export class for testing or creating new instances
export { AirportService };
