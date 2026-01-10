#!/bin/bash

# AirportWaze Quick Start Script
# This script starts both backend and frontend servers

echo "🚀 Starting AirportWaze..."
echo ""

# Check if running from correct directory
if [ ! -d "airport-waze-backend" ] || [ ! -d "airport-waze-frontend" ]; then
    echo "❌ Error: Please run this script from the Airportwaze root directory"
    exit 1
fi

# Function to get local IP
get_local_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null
    else
        # Linux
        hostname -I | awk '{print $1}'
    fi
}

LOCAL_IP=$(get_local_ip)

# Check dependencies
echo "📦 Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

# Check Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Installing..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm"
    exit 1
fi

echo "✅ All dependencies found"
echo ""

# Initialize database if not exists
if [ ! -f "airport-waze-backend/airportwaze.db" ]; then
    echo "🗄️  Initializing database..."
    cd airport-waze-backend
    python3 scripts/init_database.py
    cd ..
    echo "✅ Database initialized"
    echo ""
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd airport-waze-backend
poetry install --no-interaction --quiet
cd ..
echo "✅ Backend dependencies installed"
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd airport-waze-frontend
npm install --silent
cd ..
echo "✅ Frontend dependencies installed"
echo ""

# Kill any existing processes on ports 8000 and 5173
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
sleep 1

# Start backend in background
echo "🚀 Starting backend server..."
cd airport-waze-backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 3

# Check if backend started successfully
if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Backend failed to start. Check backend.log for errors"
    cat backend.log
    exit 1
fi
echo "✅ Backend started (PID: $BACKEND_PID)"
echo ""

# Start frontend in background
echo "🚀 Starting frontend server..."
cd airport-waze-frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3

# Check if frontend started successfully
if ! lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Frontend failed to start. Check frontend.log for errors"
    cat frontend.log
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""

# Success message
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ AirportWaze is now running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Access on this computer:"
echo "   → http://localhost:5173"
echo ""
if [ ! -z "$LOCAL_IP" ]; then
    echo "📱 Access on mobile (same WiFi):"
    echo "   → http://$LOCAL_IP:5173"
    echo ""
fi
echo "🔧 Backend API:"
echo "   → http://localhost:8000"
echo "   → API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Process IDs:"
echo "   → Backend: $BACKEND_PID"
echo "   → Frontend: $FRONTEND_PID"
echo ""
echo "📝 Logs:"
echo "   → Backend: tail -f backend.log"
echo "   → Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop servers:"
echo "   → kill $BACKEND_PID $FRONTEND_PID"
echo "   → Or run: ./stop-app.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 To install as PWA on mobile:"
echo "   1. Open the URL above on your phone"
echo "   2. iOS: Share → Add to Home Screen"
echo "   3. Android: Menu → Install App"
echo ""
echo "Press Ctrl+C to stop monitoring, servers will continue running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save PIDs to file for stop script
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Monitor logs
tail -f backend.log frontend.log
