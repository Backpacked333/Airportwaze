import * as Sentry from '@sentry/react';
import { env, isProduction } from '../config/env';

/**
 * Initialize Sentry for error tracking
 *
 * This should be called before React renders the app
 */
export function initSentry(): void {
  // Only initialize if error tracking is enabled and DSN is provided
  if (!env.ENABLE_ERROR_TRACKING || !env.SENTRY_DSN) {
    if (!isProduction) {
      console.log('[Sentry] Error tracking is disabled or DSN is not configured');
    }
    return;
  }

  try {
    Sentry.init({
      dsn: env.SENTRY_DSN,
      environment: env.SENTRY_ENVIRONMENT,

      // Set sample rate for performance monitoring
      // In production, you might want to lower this to reduce quota usage
      tracesSampleRate: isProduction ? 0.1 : 1.0,

      // Integrations
      integrations: [
        // Automatically instrument React components
        Sentry.reactRouterV6BrowserTracingIntegration({
          useEffect: React.useEffect,
        }),

        // Capture console errors
        Sentry.captureConsoleIntegration({
          levels: ['error'],
        }),

        // Session replay for debugging (optional, can be resource-intensive)
        // Sentry.replayIntegration({
        //   maskAllText: true,
        //   blockAllMedia: true,
        // }),
      ],

      // Filter out common errors that aren't actionable
      ignoreErrors: [
        // Browser extensions
        'top.GLOBALS',
        'chrome-extension://',
        'moz-extension://',

        // Network errors that are expected
        'NetworkError',
        'Failed to fetch',
        'Load failed',

        // ResizeObserver errors (common and harmless)
        'ResizeObserver loop',
      ],

      // Before sending events, you can modify them here
      beforeSend(event, hint) {
        // Filter out events in development if needed
        if (!isProduction && event.level === 'info') {
          return null;
        }

        // Add additional context
        if (event.extra) {
          event.extra.appVersion = env.APP_VERSION;
        }

        return event;
      },

      // Set release version for better tracking
      release: `${env.APP_NAME}@${env.APP_VERSION}`,

      // Enable debug mode in development
      debug: !isProduction,
    });

    // Set user context if available
    const userId = localStorage.getItem('user_id');
    if (userId) {
      Sentry.setUser({ id: userId });
    }

    console.log('[Sentry] Initialized successfully');
  } catch (error) {
    console.error('[Sentry] Failed to initialize:', error);
  }
}

/**
 * Capture an exception manually
 */
export function captureException(error: Error, context?: Record<string, any>): void {
  if (!env.ENABLE_ERROR_TRACKING) {
    console.error('[Sentry] Error captured (but not sent):', error, context);
    return;
  }

  Sentry.captureException(error, {
    extra: context,
  });
}

/**
 * Capture a message manually
 */
export function captureMessage(message: string, level: Sentry.SeverityLevel = 'info'): void {
  if (!env.ENABLE_ERROR_TRACKING) {
    console.log('[Sentry] Message captured (but not sent):', message);
    return;
  }

  Sentry.captureMessage(message, level);
}

/**
 * Set user context for error tracking
 */
export function setUser(user: { id: string; email?: string; username?: string }): void {
  if (!env.ENABLE_ERROR_TRACKING) {
    return;
  }

  Sentry.setUser(user);

  // Persist user ID for future sessions
  localStorage.setItem('user_id', user.id);
}

/**
 * Clear user context
 */
export function clearUser(): void {
  if (!env.ENABLE_ERROR_TRACKING) {
    return;
  }

  Sentry.setUser(null);
  localStorage.removeItem('user_id');
}

/**
 * Add breadcrumb for debugging
 */
export function addBreadcrumb(
  message: string,
  category: string = 'custom',
  level: Sentry.SeverityLevel = 'info',
  data?: Record<string, any>
): void {
  if (!env.ENABLE_ERROR_TRACKING) {
    return;
  }

  Sentry.addBreadcrumb({
    message,
    category,
    level,
    data,
    timestamp: Date.now() / 1000,
  });
}

/**
 * Wrap ErrorBoundary with Sentry
 */
export const SentryErrorBoundary = Sentry.ErrorBoundary;

// Import React for the integration
import React from 'react';
