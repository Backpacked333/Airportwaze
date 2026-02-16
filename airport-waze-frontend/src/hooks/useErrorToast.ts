import { toast } from 'sonner';
import { ApiError } from '../lib/api-client';

/**
 * Error types for categorization
 */
export enum ErrorType {
  NETWORK = 'network',
  VALIDATION = 'validation',
  SERVER = 'server',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  NOT_FOUND = 'not_found',
  UNKNOWN = 'unknown',
}

/**
 * Error toast configuration
 */
interface ErrorToastConfig {
  title?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Default error messages by type
 */
const DEFAULT_ERROR_MESSAGES: Record<ErrorType, string> = {
  [ErrorType.NETWORK]: 'Network error. Please check your connection and try again.',
  [ErrorType.VALIDATION]: 'Please check your input and try again.',
  [ErrorType.SERVER]: 'Server error. Please try again later.',
  [ErrorType.AUTHENTICATION]: 'Please log in to continue.',
  [ErrorType.AUTHORIZATION]: 'You do not have permission to perform this action.',
  [ErrorType.NOT_FOUND]: 'The requested resource was not found.',
  [ErrorType.UNKNOWN]: 'An unexpected error occurred. Please try again.',
};

/**
 * Categorize error based on status code or error properties
 */
function categorizeError(error: ApiError | Error | unknown): ErrorType {
  // Handle ApiError
  if (typeof error === 'object' && error !== null && 'status' in error) {
    const apiError = error as ApiError;
    const status = apiError.status;

    if (!status || status === 0) {
      return ErrorType.NETWORK;
    }

    if (status === 400 || status === 422) {
      return ErrorType.VALIDATION;
    }

    if (status === 401) {
      return ErrorType.AUTHENTICATION;
    }

    if (status === 403) {
      return ErrorType.AUTHORIZATION;
    }

    if (status === 404) {
      return ErrorType.NOT_FOUND;
    }

    if (status >= 500) {
      return ErrorType.SERVER;
    }
  }

  // Handle Error objects
  if (error instanceof Error) {
    if (error.message.toLowerCase().includes('network')) {
      return ErrorType.NETWORK;
    }

    if (error.message.toLowerCase().includes('validation')) {
      return ErrorType.VALIDATION;
    }
  }

  return ErrorType.UNKNOWN;
}

/**
 * Format error message for display
 */
function formatErrorMessage(error: ApiError | Error | unknown): string {
  // Handle ApiError
  if (typeof error === 'object' && error !== null && 'message' in error) {
    const apiError = error as ApiError;
    return apiError.message || DEFAULT_ERROR_MESSAGES[ErrorType.UNKNOWN];
  }

  // Handle Error objects
  if (error instanceof Error) {
    return error.message || DEFAULT_ERROR_MESSAGES[ErrorType.UNKNOWN];
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }

  return DEFAULT_ERROR_MESSAGES[ErrorType.UNKNOWN];
}

/**
 * Format validation errors
 */
function formatValidationErrors(errors?: Record<string, string[]>): string | undefined {
  if (!errors || Object.keys(errors).length === 0) {
    return undefined;
  }

  const errorMessages = Object.entries(errors)
    .map(([field, messages]) => {
      const fieldName = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
      return `${fieldName}: ${messages.join(', ')}`;
    })
    .join('\n');

  return errorMessages;
}

/**
 * Custom hook for displaying error toasts
 *
 * Features:
 * - Categorize errors (network, validation, server, etc.)
 * - User-friendly error messages
 * - Integration with sonner toast library
 * - Support for validation errors
 * - Customizable configuration
 *
 * Usage:
 * ```ts
 * const { showError, showValidationError, showNetworkError } = useErrorToast();
 *
 * // Show generic error
 * showError(error);
 *
 * // Show error with custom message
 * showError(error, { title: 'Failed to load data' });
 *
 * // Show validation error with field details
 * showValidationError(apiError);
 * ```
 */
export function useErrorToast() {
  /**
   * Show error toast with automatic categorization
   */
  const showError = (error: ApiError | Error | unknown, config?: ErrorToastConfig) => {
    const errorType = categorizeError(error);
    const message = formatErrorMessage(error);
    const title = config?.title || DEFAULT_ERROR_MESSAGES[errorType];

    // Check for validation errors
    if (
      errorType === ErrorType.VALIDATION &&
      typeof error === 'object' &&
      error !== null &&
      'errors' in error
    ) {
      const apiError = error as ApiError;
      const validationDetails = formatValidationErrors(apiError.errors);

      if (validationDetails) {
        toast.error(title, {
          description: validationDetails,
          duration: config?.duration || 5000,
          action: config?.action,
        });
        return;
      }
    }

    toast.error(title, {
      description: message !== title ? message : undefined,
      duration: config?.duration || 4000,
      action: config?.action,
    });
  };

  /**
   * Show validation error with field details
   */
  const showValidationError = (error: ApiError, config?: ErrorToastConfig) => {
    const validationDetails = formatValidationErrors(error.errors);
    const message = error.message || DEFAULT_ERROR_MESSAGES[ErrorType.VALIDATION];

    toast.error(config?.title || 'Validation Error', {
      description: validationDetails || message,
      duration: config?.duration || 5000,
      action: config?.action,
    });
  };

  /**
   * Show network error
   */
  const showNetworkError = (config?: ErrorToastConfig) => {
    toast.error(config?.title || 'Network Error', {
      description: DEFAULT_ERROR_MESSAGES[ErrorType.NETWORK],
      duration: config?.duration || 4000,
      action: config?.action || {
        label: 'Retry',
        onClick: () => window.location.reload(),
      },
    });
  };

  /**
   * Show authentication error
   */
  const showAuthError = (config?: ErrorToastConfig) => {
    toast.error(config?.title || 'Authentication Required', {
      description: DEFAULT_ERROR_MESSAGES[ErrorType.AUTHENTICATION],
      duration: config?.duration || 4000,
      action: config?.action,
    });
  };

  /**
   * Show server error
   */
  const showServerError = (config?: ErrorToastConfig) => {
    toast.error(config?.title || 'Server Error', {
      description: DEFAULT_ERROR_MESSAGES[ErrorType.SERVER],
      duration: config?.duration || 4000,
      action: config?.action,
    });
  };

  /**
   * Show custom error message
   */
  const showCustomError = (message: string, config?: ErrorToastConfig) => {
    toast.error(config?.title || 'Error', {
      description: message,
      duration: config?.duration || 4000,
      action: config?.action,
    });
  };

  return {
    showError,
    showValidationError,
    showNetworkError,
    showAuthError,
    showServerError,
    showCustomError,
  };
}

/**
 * Standalone error toast function (for use outside of React components)
 */
export const showErrorToast = (error: ApiError | Error | unknown, config?: ErrorToastConfig) => {
  const errorType = categorizeError(error);
  const message = formatErrorMessage(error);
  const title = config?.title || DEFAULT_ERROR_MESSAGES[errorType];

  // Check for validation errors
  if (
    errorType === ErrorType.VALIDATION &&
    typeof error === 'object' &&
    error !== null &&
    'errors' in error
  ) {
    const apiError = error as ApiError;
    const validationDetails = formatValidationErrors(apiError.errors);

    if (validationDetails) {
      toast.error(title, {
        description: validationDetails,
        duration: config?.duration || 5000,
        action: config?.action,
      });
      return;
    }
  }

  toast.error(title, {
    description: message !== title ? message : undefined,
    duration: config?.duration || 4000,
    action: config?.action,
  });
};
