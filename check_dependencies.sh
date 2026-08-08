#!/bin/bash

echo "🔍 Voxa CLI - Dependency Verification Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python package
check_python_package() {
    if source venv/bin/activate 2>/dev/null && python -c "import $1" 2>/dev/null; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# Function to check Node.js package
check_node_package() {
    if cd frontend && npm list "$1" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $1${NC}"
        cd ..
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        cd ..
        return 1
    fi
}

echo -e "\n${BLUE}📋 System Requirements Check${NC}"
echo "================================"

# Check Python
if command_exists python3; then
    echo -e "${GREEN}✅ Python 3${NC} ($(python3 --version))"
else
    echo -e "${RED}❌ Python 3${NC}"
fi

# Check Node.js
if command_exists node; then
    echo -e "${GREEN}✅ Node.js${NC} ($(node --version))"
else
    echo -e "${RED}❌ Node.js${NC}"
fi

# Check npm
if command_exists npm; then
    echo -e "${GREEN}✅ npm${NC} ($(npm --version))"
else
    echo -e "${RED}❌ npm${NC}"
fi

# Check PostgreSQL
if command_exists psql; then
    echo -e "${GREEN}✅ PostgreSQL${NC} ($(psql --version))"
else
    echo -e "${YELLOW}⚠️  PostgreSQL${NC} (Required for database)"
fi

echo -e "\n${BLUE}🐍 Python Dependencies (Voxa.py)${NC}"
echo "=================================="

# Core Voxa.py dependencies
check_python_package "nltk"
check_python_package "speech_recognition"
check_python_package "pyttsx3"
check_python_package "sklearn"
check_python_package "requests"
check_python_package "bs4"
check_python_package "googleapiclient"
check_python_package "textblob"
check_python_package "dotenv"

# Optional PyAudio (may fail on some systems)
echo -e "\n${YELLOW}🎤 Audio Dependencies${NC}"
echo "====================="
if source venv/bin/activate 2>/dev/null && python -c "import pyaudio" 2>/dev/null; then
    echo -e "${GREEN}✅ PyAudio${NC}"
else
    echo -e "${YELLOW}⚠️  PyAudio${NC} (Optional - install with: sudo apt install python3-pyaudio)"
fi

echo -e "\n${BLUE}🌐 Backend Dependencies (Flask)${NC}"
echo "================================="

# Flask backend dependencies
check_python_package "flask"
check_python_package "flask_socketio"
check_python_package "flask_sqlalchemy"
check_python_package "flask_bcrypt"
check_python_package "flask_jwt_extended"
check_python_package "flask_cors"
check_python_package "socketio"
check_python_package "eventlet"

# Optional PostgreSQL driver
echo -e "\n${YELLOW}🗄️  Database Dependencies${NC}"
echo "=========================="
if source venv/bin/activate 2>/dev/null && python -c "import psycopg2" 2>/dev/null; then
    echo -e "${GREEN}✅ psycopg2${NC}"
else
    echo -e "${YELLOW}⚠️  psycopg2${NC} (Required for PostgreSQL - install with: sudo apt install libpq-dev)"
fi

echo -e "\n${BLUE}⚛️  Frontend Dependencies (React)${NC}"
echo "=================================="

# React frontend dependencies
check_node_package "react"
check_node_package "react-dom"
check_node_package "react-scripts"
check_node_package "socket.io-client"

echo -e "\n${BLUE}📁 Project Structure Check${NC}"
echo "============================"

# Check if all required files exist
required_files=(
    "Voxa.py"
    "knowledge_base.json"
    "requirements.txt"
    "backend/app.py"
    "backend/requirements.txt"
    "frontend/package.json"
    "frontend/src/App.js"
    "README.md"
    "docker-compose.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file${NC}"
    fi
done

echo -e "\n${BLUE}🔧 Environment Setup${NC}"
echo "====================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Python Virtual Environment${NC}"
else
    echo -e "${RED}❌ Python Virtual Environment${NC}"
fi

# Check if frontend node_modules exists
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✅ Frontend node_modules${NC}"
else
    echo -e "${RED}❌ Frontend node_modules${NC}"
fi

# Check if .env files exist
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✅ Backend .env file${NC}"
else
    echo -e "${YELLOW}⚠️  Backend .env file${NC} (Copy from env.example)"
fi

if [ -f "frontend/.env" ]; then
    echo -e "${GREEN}✅ Frontend .env file${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend .env file${NC} (Create with REACT_APP_API_URL)"
fi

echo -e "\n${BLUE}🚀 Quick Start Commands${NC}"
echo "========================"
echo -e "${YELLOW}Backend:${NC}"
echo "  source venv/bin/activate"
echo "  cd backend && python app.py"
echo ""
echo -e "${YELLOW}Frontend:${NC}"
echo "  cd frontend && npm start"
echo ""
echo -e "${YELLOW}Docker:${NC}"
echo "  docker-compose up -d"
echo ""

echo -e "${GREEN}🎉 Dependency check complete!${NC}"
echo ""
echo -e "${BLUE}📖 For detailed setup instructions, see README.md${NC}"
