#!/bin/bash

echo "Setting up RCA Analysis Chatbot..."

# Backend setup
echo "Setting up Flask backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file in backend/ - Please update with your Azure OpenAI credentials"
fi

cd ..

# Frontend setup
echo "Setting up React frontend..."
cd frontend
npm install

cd ..

echo "Setup complete!"
echo ""
echo "IMPORTANT: Before running the application:"
echo "1. Update backend/.env with your Azure OpenAI credentials"
echo "2. Ensure the metric files are in place (markerEvent/, dagDetails/, etc.)"
echo ""
echo "To run the application:"
echo "1. Start backend: cd backend && source venv/bin/activate && python app.py"
echo "2. Start frontend: cd frontend && npm start"