#!/bin/bash

echo "Setting up RCA Analysis Chatbot (Alternative setup with flexible dependencies)..."

# Check Python version
python3 --version

# Backend setup
echo "Setting up Flask backend..."
cd backend

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and essential tools
echo "Upgrading pip and build tools..."
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

# Try installing with flexible requirements
echo "Installing dependencies with flexible version constraints..."
if pip install -r requirements-flexible.txt; then
    echo "Successfully installed with flexible requirements"
else
    echo "Failed with flexible requirements, trying minimal install..."
    # Minimal install
    pip install flask flask-cors python-dotenv
    pip install openai
    pip install azure-identity
    pip install --no-deps pandas numpy
    pip install python-dateutil pydantic
fi

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file in backend/ - Please update with your Azure OpenAI credentials"
fi

cd ..

# Frontend setup
echo "Setting up React frontend..."
cd frontend

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install Node.js and npm first."
    exit 1
fi

npm install

cd ..

echo "Setup complete!"
echo ""
echo "IMPORTANT: Before running the application:"
echo "1. Update backend/.env with your Azure OpenAI credentials"
echo "2. Place certificate in backend/cert/ if using certificate auth"
echo ""
echo "To run the application:"
echo "1. Start backend: cd backend && source venv/bin/activate && python app.py"
echo "2. Start frontend: cd frontend && npm start"