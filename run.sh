#!/bin/bash
# Quick start script for FastAPI Webstore

echo "Starting FastAPI Webstore..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Run the application
echo "Starting server..."
echo "API Documentation: http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

