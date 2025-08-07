#!/bin/bash

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Dependencies not installed. Running npm install..."
    npm install
fi

# Start React app
echo "Starting React frontend on http://localhost:3000"
npm start