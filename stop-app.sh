#!/bin/bash

# AirportWaze Stop Script
# This script stops both backend and frontend servers

echo "🛑 Stopping AirportWaze..."
echo ""

# Read PIDs from files
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✅ Backend stopped (PID: $BACKEND_PID)"
    else
        echo "ℹ️  Backend not running"
    fi
    rm .backend.pid
else
    echo "ℹ️  No backend PID file found"
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "✅ Frontend stopped (PID: $FRONTEND_PID)"
    else
        echo "ℹ️  Frontend not running"
    fi
    rm .frontend.pid
else
    echo "ℹ️  No frontend PID file found"
fi

# Force kill any remaining processes on ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo ""
echo "✨ AirportWaze stopped successfully"
