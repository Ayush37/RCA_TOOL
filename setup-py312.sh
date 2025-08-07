#!/bin/bash

echo "Setting up RCA Analysis Chatbot for Python 3.12+..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $python_version"

# Backend setup
echo "Setting up Flask backend..."
cd backend

# Clean existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create fresh virtual environment
echo "Creating virtual environment..."
python3 -m venv venv --upgrade-deps
source venv/bin/activate

# Ensure we have the latest pip and setuptools
echo "Upgrading pip and build tools..."
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

# Install requirements for Python 3.12+
echo "Installing dependencies for Python 3.12+..."
pip install -r requirements-py312.txt

# Verify installations
echo "Verifying installations..."
python -c "import flask; print(f'Flask version: {flask.__version__}')"
python -c "import openai; print(f'OpenAI version: {openai.__version__}')"
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"
python -c "import numpy; print(f'Numpy version: {numpy.__version__}')"

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

# Clean install
echo "Installing frontend dependencies..."
rm -rf node_modules package-lock.json
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