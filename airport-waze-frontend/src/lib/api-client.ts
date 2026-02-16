import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios';
import { env } from '../config/env';

/**
 * API Response wrapper type
 */
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

/**
 * API Error response type
 */
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  errors?: Record<string, string[]>;
}

/**
 * Request configuration with retry options
 */
interface RequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
  _retryCount?: number;
}

/**
 * Centralized API Client
 *
 * Features:
 * - Request/response interceptors
 * - Automatic retry logic for failed requests
 * - Authentication token handling
 * - Type-safe requests and responses
 * - Centralized error handling
 */
class ApiClient {
  private client: AxiosInstance;
  private readonly MAX_RETRIES = 3;
  private readonly RETRY_DELAY = 1000; // 1 second
  private authToken: string | null = null;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Set up request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add authentication token if available
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }

        // Log request in development
        if (import.meta.env.DEV) {
          console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
            params: config.params,
            data: config.data,
          });
        }

        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response in development
        if (import.meta.env.DEV) {
          console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
            status: response.status,
            data: response.data,
          });
        }

        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as RequestConfig;

        // Handle network errors with retry logic
        if (this.shouldRetry(error, originalRequest)) {
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

          if (import.meta.env.DEV) {
            console.log(
              `[API Retry] Attempt ${originalRequest._retryCount}/${this.MAX_RETRIES} for ${originalRequest.url}`
            );
          }

          // Wait before retrying (exponential backoff)
          await this.delay(this.RETRY_DELAY * originalRequest._retryCount);

          return this.client(originalRequest);
        }

        // Handle 401 Unauthorized - clear token and redirect to login
        if (error.response?.status === 401) {
          this.clearAuthToken();
          // Optionally redirect to login page
          // window.location.href = '/login';
        }

        // Log error in development
        if (import.meta.env.DEV) {
          console.error('[API Error]', {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            data: error.response?.data,
            message: error.message,
          });
        }

        return Promise.reject(this.normalizeError(error));
      }
    );
  }

  /**
   * Determine if request should be retried
   */
  private shouldRetry(error: AxiosError, config?: RequestConfig): boolean {
    if (!config || config._retry === false) {
      return false;
    }

    const retryCount = config._retryCount || 0;
    if (retryCount >= this.MAX_RETRIES) {
      return false;
    }

    // Retry on network errors or 5xx server errors
    const isNetworkError = !error.response;
    const isServerError = error.response?.status ? error.response.status >= 500 : false;
    const isTimeout = error.code === 'ECONNABORTED';

    return isNetworkError || isServerError || isTimeout;
  }

  /**
   * Delay utility for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Normalize error to consistent format
   */
  private normalizeError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error
      const data = error.response.data as any;
      return {
        message: data?.message || data?.error || 'An error occurred',
        code: data?.code,
        status: error.response.status,
        errors: data?.errors,
      };
    } else if (error.request) {
      // Request made but no response
      return {
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR',
      };
    } else {
      // Something else happened
      return {
        message: error.message || 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
      };
    }
  }

  /**
   * Set authentication token
   */
  public setAuthToken(token: string): void {
    this.authToken = token;
    // Optionally persist to localStorage
    localStorage.setItem('auth_token', token);
  }

  /**
   * Clear authentication token
   */
  public clearAuthToken(): void {
    this.authToken = null;
    localStorage.removeItem('auth_token');
  }

  /**
   * Load authentication token from storage
   */
  public loadAuthToken(): void {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.authToken = token;
    }
  }

  /**
   * GET request
   */
  public async get<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return response.data;
  }

  /**
   * POST request
   */
  public async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  /**
   * PUT request
   */
  public async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  /**
   * PATCH request
   */
  public async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  /**
   * DELETE request
   */
  public async delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return response.data;
  }

  /**
   * Get the underlying axios instance
   */
  public getClient(): AxiosInstance {
    return this.client;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient(env.API_URL);

// Load auth token on initialization
apiClient.loadAuthToken();

// Export the class for testing or creating additional instances
export { ApiClient };
