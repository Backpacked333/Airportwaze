# AirportWaze Frontend

Modern, responsive React application for real-time airport navigation and wait time predictions. Built with React 18, TypeScript, and Tailwind CSS, featuring interactive maps and probabilistic predictions.

## Overview

The frontend is a single-page application (SPA) built with **React** and **TypeScript**, using **Vite** for blazing-fast development and optimized production builds. It features a clean, intuitive UI built with **shadcn/ui** components and **Tailwind CSS**, with interactive maps powered by **Leaflet**.

## Features

- **Interactive Airport Maps** with Leaflet/React-Leaflet
- **Real-time Wait Time Visualization** with charts and heatmaps
- **Probabilistic Flight Predictions** showing P50, P80, P90, P95
- **Journey Planning Interface** with step-by-step navigation
- **Multi-Airport Support** with search and autocomplete
- **Responsive Design** optimized for mobile and desktop
- **Dark Mode Support** (ready for implementation)
- **Accessibility** following WCAG 2.1 guidelines
- **Progressive Web App** capabilities (PWA-ready)

## Tech Stack

### Core
- **React**: 18.3+ with Hooks
- **TypeScript**: 5.6+ for type safety
- **Vite**: 6.0+ for development and building
- **React Router**: (planned for multi-page navigation)

### UI & Styling
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality React components built on Radix UI
- **Radix UI**: Accessible component primitives
- **Lucide React**: Beautiful, consistent icons
- **class-variance-authority**: Dynamic variant styling
- **tailwind-merge**: Intelligent Tailwind class merging

### Data Visualization
- **Recharts**: Composable charting library
- **Leaflet**: Interactive maps
- **React-Leaflet**: React components for Leaflet

### Forms & Validation
- **React Hook Form**: Performant form management
- **Zod**: TypeScript-first schema validation
- **@hookform/resolvers**: Validation resolver for React Hook Form

### UI Components (shadcn/ui)
- Accordion, Alert Dialog, Avatar, Button, Card
- Checkbox, Dialog, Dropdown Menu, Form, Input
- Label, Popover, Progress, Radio Group, ScrollArea
- Select, Separator, Slider, Switch, Tabs, Toast
- Tooltip, and more...

## Project Structure

```
airport-waze-frontend/
├── public/                        # Static assets
│   ├── favicon.ico
│   └── robots.txt
├── src/
│   ├── components/                # React components
│   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   ├── AirportMap.tsx         # Interactive map component
│   │   ├── CheckpointCard.tsx     # Checkpoint visualization
│   │   ├── FlightForm.tsx         # Flight input form
│   │   ├── JourneyPlanner.tsx     # Journey planning UI
│   │   ├── ProbabilityDisplay.tsx # Probability visualization
│   │   └── WaitTimeChart.tsx      # Wait time charts
│   ├── hooks/                     # Custom React hooks
│   │   ├── useAirports.ts         # Airport data fetching
│   │   ├── useJourney.ts          # Journey planning
│   │   ├── usePrediction.ts       # Probability predictions
│   │   └── useWaitTimes.ts        # Wait time data
│   ├── lib/                       # Utilities and helpers
│   │   ├── api.ts                 # API client
│   │   ├── utils.ts               # Helper functions
│   │   └── types.ts               # TypeScript types
│   ├── assets/                    # Images, fonts, etc.
│   ├── App.tsx                    # Main application component
│   ├── App.css                    # Global styles
│   ├── main.tsx                   # Application entry point
│   ├── index.css                  # Tailwind imports
│   └── vite-env.d.ts              # Vite type declarations
├── Dockerfile                     # Multi-stage production build
├── nginx.conf                     # Nginx configuration for production
├── package.json                   # Node dependencies
├── package-lock.json              # Locked dependencies
├── tsconfig.json                  # TypeScript configuration
├── tsconfig.app.json              # App-specific TypeScript config
├── tsconfig.node.json             # Node-specific TypeScript config
├── vite.config.ts                 # Vite configuration
├── tailwind.config.js             # Tailwind CSS configuration
├── postcss.config.js              # PostCSS configuration
├── components.json                # shadcn/ui configuration
├── eslint.config.js               # ESLint configuration
└── README.md                      # This file
```

## Development Setup

### Prerequisites

- Node.js 20+ (LTS recommended)
- npm 10+ or yarn 1.22+
- Modern browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
# Navigate to frontend directory
cd airport-waze-frontend

# Install dependencies
npm install

# Or using yarn
yarn install
```

### Environment Configuration

Create `.env.local` for development configuration:

```bash
# API Base URL
VITE_API_BASE_URL=http://localhost:8000

# Feature flags (optional)
VITE_ENABLE_DEBUG=true
VITE_ENABLE_ANALYTICS=false
```

### Running Development Server

```bash
# Start dev server with hot reload
npm run dev

# Server will start at http://localhost:5173
# - Fast refresh on file changes
# - TypeScript type checking
# - ESLint warnings in terminal
```

### Building for Production

```bash
# Build optimized production bundle
npm run build

# Output will be in dist/ directory
# - Minified JavaScript and CSS
# - Tree-shaken dependencies
# - Optimized assets
# - Source maps for debugging

# Preview production build locally
npm run preview
```

### Docker Development

```bash
# Build Docker image
docker build -t airportwaze-frontend .

# Run container
docker run -p 8080:8080 airportwaze-frontend

# Access at http://localhost:8080
```

## Available Scripts

```bash
# Development
npm run dev              # Start dev server with hot reload

# Build
npm run build            # Build for production
npm run preview          # Preview production build

# Code Quality
npm run lint             # Run ESLint
npm run lint:fix         # Auto-fix ESLint issues

# Type Checking
npm run type-check       # Run TypeScript compiler check
```

## Code Style & Quality

### ESLint Configuration

The project uses ESLint with TypeScript and React plugins:

```bash
# Run linter
npm run lint

# Auto-fix issues
npm run lint:fix
```

### TypeScript

Strict TypeScript configuration for type safety:

```typescript
// Example: Type-safe API call
import { Airport } from '@/lib/types';

async function getAirport(code: string): Promise<Airport> {
  const response = await fetch(`/api/airports/${code}`);
  return response.json();
}
```

### Formatting

```bash
# Format code with Prettier (if configured)
npm run format

# Check formatting
npm run format:check
```

## Component Development

### Using shadcn/ui Components

```bash
# Add new shadcn/ui component
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add dialog

# Components are copied to src/components/ui/
# Fully customizable and type-safe
```

### Creating Custom Components

```tsx
// src/components/WaitTimeCard.tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface WaitTimeCardProps {
  checkpoint: string;
  waitMinutes: number;
  status: 'low' | 'moderate' | 'high';
}

export function WaitTimeCard({ checkpoint, waitMinutes, status }: WaitTimeCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{checkpoint}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold">{waitMinutes} min</span>
          <Badge variant={status}>{status}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Custom Hooks

```typescript
// src/hooks/useAirport.ts
import { useState, useEffect } from 'react';
import { Airport } from '@/lib/types';

export function useAirport(code: string) {
  const [airport, setAirport] = useState<Airport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchAirport() {
      try {
        setLoading(true);
        const response = await fetch(`/api/airports/${code}`);
        const data = await response.json();
        setAirport(data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    if (code) {
      fetchAirport();
    }
  }, [code]);

  return { airport, loading, error };
}
```

## API Integration

### API Client

```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchAirports() {
  const response = await fetch(`${API_BASE_URL}/api/airports`);
  if (!response.ok) {
    throw new Error('Failed to fetch airports');
  }
  return response.json();
}

export async function planJourney(request: JourneyRequest) {
  const response = await fetch(`${API_BASE_URL}/api/journey/plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error('Failed to plan journey');
  }
  return response.json();
}

export async function checkFlightProbability(request: WillIMakeItRequest) {
  const response = await fetch(`${API_BASE_URL}/api/will-i-make-it`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error('Failed to calculate probability');
  }
  return response.json();
}
```

## Styling

### Tailwind CSS

Utility-first CSS with custom configuration:

```tsx
// Example component with Tailwind classes
export function ProbabilityCard({ probability }: { probability: number }) {
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <h3 className="text-lg font-semibold">Flight Probability</h3>
      <p className="text-4xl font-bold text-green-600">
        {(probability * 100).toFixed(0)}%
      </p>
      <p className="text-sm text-muted-foreground">
        Chance of making your flight
      </p>
    </div>
  );
}
```

### Custom Theme

```javascript
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6',
          foreground: '#ffffff',
        },
        // Add custom colors
      },
    },
  },
};
```

## State Management

### React Context (Current)

```tsx
// src/contexts/AppContext.tsx
import { createContext, useContext, useState } from 'react';

interface AppState {
  selectedAirport: string | null;
  setSelectedAirport: (code: string) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [selectedAirport, setSelectedAirport] = useState<string | null>(null);

  return (
    <AppContext.Provider value={{ selectedAirport, setSelectedAirport }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}
```

### Future: Redux/Zustand (Planned)

For more complex state management needs.

## Testing

### Unit Tests (Future)

```bash
# Install testing dependencies
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Run tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

### Example Test

```typescript
// src/components/Button.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
});
```

## Performance Optimization

### Bundle Size

- **Target**: < 500KB gzipped
- **Code Splitting**: Dynamic imports for routes
- **Tree Shaking**: Automatic with Vite
- **Asset Optimization**: Images compressed, fonts subset

### Lazy Loading

```tsx
import { lazy, Suspense } from 'react';

const JourneyPlanner = lazy(() => import('./components/JourneyPlanner'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <JourneyPlanner />
    </Suspense>
  );
}
```

### Image Optimization

```tsx
// Use responsive images
<img
  src="/images/airport-sm.jpg"
  srcSet="/images/airport-md.jpg 768w, /images/airport-lg.jpg 1280w"
  alt="Airport"
  loading="lazy"
/>
```

## Deployment

### Production Build

```bash
# Build for production
npm run build

# Output in dist/ directory
# - index.html
# - assets/
#   - *.js (JavaScript bundles)
#   - *.css (Stylesheets)
#   - Images and fonts
```

### Docker Deployment

```bash
# Build Docker image
docker build -t airportwaze-frontend .

# Run container
docker run -d -p 80:8080 airportwaze-frontend

# With environment variables
docker run -d \
  -p 80:8080 \
  -e VITE_API_BASE_URL=https://api.airportwaze.com \
  airportwaze-frontend
```

### Nginx Configuration

The included `nginx.conf` provides:
- Gzip compression
- Cache headers for static assets
- SPA routing support (fallback to index.html)
- Security headers

### Environment Variables

Build-time variables (must start with `VITE_`):

```bash
# .env.production
VITE_API_BASE_URL=https://api.airportwaze.com
VITE_ENABLE_ANALYTICS=true
```

## Accessibility

### Best Practices

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus management
- Color contrast compliance (WCAG AA)
- Screen reader testing

### Example

```tsx
<button
  aria-label="Plan your journey"
  onClick={handlePlan}
  className="btn-primary"
>
  <IconRoute aria-hidden="true" />
  <span>Plan Journey</span>
</button>
```

## Browser Support

- **Chrome/Edge**: Last 2 versions
- **Firefox**: Last 2 versions
- **Safari**: Last 2 versions
- **Mobile Safari**: iOS 14+
- **Chrome Android**: Last 2 versions

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

#### Module Not Found

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### TypeScript Errors

```bash
# Clear TypeScript cache
rm -rf node_modules/.vite

# Restart dev server
npm run dev
```

#### Build Fails

```bash
# Check for type errors
npm run type-check

# Check for linting errors
npm run lint

# Clean build directory
rm -rf dist
npm run build
```

## Contributing

1. Follow React best practices
2. Use TypeScript for all new code
3. Write accessible components
4. Test on multiple browsers
5. Optimize images and assets
6. Document complex logic

### Pre-commit Checklist

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build succeeds
npm run build
```

## License

MIT License - see [../LICENSE](../LICENSE)

## Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Radix UI](https://www.radix-ui.com/)
- [Leaflet Documentation](https://leafletjs.com/)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/airportwaze/issues)
- **Main README**: [../README.md](../README.md)
- **Architecture**: [../ARCHITECTURE.md](../ARCHITECTURE.md)
