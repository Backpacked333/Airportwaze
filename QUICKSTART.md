# AirportWaze - Quick Start

Get AirportWaze running in 30 seconds!

## 🚀 One-Command Start

```bash
./start-app.sh
```

That's it! The script will:
- ✅ Check all dependencies
- ✅ Install packages if needed
- ✅ Initialize database
- ✅ Start backend (port 8000)
- ✅ Start frontend (port 5173)
- ✅ Show you the URLs to access

## 📱 Access the App

### On Your Computer
Open: **http://localhost:5173**

### On Your Phone (Same WiFi)
1. The script will show you the URL (e.g., `http://192.168.1.100:5173`)
2. Open that URL in your phone's browser
3. **Install as PWA**:
   - **iOS**: Safari → Share → Add to Home Screen
   - **Android**: Chrome → Menu → Install App

## 🛑 Stop the App

```bash
./stop-app.sh
```

## 📋 Prerequisites

- **Python 3.9+**: [Download](https://www.python.org/downloads/)
- **Node.js 18+**: [Download](https://nodejs.org/)
- **Poetry**: Will auto-install if missing

## 🎯 First Time Setup

```bash
# Clone repository (if you haven't)
git clone https://github.com/Backpacked333/Airportwaze.git
cd Airportwaze

# Checkout the feature branch
git checkout claude/airport-wait-times-E0lz8

# Run the app
./start-app.sh
```

## ✨ What You Get

- 🧠 **AI-Powered Predictions**: Personal speed profiling and smart predictions
- 📱 **iOS Design**: Beautiful, native-feeling interface
- 📸 **Boarding Pass Scanner**: Scan QR codes in 2 seconds
- 🗺️ **Route Optimization**: Find fastest path through airport
- 📍 **Location Tracking**: Background tracking with battery optimization
- 🔒 **Privacy First**: K-anonymity protection, data stays anonymous
- ✈️ **500+ Airports**: Worldwide coverage

## 📖 Need More Help?

- **Full Deployment Guide**: See `DEPLOYMENT_GUIDE.md`
- **Setup Instructions**: See `SETUP_GUIDE.md`
- **Phase Documentation**: See `PHASE*_COMPLETE.md` files

## 🐛 Troubleshooting

### Backend won't start?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i :8000)

# Try again
./start-app.sh
```

### Frontend won't start?
```bash
# Clear and reinstall
cd airport-waze-frontend
rm -rf node_modules
npm install
cd ..
./start-app.sh
```

### Database issues?
```bash
# Reinitialize database
cd airport-waze-backend
python scripts/init_database.py
cd ..
./start-app.sh
```

## 🎉 Enjoy!

You're now running a production-ready airport intelligence system!

Visit **http://localhost:5173** and start exploring.
