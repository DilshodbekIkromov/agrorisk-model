#!/bin/bash
# Startup script for AgroRisk Flask Backend

echo "🌾 Starting AgroRisk Copilot Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Start Flask server
echo "Starting Flask server on port 5000..."
echo "Press Ctrl+C to stop"
echo ""
python app.py
