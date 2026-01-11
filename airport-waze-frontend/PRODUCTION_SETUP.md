# Production-Ready Setup Guide

Quick reference guide for integrating the production-ready features into your AirportWaze frontend.

## Quick Start

### 1. Install Dependencies

```bash
cd /home/user/Airportwaze/airport-waze-frontend
npm install
```

This will install:
- `axios` - HTTP client for API calls
- `@sentry/react` - Error tracking and monitoring
- `zod` - Runtime validation (already installed)
- All other dependencies

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env.local

# Edit with your settings
nano .env.local
```

**Minimum required configuration:**
```env
VITE_API_URL=http://localhost:8000
```

**Recommended for production:**
```env
VITE_API_URL=https://app-awudjxxy.fly.dev
VITE_ENABLE_ERROR_TRACKING=true
VITE_SENTRY_DSN=your-sentry-dsn
VITE_SENTRY_ENVIRONMENT=production
```

### 3. Integrate into Your App

**Option A: Use the enhanced main.tsx (Recommended)**

```bash
# Backup original
mv src/main.tsx src/main.tsx.backup

# Use enhanced version
mv src/main.enhanced.tsx src/main.tsx
```

**Option B: Manual integration**

Update your `src/main.tsx`:

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';
import ErrorBoundary from './components/ErrorBoundary';
import { Toaster } from './components/ui/sonner';
import { initializeApp } from './lib/setup';

// Initialize app services
initializeApp();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
      <Toaster richColors position="top-right" />
    </ErrorBoundary>
  </StrictMode>
);
```

### 4. Start Development Server

```bash
npm run dev
```

## Created Files

### Core Features
1. **ErrorBoundary.tsx** - `/src/components/ErrorBoundary.tsx`
   - React error boundary for catching unhandled errors
   - User-friendly error display
   - Sentry integration

2. **api-client.ts** - `/src/lib/api-client.ts`
   - Centralized HTTP client with axios
   - Request/response interceptors
   - Automatic retry logic
   - Authentication handling

3. **useErrorToast.ts** - `/src/hooks/useErrorToast.ts`
   - Custom hook for error notifications
   - Categorized error messages
   - Integration with sonner toast library

4. **LoadingState.tsx** - `/src/components/LoadingState.tsx`
   - Loading spinners
   - Skeleton loaders
   - Loading overlay
   - Various loading components

5. **env.ts** - `/src/config/env.ts`
   - Type-safe environment configuration
   - Runtime validation with Zod
   - Default values

### Supporting Files
6. **sentry.ts** - `/src/lib/sentry.ts`
   - Sentry initialization
   - Error capture utilities

7. **setup.ts** - `/src/lib/setup.ts`
   - App initialization
   - Global error handlers

8. **api.ts** - `/src/types/api.ts`
   - TypeScript types for API
   - Request/response types

9. **airport.service.ts** - `/src/services/airport.service.ts`
   - Example service using API client
   - Type-safe API calls

10. **ExampleComponent.tsx** - `/src/components/ExampleComponent.tsx`
    - Example components showing integration
    - Best practices reference

### Documentation
11. **.env.example** - `/.env.example`
    - Environment variable template
    - Configuration reference

12. **PRODUCTION_FEATURES.md** - `/PRODUCTION_FEATURES.md`
    - Comprehensive feature documentation
    - Usage examples

13. **main.enhanced.tsx** - `/src/main.enhanced.tsx`
    - Enhanced entry point with all features

## Usage Examples

### Making API Calls

```tsx
import { apiClient } from '@/lib/api-client';

// GET request
const airports = await apiClient.get('/airports');

// POST request
const result = await apiClient.post('/predictions', {
  airport_id: 'SFO',
  departure_time: new Date().toISOString(),
});
```

### Handling Errors

```tsx
import { useErrorToast } from '@/hooks/useErrorToast';

function MyComponent() {
  const { showError } = useErrorToast();

  const handleAction = async () => {
    try {
      await apiClient.post('/data', formData);
    } catch (error) {
      showError(error, { title: 'Operation failed' });
    }
  };
}
```

### Loading States

```tsx
import { LoadingSpinner, CardSkeleton } from '@/components/LoadingState';

function MyComponent() {
  const [isLoading, setIsLoading] = useState(true);

  if (isLoading) {
    return <CardSkeleton count={3} />;
  }

  return <div>Your content</div>;
}
```

## File Structure

```
airport-waze-frontend/
├── .env.example                    # Environment variables template
├── PRODUCTION_FEATURES.md          # Full documentation
├── PRODUCTION_SETUP.md            # This file
├── src/
│   ├── components/
│   │   ├── ErrorBoundary.tsx      # Error boundary component
│   │   ├── LoadingState.tsx       # Loading components
│   │   └── ExampleComponent.tsx   # Usage examples
│   ├── config/
│   │   └── env.ts                 # Environment config
│   ├── hooks/
│   │   └── useErrorToast.ts       # Error toast hook
│   ├── lib/
│   │   ├── api-client.ts          # API client
│   │   ├── sentry.ts              # Sentry setup
│   │   └── setup.ts               # App initialization
│   ├── services/
│   │   └── airport.service.ts     # Example service
│   ├── types/
│   │   └── api.ts                 # TypeScript types
│   ├── main.tsx                   # Original entry point
│   └── main.enhanced.tsx          # Enhanced entry point
```

## Next Steps

1. **Configure Sentry** (optional but recommended)
   - Sign up at https://sentry.io
   - Create a new React project
   - Add DSN to `.env.local`

2. **Test Error Handling**
   - Visit the example component
   - Trigger intentional errors
   - Verify error boundary works
   - Check Sentry dashboard

3. **Integrate into Existing Components**
   - Replace fetch calls with API client
   - Add loading states
   - Implement error handling

4. **Build for Production**
   ```bash
   npm run build
   ```

5. **Deploy**
   - Set environment variables in hosting platform
   - Enable error tracking
   - Monitor errors in Sentry

## Troubleshooting

**"Module not found" errors**
```bash
npm install
```

**Environment validation errors**
- Check `.env.local` exists
- Verify `VITE_API_URL` is set
- Ensure all required variables are present

**API calls failing**
- Verify backend is running
- Check `VITE_API_URL` is correct
- Inspect network tab in DevTools

**TypeScript errors**
```bash
npm run build
```

## Support

For detailed documentation, see:
- **PRODUCTION_FEATURES.md** - Full feature documentation
- **ExampleComponent.tsx** - Code examples
- **api.ts** - Type definitions

## Checklist

- [ ] Dependencies installed
- [ ] `.env.local` configured
- [ ] `main.tsx` updated with ErrorBoundary
- [ ] Toaster added to app
- [ ] API client tested
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Sentry configured (optional)
- [ ] Production build tested
- [ ] Environment variables set in hosting platform

---

**You're all set!** Your AirportWaze frontend now has production-ready error handling, API client, and loading states.
