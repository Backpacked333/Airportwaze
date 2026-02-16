# Supabase Setup Guide for AirportWaze

This guide will help you deploy AirportWaze using Supabase as your backend database.

## Prerequisites

- A [Supabase](https://supabase.com) account (free tier works fine)
- Node.js 18+ and Python 3.12+

## Step 1: Create a Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Fill in the details:
   - **Name**: `airportwaze` (or your preferred name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest to your users
4. Click "Create new project"
5. Wait for the project to finish setting up (~2 minutes)

## Step 2: Get Your Database Connection String

1. In your Supabase dashboard, go to **Project Settings** (gear icon) → **Database**
2. Scroll down to **Connection String** section
3. Select **URI** tab
4. Copy the connection string - it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with the database password you set in Step 1

## Step 3: Convert Connection String for SQLAlchemy

The app uses SQLAlchemy with the `psycopg` driver (not the older `psycopg2`). Convert your connection string:

**Supabase gives you:**
```
postgresql://postgres:password@db.abc123xyz.supabase.co:5432/postgres
```

**Change to (for SQLAlchemy with psycopg):**
```
postgresql+psycopg://postgres:password@db.abc123xyz.supabase.co:5432/postgres
```

Just change `postgresql://` to `postgresql+psycopg://`

## Step 4: Configure Environment Variables

### Backend Configuration

Create or update `/airport-waze-backend/.env`:

```bash
# Database (Supabase)
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

# Redis (Optional - set to dummy value if not using)
REDIS_URL=redis://localhost:6379/0

# Security (Generate a secure key!)
SECRET_KEY=your-super-secret-key-change-this

# CORS (Add your frontend URL)
CORS_ORIGINS=["http://localhost:5173", "https://your-production-domain.com"]

# Application
DEBUG=true
ENV=development
LOG_LEVEL=INFO
```

**To generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Frontend Configuration

Create or update `/airport-waze-frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000
```

For production, use your deployed backend URL.

## Step 5: Initialize Database Tables

The app automatically creates tables on startup, but you can verify:

```bash
cd airport-waze-backend

# Install dependencies (if using Poetry)
poetry install

# Or with pip
pip install -r requirements.txt

# Run database migrations (optional, app creates tables on startup)
alembic upgrade head
```

## Step 6: Run the Application

### Option 1: Development (Local)

**Terminal 1 - Backend:**
```bash
cd airport-waze-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd airport-waze-frontend
npm install
npm run dev
```

Visit http://localhost:5173

### Option 2: Production with Docker

```bash
# Update docker-compose.yml to use Supabase
docker-compose up -d backend frontend
```

You'll need to update `docker-compose.yml` to remove the local postgres service and use Supabase instead.

## Step 7: Verify Database Connection

1. Backend should start successfully and log:
   ```
   INFO: Database initialized successfully
   ```

2. Check the health endpoint:
   ```bash
   curl http://localhost:8000/healthz
   ```
   Should return: `{"status":"healthy"}`

3. View API docs at: http://localhost:8000/docs

## Supabase-Specific Features You Can Use

### 1. **Database Management**
- Go to **Database** → **Tables** in Supabase dashboard to view your data
- Use the SQL Editor to run queries
- Set up Row Level Security (RLS) policies if needed

### 2. **Real-time Subscriptions** (Optional Enhancement)
Supabase supports real-time updates. You could add this for live wait time updates:

```typescript
// Frontend example
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Subscribe to wait time changes
supabase
  .channel('wait_times')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'wait_time_report' },
    (payload) => console.log('New wait time:', payload)
  )
  .subscribe()
```

### 3. **Supabase Auth** (Optional Enhancement)
Replace the custom JWT auth with Supabase Auth for better user management:

- Email/password authentication
- Social logins (Google, GitHub, etc.)
- Magic links
- Built-in user management UI

### 4. **Storage** (Future Feature)
Use Supabase Storage for user profile pictures or airport photos.

### 5. **Edge Functions** (Future Feature)
Deploy serverless functions for complex calculations or scheduled tasks.

## Database Tables Created

The app will automatically create these tables:

- `user` - User accounts with hashed passwords
- `wait_time_report` - Crowdsourced wait time reports
- `location_trace` - GPS breadcrumbs for checkpoint discovery
- `discovered_checkpoint` - ML-discovered checkpoint locations
- `airline_checkpoint_mapping` - Airline-specific checkpoint mappings

View them in Supabase: **Database** → **Tables**

## Troubleshooting

### Connection Refused
- Check your Supabase project is active
- Verify the connection string is correct
- Ensure you added `+psycopg` to the connection string

### SSL Certificate Errors
Add SSL mode to your connection string:
```
postgresql+psycopg://user:pass@host:5432/db?sslmode=require
```

### Rate Limiting
Supabase free tier has limits:
- 500MB database size
- 2GB bandwidth
- 50,000 monthly active users

For production, consider upgrading to Pro tier.

### Redis Warnings
If you see Redis connection warnings, that's normal without Redis. The app works fine without it (caching is disabled).

To use Redis, add [Upstash Redis](https://upstash.com) (free tier available):
```bash
REDIS_URL=rediss://default:password@redis-abc123.upstash.io:6379
```

## Production Deployment

### Deploy Backend to Fly.io

1. Install Fly CLI: https://fly.io/docs/hands-on/install-flyctl/
2. Login: `fly auth login`
3. Deploy:
```bash
cd airport-waze-backend
fly launch
# Set your Supabase DATABASE_URL as a secret
fly secrets set DATABASE_URL="postgresql+psycopg://..."
fly secrets set SECRET_KEY="your-secret-key"
fly deploy
```

### Deploy Frontend to Vercel

1. Push your code to GitHub
2. Import project in [Vercel](https://vercel.com)
3. Set environment variable:
   - `VITE_API_URL`: Your Fly.io backend URL
4. Deploy!

## Next Steps

- ✅ Set up Supabase project
- ✅ Configure environment variables
- ✅ Run the application
- 📊 View your data in Supabase dashboard
- 🚀 Deploy to production
- 🔐 (Optional) Replace JWT auth with Supabase Auth
- ⚡ (Optional) Add real-time subscriptions
- 📦 (Optional) Add Upstash Redis for caching

## Support

- Supabase Docs: https://supabase.com/docs
- Supabase Discord: https://discord.supabase.com
- Project Issues: Create an issue in your repository

---

**Ready to go?** Run the app and visit http://localhost:5173 to see AirportWaze in action! ✈️
