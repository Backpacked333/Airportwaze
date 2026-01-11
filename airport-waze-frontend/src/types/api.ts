/**
 * API Type Definitions
 *
 * Type-safe definitions for API requests and responses
 */

// ==========================================
// Common Types
// ==========================================

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  errors?: Record<string, string[]>;
}

// ==========================================
// Airport Types
// ==========================================

export interface Airport {
  id: string;
  name: string;
  code: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface AirportDetails extends Airport {
  terminals: Terminal[];
  checkpoints: Checkpoint[];
  stats: AirportStats;
}

export interface Terminal {
  id: string;
  name: string;
  airport_id: string;
  checkpoints: Checkpoint[];
}

export interface Checkpoint {
  id: string;
  name: string;
  terminal_id: string;
  type: 'security' | 'immigration' | 'customs';
  status: 'open' | 'closed' | 'busy';
  current_wait_time?: number;
  average_wait_time?: number;
}

export interface AirportStats {
  total_checkpoints: number;
  average_wait_time: number;
  busiest_time: string;
  peak_wait_time: number;
  last_updated: string;
}

// ==========================================
// Prediction Types
// ==========================================

export interface WaitTimePrediction {
  checkpoint_id: string;
  checkpoint_name: string;
  predicted_wait_time: number;
  confidence: number;
  percentile_10: number;
  percentile_50: number;
  percentile_90: number;
  factors: PredictionFactors;
  timestamp: string;
}

export interface PredictionFactors {
  time_of_day: string;
  day_of_week: string;
  is_holiday: boolean;
  flight_volume: number;
  historical_average: number;
}

export interface PredictionRequest {
  airport_id: string;
  terminal_id?: string;
  checkpoint_id?: string;
  departure_time: string;
  current_time?: string;
}

export interface PredictionResponse {
  predictions: WaitTimePrediction[];
  recommended_arrival_time: string;
  total_estimated_time: number;
  confidence_level: 'low' | 'medium' | 'high';
}

// ==========================================
// Flight Types
// ==========================================

export interface Flight {
  id: string;
  flight_number: string;
  airline: string;
  departure_airport: string;
  arrival_airport: string;
  departure_time: string;
  arrival_time: string;
  status: 'scheduled' | 'delayed' | 'boarding' | 'departed' | 'cancelled';
  gate?: string;
  terminal?: string;
}

export interface FlightSearchParams {
  airport_code: string;
  date: string;
  type?: 'departure' | 'arrival';
  airline?: string;
}

// ==========================================
// Analytics Types
// ==========================================

export interface WaitTimeHistory {
  checkpoint_id: string;
  timestamp: string;
  wait_time: number;
  passenger_count?: number;
}

export interface CheckpointAnalytics {
  checkpoint_id: string;
  checkpoint_name: string;
  average_wait_time: number;
  peak_wait_time: number;
  peak_time: string;
  busiest_day: string;
  trend: 'increasing' | 'decreasing' | 'stable';
  history: WaitTimeHistory[];
}

export interface AirportAnalytics {
  airport_id: string;
  date_range: {
    start: string;
    end: string;
  };
  total_passengers: number;
  average_wait_time: number;
  checkpoints: CheckpointAnalytics[];
}

// ==========================================
// User Types
// ==========================================

export interface User {
  id: string;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfile extends User {
  preferences: UserPreferences;
  saved_airports: string[];
  notification_settings: NotificationSettings;
}

export interface UserPreferences {
  default_airport?: string;
  units: 'metric' | 'imperial';
  theme: 'light' | 'dark' | 'auto';
  language: string;
}

export interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  wait_time_alerts: boolean;
  flight_updates: boolean;
}

// ==========================================
// Authentication Types
// ==========================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  refresh_token: string;
  expires_at: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// ==========================================
// Feedback Types
// ==========================================

export interface FeedbackRequest {
  checkpoint_id: string;
  actual_wait_time: number;
  predicted_wait_time: number;
  rating: number; // 1-5
  comment?: string;
  timestamp: string;
}

export interface FeedbackResponse {
  id: string;
  message: string;
  accuracy_score: number;
}

// ==========================================
// Settings Types
// ==========================================

export interface AppSettings {
  maintenance_mode: boolean;
  features: {
    predictions_enabled: boolean;
    analytics_enabled: boolean;
    notifications_enabled: boolean;
  };
  version: string;
  api_version: string;
}

// ==========================================
// Search Types
// ==========================================

export interface SearchParams {
  query: string;
  type?: 'airport' | 'flight' | 'checkpoint';
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  type: 'airport' | 'flight' | 'checkpoint';
  id: string;
  name: string;
  description: string;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

// ==========================================
// Notification Types
// ==========================================

export interface Notification {
  id: string;
  user_id: string;
  type: 'wait_time_alert' | 'flight_update' | 'system' | 'promo';
  title: string;
  message: string;
  read: boolean;
  data?: Record<string, any>;
  created_at: string;
}

export interface NotificationPreferences {
  enabled: boolean;
  types: {
    wait_time_alerts: boolean;
    flight_updates: boolean;
    system_notifications: boolean;
    promotional: boolean;
  };
  channels: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
}
