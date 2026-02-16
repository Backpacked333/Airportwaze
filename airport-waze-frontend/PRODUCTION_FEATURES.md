# Production-Ready Features

This document describes the production-ready features added to the AirportWaze frontend and how to use them.

## Overview

The following production-ready features have been implemented:

1. **Error Boundary Component** - Catch and handle React errors gracefully
2. **API Client** - Centralized HTTP client with retry logic and error handling
3. **Error Toast Hook** - Display user-friendly error messages
4. **Loading State Components** - Skeleton loaders and loading indicators
5. **Environment Configuration** - Type-safe environment variable management
6. **Error Tracking** - Sentry integration for production error monitoring

## 1. Error Boundary Component

### Location
`/src/components/ErrorBoundary.tsx`

### Usage

Wrap your app or components with the ErrorBoundary:

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <YourApp />
    </ErrorBoundary>
  );
}
```

With custom error handler:

```tsx
<ErrorBoundary
  onError={(error, errorInfo) => {
    console.log('Custom error handler', error);
  }}
>
  <YourApp />
</ErrorBoundary>
```

### Features
- Catches unhandled React errors
- Displays user-friendly error message
- Reports errors to Sentry (if configured)
- Shows error details in development mode
- Provides reload and retry buttons

## 2. API Client

### Location
`/src/lib/api-client.ts`

### Usage

```tsx
import { apiClient } from '@/lib/api-client';

// GET request
const data = await apiClient.get('/airports');

// POST request
const result = await apiClient.post('/predictions', {
  airport_id: 'SFO',
  current_time: new Date().toISOString(),
});

// PUT request
await apiClient.put('/user/profile', userData);

// DELETE request
await apiClient.delete('/user/notification/123');
```

### Authentication

```tsx
// Set auth token (after login)
apiClient.setAuthToken('your-jwt-token');

// Clear auth token (after logout)
apiClient.clearAuthToken();
```

### Features
- Automatic retry logic for failed requests (3 retries with exponential backoff)
- Request/response interceptors
- Authentication token handling
- Type-safe requests and responses
- Automatic error normalization
- Request timeout (30 seconds)
- Development logging

## 3. Error Toast Hook

### Location
`/src/hooks/useErrorToast.ts`

### Usage

```tsx
import { useErrorToast } from '@/hooks/useErrorToast';

function MyComponent() {
  const { showError, showNetworkError, showValidationError } = useErrorToast();

  const handleSubmit = async () => {
    try {
      await apiClient.post('/data', formData);
    } catch (error) {
      // Automatically categorizes and displays error
      showError(error);
    }
  };

  return <button onClick={handleSubmit}>Submit</button>;
}
```

### Methods

```tsx
// Show generic error (auto-categorized)
showError(error);

// Show error with custom title
showError(error, { title: 'Failed to load data' });

// Show validation error with field details
showValidationError(apiError);

// Show network error
showNetworkError();

// Show authentication error
showAuthError();

// Show server error
showServerError();

// Show custom error message
showCustomError('Something went wrong');
```

### Error Categories
- Network errors
- Validation errors (with field details)
- Server errors (5xx)
- Authentication errors (401)
- Authorization errors (403)
- Not found errors (404)

## 4. Loading State Components

### Location
`/src/components/LoadingState.tsx`

### Components

#### LoadingSpinner
```tsx
import { LoadingSpinner } from '@/components/LoadingState';

<LoadingSpinner size="md" text="Loading..." />
```

#### LoadingOverlay
```tsx
import { LoadingOverlay } from '@/components/LoadingState';

<LoadingOverlay visible={isLoading} text="Processing..." />
```

#### Skeleton Loaders

```tsx
import {
  CardSkeleton,
  ListItemSkeleton,
  TableSkeleton,
  TextSkeleton,
  FormSkeleton,
} from '@/components/LoadingState';

// Show loading cards
<CardSkeleton count={3} />

// Show loading list items
<ListItemSkeleton count={5} showAvatar />

// Show loading table
<TableSkeleton rows={5} columns={4} />

// Show loading text
<TextSkeleton lines={3} />

// Show loading form
<FormSkeleton fields={4} />
```

#### Inline Loading
```tsx
import { InlineLoading, ButtonLoading } from '@/components/LoadingState';

// Inline loading indicator
<InlineLoading text="Saving..." />

// Button loading state
<Button disabled={isLoading}>
  {isLoading ? <ButtonLoading text="Submitting..." /> : 'Submit'}
</Button>
```

## 5. Environment Configuration

### Location
`/src/config/env.ts`

### Setup

1. Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

2. Configure your environment variables:
```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_ERROR_TRACKING=false
VITE_SENTRY_DSN=your-sentry-dsn
```

### Usage

```tsx
import { env, isDevelopment, isProduction } from '@/config/env';

// Access environment variables (type-safe)
const apiUrl = env.API_URL;
const appName = env.APP_NAME;

// Check environment
if (isDevelopment) {
  console.log('Running in development mode');
}

if (isProduction) {
  console.log('Running in production mode');
}

// Check feature flags
if (env.ENABLE_ANALYTICS) {
  initAnalytics();
}
```

### Features
- Type-safe environment variables
- Runtime validation with Zod
- Default values
- Automatic parsing (strings to booleans/numbers)
- Helpful error messages for missing/invalid variables

## 6. Error Tracking (Sentry)

### Location
`/src/lib/sentry.ts`

### Setup

1. Install dependencies:
```bash
npm install
```

2. Configure Sentry in `.env.local`:
```env
VITE_ENABLE_ERROR_TRACKING=true
VITE_SENTRY_DSN=your-sentry-dsn-here
VITE_SENTRY_ENVIRONMENT=development
```

3. Initialize in your app (see `main.enhanced.tsx`):
```tsx
import { initializeApp } from '@/lib/setup';

// Call before rendering
initializeApp();
```

### Manual Error Reporting

```tsx
import { captureException, captureMessage, setUser } from '@/lib/sentry';

// Capture exception
try {
  riskyOperation();
} catch (error) {
  captureException(error, { context: 'additional info' });
}

// Capture message
captureMessage('Important event occurred', 'info');

// Set user context
setUser({
  id: 'user-123',
  email: 'user@example.com',
  username: 'johndoe',
});
```

## Installation

1. Install new dependencies:
```bash
cd /home/user/Airportwaze/airport-waze-frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local with your settings
```

3. Update main.tsx (optional):
```bash
# Backup original
mv src/main.tsx src/main.tsx.backup

# Use enhanced version
mv src/main.enhanced.tsx src/main.tsx
```

4. Run the app:
```bash
npm run dev
```

## Production Deployment Checklist

- [ ] Configure production API URL in environment variables
- [ ] Set up Sentry project and add DSN
- [ ] Enable error tracking (`VITE_ENABLE_ERROR_TRACKING=true`)
- [ ] Configure analytics if needed
- [ ] Test error boundary with intentional errors
- [ ] Verify API client retry logic
- [ ] Test loading states
- [ ] Verify environment validation

## Example Integration

Here's a complete example integrating all features:

```tsx
import { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { useErrorToast } from '@/hooks/useErrorToast';
import { LoadingSpinner, CardSkeleton } from '@/components/LoadingState';

function AirportList() {
  const [airports, setAirports] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { showError } = useErrorToast();

  useEffect(() => {
    loadAirports();
  }, []);

  const loadAirports = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/airports');
      setAirports(response.data);
    } catch (error) {
      showError(error, { title: 'Failed to load airports' });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <CardSkeleton count={3} />;
  }

  return (
    <div>
      {airports.map(airport => (
        <AirportCard key={airport.id} airport={airport} />
      ))}
    </div>
  );
}
```

## Troubleshooting

### Error: "Environment validation failed"
- Check that all required environment variables are set in `.env.local`
- Ensure VITE_API_URL is a valid URL
- Verify no typos in variable names

### Errors not appearing in Sentry
- Check that `VITE_ENABLE_ERROR_TRACKING=true`
- Verify `VITE_SENTRY_DSN` is correct
- Check browser console for Sentry initialization messages
- Ensure Sentry project is active

### API requests failing
- Verify `VITE_API_URL` is correct
- Check network tab in browser DevTools
- Ensure backend is running
- Check CORS configuration

## Additional Resources

- [Sentry React Documentation](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Axios Documentation](https://axios-http.com/docs/intro)
- [Zod Documentation](https://zod.dev/)
- [Sonner Toast Documentation](https://sonner.emilkowal.ski/)
