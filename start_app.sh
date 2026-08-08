#!/bin/bash

echo "🚀 Starting Voxa CLI Application"
echo "==============================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check if ports are available
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use (Frontend)${NC}"
fi

if check_port 5000; then
    echo -e "${YELLOW}⚠️  Port 5000 is already in use (Backend)${NC}"
fi

echo ""
echo -e "${BLUE}Starting Backend Server...${NC}"
echo "Backend will run on: http://localhost:5000"
echo ""

# Start backend in background
cd backend
source ../venv/bin/activate
python app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo ""
echo -e "${BLUE}Starting Frontend Server...${NC}"
echo "Frontend will run on: http://localhost:3000"
echo ""

# Start frontend in background
cd ../frontend
npm start &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✅ Both servers are starting!${NC}"
echo ""
echo -e "${YELLOW}Access the application at: http://localhost:3000${NC}"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servers stopped.${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
