# Voxa CLI - Development Setup Script

#!/bin/bash

echo "🚀 Setting up Voxa CLI Development Environment"
echo "=============================================="

# Check if required tools are installed
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    else
        echo "✅ $1 is installed"
    fi
}

echo "Checking prerequisites..."
check_command "python3"
check_command "node"
check_command "npm"
check_command "psql"

# Create virtual environment for backend
echo "Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Install frontend dependencies
echo "Setting up frontend dependencies..."
cd ../frontend
npm install
echo "✅ Frontend dependencies installed"

# Create environment files
echo "Creating environment files..."
cd ../backend
if [ ! -f .env ]; then
    cp env.example .env
    echo "📝 Created backend/.env file - please configure your API keys"
else
    echo "✅ Backend .env file already exists"
fi

cd ../frontend
if [ ! -f .env ]; then
    echo "REACT_APP_API_URL=http://localhost:5000" > .env
    echo "📝 Created frontend/.env file"
else
    echo "✅ Frontend .env file already exists"
fi

# Database setup
echo "Setting up database..."
cd ../backend
echo "Please ensure PostgreSQL is running and create a database named 'voxa_cli'"
echo "You can run: createdb voxa_cli"
echo "Then run: python setup_database.py"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your API keys in backend/.env"
echo "2. Set up PostgreSQL database"
echo "3. Run: python backend/setup_database.py"
echo "4. Start backend: cd backend && python app.py"
echo "5. Start frontend: cd frontend && npm start"
echo ""
echo "Access the application at: http://localhost:3000"






