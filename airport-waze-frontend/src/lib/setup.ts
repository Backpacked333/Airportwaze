/**
 * Application Setup & Initialization
 *
 * This file contains setup functions that should be called before the app starts.
 * It initializes error tracking, analytics, and other global services.
 */

import { initSentry } from './sentry';
import { env } from '../config/env';

/**
 * Initialize all application services
 *
 * Call this function before rendering the React app
 */
export function initializeApp(): void {
  console.log('[App] Initializing AirportWaze...');

  // 1. Initialize error tracking
  initSentry();

  // 2. Initialize analytics (if enabled)
  if (env.ENABLE_ANALYTICS && env.ANALYTICS_ID) {
    initAnalytics();
  }

  // 3. Setup global error handlers
  setupGlobalErrorHandlers();

  // 4. Log environment info in development
  if (import.meta.env.DEV) {
    logEnvironmentInfo();
  }

  console.log('[App] Initialization complete');
}

/**
 * Initialize analytics
 */
function initAnalytics(): void {
  try {
    // Initialize Google Analytics, Mixpanel, or other analytics services here
    console.log('[Analytics] Initialized');

    // Example for Google Analytics
    // if (window.gtag) {
    //   window.gtag('config', env.ANALYTICS_ID);
    // }
  } catch (error) {
    console.error('[Analytics] Failed to initialize:', error);
  }
}

/**
 * Setup global error handlers
 */
function setupGlobalErrorHandlers(): void {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('[Unhandled Promise Rejection]', event.reason);

    // Report to error tracking service
    if (env.ENABLE_ERROR_TRACKING && window.Sentry) {
      window.Sentry.captureException(event.reason);
    }
  });

  // Handle global errors
  window.addEventListener('error', (event) => {
    console.error('[Global Error]', event.error);

    // Report to error tracking service
    if (env.ENABLE_ERROR_TRACKING && window.Sentry) {
      window.Sentry.captureException(event.error);
    }
  });
}

/**
 * Log environment information in development
 */
function logEnvironmentInfo(): void {
  console.group('[Environment Info]');
  console.log('App Name:', env.APP_NAME);
  console.log('App Version:', env.APP_VERSION);
  console.log('API URL:', env.API_URL);
  console.log('Environment:', env.NODE_ENV);
  console.log('Analytics Enabled:', env.ENABLE_ANALYTICS);
  console.log('Error Tracking Enabled:', env.ENABLE_ERROR_TRACKING);
  console.groupEnd();
}

/**
 * Cleanup function for app shutdown (if needed)
 */
export function cleanupApp(): void {
  console.log('[App] Cleaning up...');
  // Perform any necessary cleanup here
}
