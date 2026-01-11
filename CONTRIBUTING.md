# Contributing to AirportWaze

Thank you for your interest in contributing to AirportWaze! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Examples of behavior that contributes to a positive environment:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**

- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at conduct@airportwaze.com. All complaints will be reviewed and investigated promptly and fairly.

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Git** installed and configured
- **Python 3.12+** for backend development
- **Node.js 20+** for frontend development
- **Docker & Docker Compose** for full-stack development
- **PostgreSQL 16+** and **Redis 7+** (or use Docker)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/airportwaze.git
cd airportwaze

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/airportwaze.git
```

### Set Up Development Environment

#### Backend Setup

```bash
cd airport-waze-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Poetry
pip install poetry

# Install dependencies (including dev dependencies)
poetry install

# Copy environment template
cp .env.example .env
# Edit .env with your local configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd airport-waze-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Full Stack with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec backend alembic upgrade head
```

## Development Workflow

### Branch Naming Convention

Use descriptive branch names with prefixes:

```bash
# Feature branches
feature/add-flight-tracking
feature/improve-prediction-accuracy

# Bug fix branches
fix/checkpoint-calculation-error
fix/map-rendering-issue

# Documentation branches
docs/update-api-documentation
docs/add-deployment-guide

# Refactoring branches
refactor/simplify-auth-logic
refactor/optimize-database-queries
```

### Workflow Steps

1. **Create a branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

```bash
# Edit files
# Add tests
# Update documentation
```

3. **Commit your changes**

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add flight tracking feature

- Implement flight API integration
- Add flight search endpoint
- Update frontend with flight selection
- Add tests for flight service"
```

4. **Keep your branch updated**

```bash
# Fetch latest from upstream
git fetch upstream

# Rebase on main
git rebase upstream/main

# Resolve any conflicts
# Continue rebase
git rebase --continue
```

5. **Push to your fork**

```bash
git push origin feature/your-feature-name
```

6. **Create Pull Request**
   - Go to GitHub and create a PR from your branch
   - Fill out the PR template
   - Link related issues

## Coding Standards

### Python (Backend)

#### Style Guide

Follow **PEP 8** with these tools:

```bash
# Format code with black
black .

# Lint with ruff
ruff check .

# Type checking with mypy
mypy app/
```

#### Code Style

```python
# Good: Clear, typed, documented
from typing import Optional

async def get_airport(
    airport_code: str,
    include_checkpoints: bool = True
) -> Optional[Airport]:
    """
    Retrieve airport information by code.

    Args:
        airport_code: Three-letter IATA airport code
        include_checkpoints: Whether to include checkpoint data

    Returns:
        Airport object if found, None otherwise

    Raises:
        ValueError: If airport_code is invalid
    """
    if not airport_code or len(airport_code) != 3:
        raise ValueError("Airport code must be 3 characters")

    airport = await airport_service.get_by_code(airport_code.upper())
    if airport and include_checkpoints:
        airport.checkpoints = await checkpoint_service.get_by_airport(airport.id)

    return airport


# Bad: No types, unclear, undocumented
def get_airport(code, inc=True):
    if not code:
        return None
    a = service.get(code)
    if a and inc:
        a.c = service2.get(a.id)
    return a
```

#### Documentation

- Use docstrings for all public functions and classes
- Include type hints for all function arguments and returns
- Add inline comments for complex logic
- Update API documentation when adding endpoints

#### Testing

- Write tests for all new features
- Aim for >85% code coverage
- Use pytest fixtures for common setups
- Mock external dependencies

```python
# Good test example
import pytest
from app.services.prediction_service import calculate_probability

@pytest.fixture
def sample_journey():
    """Create sample journey data for testing."""
    return {
        "segments": [
            {"wait_distribution": {"mu": 3.0, "sigma": 0.4}, "walk_minutes": 5},
            {"wait_distribution": {"mu": 2.5, "sigma": 0.3}, "walk_minutes": 10}
        ],
        "time_available": 30
    }

def test_probability_calculation(sample_journey):
    """Test that probability calculation returns valid result."""
    probability = calculate_probability(
        sample_journey["segments"],
        sample_journey["time_available"]
    )

    assert 0.0 <= probability <= 1.0
    assert isinstance(probability, float)

def test_probability_with_insufficient_time(sample_journey):
    """Test probability when time is insufficient."""
    sample_journey["time_available"] = 1  # Not enough time

    probability = calculate_probability(
        sample_journey["segments"],
        sample_journey["time_available"]
    )

    assert probability < 0.1  # Should be very low
```

### TypeScript/React (Frontend)

#### Style Guide

Follow **Airbnb React/JSX Style Guide** with TypeScript:

```bash
# Lint code
npm run lint

# Auto-fix issues
npm run lint:fix

# Type checking
npm run type-check
```

#### Component Style

```tsx
// Good: Typed, documented, accessible
import { FC, useState } from 'react';

interface AirportSelectorProps {
  /** List of available airports */
  airports: Airport[];
  /** Currently selected airport code */
  selectedCode?: string;
  /** Callback when airport is selected */
  onSelect: (code: string) => void;
  /** Optional CSS class name */
  className?: string;
}

/**
 * Airport selection dropdown component
 *
 * Allows users to select an airport from a list of available options.
 * Includes search functionality and keyboard navigation.
 */
export const AirportSelector: FC<AirportSelectorProps> = ({
  airports,
  selectedCode,
  onSelect,
  className
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredAirports = airports.filter(airport =>
    airport.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    airport.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className={className} role="combobox" aria-expanded="true">
      <input
        type="text"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="Search airports..."
        aria-label="Search airports"
      />
      <ul role="listbox">
        {filteredAirports.map(airport => (
          <li
            key={airport.code}
            role="option"
            aria-selected={airport.code === selectedCode}
            onClick={() => onSelect(airport.code)}
          >
            {airport.name} ({airport.code})
          </li>
        ))}
      </ul>
    </div>
  );
};


// Bad: No types, unclear, inaccessible
export const AirportSelector = ({ airports, selected, onSelect }) => {
  const [term, setTerm] = useState('');

  const filtered = airports.filter(a =>
    a.name.includes(term) || a.code.includes(term)
  );

  return (
    <div>
      <input value={term} onChange={(e) => setTerm(e.target.value)} />
      <ul>
        {filtered.map(a => (
          <li onClick={() => onSelect(a.code)}>{a.name}</li>
        ))}
      </ul>
    </div>
  );
};
```

#### Hooks

```typescript
// Good: Custom hook with proper typing
import { useState, useEffect } from 'react';

interface UseAirportResult {
  airport: Airport | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useAirport(code: string): UseAirportResult {
  const [airport, setAirport] = useState<Airport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [refetchTrigger, setRefetchTrigger] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function fetchAirport() {
      try {
        setLoading(true);
        setError(null);

        const data = await api.getAirport(code);

        if (!cancelled) {
          setAirport(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    if (code) {
      fetchAirport();
    }

    return () => {
      cancelled = true;
    };
  }, [code, refetchTrigger]);

  const refetch = () => setRefetchTrigger(prev => prev + 1);

  return { airport, loading, error, refetch };
}
```

### Commit Messages

Follow the **Conventional Commits** specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

**Examples:**

```bash
# Feature
feat(backend): add flight tracking API endpoint

# Bug fix
fix(frontend): resolve map rendering on mobile devices

# Documentation
docs: update deployment guide with Kubernetes instructions

# Refactoring
refactor(backend): simplify authentication middleware

# Multiple paragraphs
feat(backend): implement Monte Carlo simulation

Add probabilistic prediction using log-normal distributions
and Monte Carlo simulation with 10,000 iterations.

This replaces the simple average calculation and provides
confidence intervals (P50, P80, P90, P95).

Closes #123
```

## Testing Requirements

### Backend Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_predictions.py

# Run specific test function
pytest tests/test_predictions.py::test_monte_carlo_simulation
```

**Coverage Requirements:**
- Overall: >85%
- New features: >90%
- Critical paths: 100%

### Frontend Testing (Future)

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Writing Tests

**Backend Test Example:**

```python
# tests/test_journey_service.py
import pytest
from app.services.journey_service import plan_journey

@pytest.mark.asyncio
async def test_plan_journey_with_tsa_precheck(test_db, sample_airport):
    """Test journey planning with TSA PreCheck."""
    request = JourneyRequest(
        airport_code="JFK",
        terminal="Terminal 4",
        gate="A1",
        has_tsa_precheck=True,
        has_checked_bags=False
    )

    result = await plan_journey(request)

    assert result.total_time_minutes > 0
    assert len(result.steps) >= 2  # Security + walk to gate
    assert any("PreCheck" in step.step_name for step in result.steps)
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code is formatted and linted
3. ✅ Documentation is updated
4. ✅ Commit messages follow conventions
5. ✅ Branch is up to date with main

### PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Related Issues

Closes #123

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
- [ ] Dependent changes merged

## Screenshots (if applicable)

Add screenshots for UI changes
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: Maintainers review your code
3. **Feedback**: Address review comments
4. **Approval**: At least one maintainer approves
5. **Merge**: Maintainer merges your PR

### After Merge

- Delete your branch
- Update your local repository
- Celebrate your contribution!

## Issue Guidelines

### Creating Issues

Use issue templates for:

- **Bug Reports**: Describe the bug with reproduction steps
- **Feature Requests**: Propose new features with use cases
- **Questions**: Ask for help or clarification
- **Documentation**: Report documentation issues

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable, add screenshots

**Environment:**
- OS: [e.g. Ubuntu 22.04]
- Browser: [e.g. Chrome 120]
- Version: [e.g. 2.0.0]

**Additional context**
Any other information
```

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem

**Describe the solution you'd like**
A clear description of what you want to happen

**Describe alternatives you've considered**
Alternative solutions you've thought about

**Additional context**
Any other context or screenshots
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord** (planned): Real-time chat
- **Email**: contribute@airportwaze.com

### Getting Help

If you're stuck:

1. Check existing documentation
2. Search closed issues/PRs
3. Ask in GitHub Discussions
4. Contact maintainers

### Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AirportWaze! Your efforts help make air travel easier for everyone.
