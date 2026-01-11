import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from './ui/button';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary Component
 *
 * Catches unhandled React errors and displays a user-friendly error message.
 * Provides options to reload the page or report the error to tracking services.
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <YourApp />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Update state with error info
    this.setState({
      error,
      errorInfo,
    });

    // Report to error tracking service (e.g., Sentry)
    this.reportError(error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private reportError(error: Error, errorInfo: ErrorInfo) {
    try {
      // Check if Sentry is available
      if (window.Sentry) {
        window.Sentry.captureException(error, {
          contexts: {
            react: {
              componentStack: errorInfo.componentStack,
            },
          },
        });
      }
    } catch (reportError) {
      // Silently fail if error reporting fails
      console.error('Failed to report error:', reportError);
    }
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render() {
    if (this.state.hasError) {
      // If custom fallback is provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-background">
          <div className="max-w-md w-full space-y-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Something went wrong</AlertTitle>
              <AlertDescription>
                An unexpected error occurred. We've been notified and will look
                into it. Please try reloading the page.
              </AlertDescription>
            </Alert>

            {import.meta.env.DEV && this.state.error && (
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <h3 className="font-semibold mb-2 text-sm">Error Details (Development Only):</h3>
                <div className="space-y-2">
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Error:</p>
                    <pre className="text-xs mt-1 p-2 bg-background rounded overflow-auto">
                      {this.state.error.toString()}
                    </pre>
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">Component Stack:</p>
                      <pre className="text-xs mt-1 p-2 bg-background rounded overflow-auto max-h-48">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <Button onClick={this.handleReload} className="flex-1">
                Reload Page
              </Button>
              <Button onClick={this.handleReset} variant="outline" className="flex-1">
                Try Again
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Extend Window interface for Sentry
declare global {
  interface Window {
    Sentry?: {
      captureException: (error: Error, context?: any) => void;
    };
  }
}

export default ErrorBoundary;
