# AirportWaze Deployment Guide

Complete guide to deploy and run AirportWaze on your device.

---

## 🚀 Quick Start (Run Locally)

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Poetry (Python package manager)

### Step 1: Start Backend Server

```bash
cd airport-waze-backend

# Install dependencies
poetry install

# Set up environment variables (optional - has defaults)
cp .env.example .env

# Initialize database (if not already done)
python scripts/init_database.py

# Start backend server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: `http://localhost:8000`

### Step 2: Start Frontend Dev Server

```bash
cd airport-waze-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Step 3: Access on Mobile

#### Option A: Same WiFi Network
1. Find your computer's local IP address:
   - **Mac/Linux**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - **Windows**: `ipconfig` (look for IPv4 Address)
2. On your phone, open: `http://YOUR_IP:5173`
3. Allow location permissions when prompted

#### Option B: Use Ngrok (Public URL)
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5173
```
Use the provided https URL on any device.

---

## 📱 Deploy as PWA (Progressive Web App)

### For Development/Testing

1. **Start servers** (as above)
2. **Open in mobile browser**: `http://YOUR_IP:5173`
3. **Install PWA**:
   - **iPhone/iPad**: Tap Share → Add to Home Screen
   - **Android**: Tap menu → Install App / Add to Home Screen
4. **Launch from home screen** - works like a native app!

### For Production Deployment

#### Option 1: Deploy to Vercel (Frontend) + Render (Backend)

##### Backend on Render:
1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Create new Web Service
4. Connect GitHub repo → `airport-waze-backend`
5. Settings:
   - **Build Command**: `pip install poetry && poetry install`
   - **Start Command**: `poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.9+
6. Add environment variables (if needed)
7. Deploy!

Backend URL: `https://your-app.onrender.com`

##### Frontend on Vercel:
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repo → `airport-waze-frontend`
3. Settings:
   - **Framework**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. **Environment Variables**:
   ```
   VITE_API_URL=https://your-app.onrender.com
   ```
5. Deploy!

Frontend URL: `https://your-app.vercel.app`

#### Option 2: Deploy to Fly.io (Full Stack)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy backend
cd airport-waze-backend
fly launch --name airportwaze-api
fly deploy

# Deploy frontend (after updating API URL)
cd ../airport-waze-frontend
fly launch --name airportwaze-app
fly deploy
```

#### Option 3: Deploy to Your Own Server (VPS)

```bash
# SSH into your server
ssh user@your-server.com

# Clone repository
git clone https://github.com/Backpacked333/Airportwaze.git
cd Airportwaze

# Set up backend with systemd service
sudo nano /etc/systemd/system/airportwaze-backend.service
```

```ini
[Unit]
Description=AirportWaze Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/Airportwaze/airport-waze-backend
ExecStart=/usr/local/bin/poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start backend service
sudo systemctl enable airportwaze-backend
sudo systemctl start airportwaze-backend

# Build frontend
cd airport-waze-frontend
npm install
npm run build

# Serve with nginx
sudo nano /etc/nginx/sites-available/airportwaze
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/Airportwaze/airport-waze-frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/airportwaze /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## 🔧 Configuration

### Backend Environment Variables

Create `.env` in `airport-waze-backend/`:

```bash
# API Keys (optional - has mock fallbacks)
AVIATIONSTACK_API_KEY=your_key_here
AERODATABOX_API_KEY=your_key_here
FLIGHTAWARE_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./airportwaze.db

# CORS (add your frontend URL)
ALLOWED_ORIGINS=http://localhost:5173,https://your-app.vercel.app
```

### Frontend Environment Variables

Create `.env` in `airport-waze-frontend/`:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Or for production:
# VITE_API_URL=https://your-backend.onrender.com
```

---

## 📊 Production Checklist

Before deploying to production:

### Backend
- [ ] Set strong API keys in environment variables
- [ ] Configure CORS allowed origins for your domain
- [ ] Set up HTTPS (use Cloudflare, Let's Encrypt, or platform SSL)
- [ ] Configure database backups
- [ ] Set up error monitoring (Sentry, Rollbar)
- [ ] Enable rate limiting on API endpoints
- [ ] Review and update k-anonymity threshold (currently 10 users)

### Frontend
- [ ] Update `VITE_API_URL` to production backend
- [ ] Update `manifest.json` with your app name and colors
- [ ] Generate proper app icons (use icon generator tool)
- [ ] Test PWA installation on iOS and Android
- [ ] Verify service worker caching works offline
- [ ] Test location tracking in background
- [ ] Test boarding pass scanner with real boarding passes
- [ ] Add analytics (Google Analytics, Plausible, etc.)
- [ ] Set up error tracking (Sentry)

### Security
- [ ] Enable HTTPS everywhere
- [ ] Set proper Content Security Policy headers
- [ ] Review and test privacy controls
- [ ] Ensure k-anonymity protection active
- [ ] Test with mock data before real users
- [ ] Review telemetry data collection and storage

### Performance
- [ ] Enable gzip compression
- [ ] Optimize images and assets
- [ ] Test on slow 3G connection
- [ ] Verify lazy loading works
- [ ] Check bundle size (should be < 500KB)
- [ ] Test battery usage on mobile
- [ ] Verify location sampling rate adapts to battery

---

## 🧪 Testing on Mobile

### iOS Testing
1. **Safari Required**: iOS only allows PWA installation from Safari
2. **Location Permissions**: Settings → Safari → Location → "While Using App"
3. **Camera Permissions**: Allow camera access for boarding pass scanner
4. **Install**: Share button → Add to Home Screen
5. **Test Offline**: Enable Airplane Mode, app should still load

### Android Testing
1. **Chrome or Firefox**: Both support PWA installation
2. **Location**: Allow "Precise Location" in browser
3. **Camera**: Allow camera for QR code scanning
4. **Install**: Menu → "Install App" or "Add to Home Screen"
5. **Test Background**: App should track location when minimized

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i :8000)

# Check database exists
ls airport-waze-backend/airportwaze.db

# Reinitialize database if missing
python airport-waze-backend/scripts/init_database.py
```

### Frontend Won't Start
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version (need 18+)
node --version

# Try with legacy OpenSSL (if on Node 17+)
export NODE_OPTIONS=--openssl-legacy-provider
npm run dev
```

### PWA Won't Install
- **iOS**: Must use Safari browser
- **Android**: Ensure manifest.json is accessible
- **Both**: Must be served over HTTPS (or localhost for dev)
- Check browser console for manifest/service worker errors

### Location Tracking Not Working
- Check browser permissions (allow location access)
- Ensure HTTPS (location APIs require secure context)
- Check console for geolocation errors
- Verify backend telemetry endpoint responding

### Boarding Pass Scanner Not Working
- Camera permissions must be granted
- Check if BarcodeDetector API supported (Chrome/Edge only currently)
- Test with real boarding pass QR code
- Use manual entry as fallback

---

## 📱 Access the App

Once deployed, users can:

1. **Open in Browser**: Visit your deployed URL
2. **Install as App**:
   - iOS: Safari → Share → Add to Home Screen
   - Android: Chrome → Menu → Install App
3. **Use Offline**: Service worker caches everything
4. **Track Location**: Background tracking with battery optimization
5. **Scan Boarding Pass**: Camera-based QR code scanning
6. **Get Predictions**: AI-powered wait time predictions

---

## 🎉 You're Ready!

Your AirportWaze app is now live and ready to use. Share the URL with travelers and watch as the AI learns and improves predictions with each user!

### Share Your Deployment
- Frontend: `https://your-app-url.com`
- API Docs: `https://your-api-url.com/docs`
- GitHub: `https://github.com/Backpacked333/Airportwaze`

### Next Steps
1. Test with real airport visits
2. Gather feedback from users
3. Monitor telemetry data for accuracy
4. Add more airports as needed
5. Enhance ML models with collected data

---

## 📞 Support

Issues? Check:
- GitHub Issues: https://github.com/Backpacked333/Airportwaze/issues
- Documentation: All PHASE*_COMPLETE.md files
- Setup Guide: SETUP_GUIDE.md

Happy travels! ✈️
