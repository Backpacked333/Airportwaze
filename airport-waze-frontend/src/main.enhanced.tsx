/**
 * Enhanced Main Entry Point with Production-Ready Features
 *
 * This file demonstrates how to integrate all the production-ready components:
 * - Error Boundary
 * - Sentry Error Tracking
 * - Environment Configuration
 * - Application Setup
 *
 * To use this enhanced version:
 * 1. Rename this file to main.tsx (backup the original first)
 * 2. Install dependencies: npm install
 * 3. Configure .env file (copy from .env.example)
 * 4. Run the app: npm run dev
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

// Import production-ready features
import ErrorBoundary from './components/ErrorBoundary';
import { Toaster } from './components/ui/sonner';
import { initializeApp } from './lib/setup';

// Initialize application services (Sentry, Analytics, etc.)
initializeApp();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/*
      Error Boundary catches all unhandled errors in the React tree
      and displays a user-friendly fallback UI
    */}
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Custom error handler (optional)
        console.error('App Error:', error, errorInfo);
      }}
    >
      <App />

      {/* Toaster for displaying toast notifications (errors, success, info) */}
      <Toaster richColors position="top-right" />
    </ErrorBoundary>
  </StrictMode>
);
