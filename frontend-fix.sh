#!/bin/bash

echo "Fixing Frontend TypeScript and dependency issues..."

cd frontend

# Clean previous installations
echo "Cleaning previous installations..."
rm -rf node_modules package-lock.json

# Install dependencies
echo "Installing dependencies..."
npm install

# Install any missing type definitions
echo "Installing missing type definitions..."
npm install --save-dev @types/uuid

# Try to build to check for errors
echo "Testing build..."
npm run build

echo "Frontend fix complete!"
echo ""
echo "To start the frontend:"
echo "cd frontend && npm start"