#!/bin/bash

# Function to stop all background processes on exit
cleanup() {
    echo "Stopping all processes..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT

# Check if Python virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install backend dependencies
source venv/bin/activate
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

# Start backend server
echo "Starting backend server..."
cd backend && python run.py &

# Wait a bit for backend to start
sleep 2

# Start frontend server
echo "Starting frontend server..."
cd ../frontend && npm start &

# Wait for all background processes
wait
