import { z } from 'zod';

/**
 * Environment variable schema with validation rules
 */
const envSchema = z.object({
  // API Configuration
  API_URL: z.string().url('API_URL must be a valid URL'),

  // Feature Flags
  ENABLE_ANALYTICS: z
    .string()
    .optional()
    .default('false')
    .transform((val) => val === 'true'),

  ENABLE_ERROR_TRACKING: z
    .string()
    .optional()
    .default('false')
    .transform((val) => val === 'true'),

  // Error Tracking (Sentry)
  SENTRY_DSN: z.string().optional(),
  SENTRY_ENVIRONMENT: z
    .string()
    .optional()
    .default(() => (import.meta.env.PROD ? 'production' : 'development')),

  // Analytics
  ANALYTICS_ID: z.string().optional(),

  // App Configuration
  APP_NAME: z.string().optional().default('AirportWaze'),
  APP_VERSION: z.string().optional().default('1.0.0'),

  // Environment
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .optional()
    .default('development'),

  // Map Configuration
  MAP_DEFAULT_CENTER_LAT: z
    .string()
    .optional()
    .default('37.7749')
    .transform((val) => parseFloat(val)),

  MAP_DEFAULT_CENTER_LNG: z
    .string()
    .optional()
    .default('-122.4194')
    .transform((val) => parseFloat(val)),

  MAP_DEFAULT_ZOOM: z
    .string()
    .optional()
    .default('13')
    .transform((val) => parseInt(val, 10)),
});

/**
 * Type representing validated environment variables
 */
export type Env = z.infer<typeof envSchema>;

/**
 * Parse and validate environment variables from import.meta.env
 */
function parseEnv(): Env {
  const rawEnv = {
    API_URL: import.meta.env.VITE_API_URL,
    ENABLE_ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS,
    ENABLE_ERROR_TRACKING: import.meta.env.VITE_ENABLE_ERROR_TRACKING,
    SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
    SENTRY_ENVIRONMENT: import.meta.env.VITE_SENTRY_ENVIRONMENT,
    ANALYTICS_ID: import.meta.env.VITE_ANALYTICS_ID,
    APP_NAME: import.meta.env.VITE_APP_NAME,
    APP_VERSION: import.meta.env.VITE_APP_VERSION,
    NODE_ENV: import.meta.env.MODE,
    MAP_DEFAULT_CENTER_LAT: import.meta.env.VITE_MAP_DEFAULT_CENTER_LAT,
    MAP_DEFAULT_CENTER_LNG: import.meta.env.VITE_MAP_DEFAULT_CENTER_LNG,
    MAP_DEFAULT_ZOOM: import.meta.env.VITE_MAP_DEFAULT_ZOOM,
  };

  try {
    const parsed = envSchema.parse(rawEnv);
    return parsed;
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('Environment validation failed:');
      error.errors.forEach((err) => {
        console.error(`  - ${err.path.join('.')}: ${err.message}`);
      });

      // In production, throw error to prevent app from running with invalid config
      if (import.meta.env.PROD) {
        throw new Error('Invalid environment configuration. Please check your .env file.');
      }

      // In development, provide helpful error message
      throw new Error(
        `Environment validation failed:\n${error.errors
          .map((err) => `  - ${err.path.join('.')}: ${err.message}`)
          .join('\n')}`
      );
    }
    throw error;
  }
}

/**
 * Validated and typed environment variables
 *
 * Usage:
 * ```ts
 * import { env } from '@/config/env';
 *
 * const apiUrl = env.API_URL;
 * ```
 */
export const env = parseEnv();

/**
 * Check if running in development mode
 */
export const isDevelopment = env.NODE_ENV === 'development';

/**
 * Check if running in production mode
 */
export const isProduction = env.NODE_ENV === 'production';

/**
 * Check if running in test mode
 */
export const isTest = env.NODE_ENV === 'test';

/**
 * Export helper to check if a feature is enabled
 */
export const isFeatureEnabled = (feature: keyof Env): boolean => {
  const value = env[feature];
  return typeof value === 'boolean' ? value : false;
};

// Log environment info in development
if (isDevelopment) {
  console.log('[Environment Configuration]', {
    API_URL: env.API_URL,
    NODE_ENV: env.NODE_ENV,
    ENABLE_ANALYTICS: env.ENABLE_ANALYTICS,
    ENABLE_ERROR_TRACKING: env.ENABLE_ERROR_TRACKING,
  });
}
