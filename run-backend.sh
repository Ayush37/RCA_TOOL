#!/bin/bash

cd backend

# Activate virtual environment
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example"
    cp .env.example .env
    echo "Please update .env with your Azure OpenAI credentials"
fi

# Run Flask app
echo "Starting Flask backend on http://localhost:5000"
python app.py