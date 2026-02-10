#!/bin/bash

echo "========================================"
echo "AI Question Testing System - Setup"
echo "========================================"
echo ""

echo "Step 1: Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi
echo "Virtual environment created successfully!"
echo ""

echo "Step 2: Activating virtual environment..."
source venv/bin/activate
echo ""

echo "Step 3: Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully!"
echo ""

echo "Step 4: Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created. Please edit it with your Hunyuan API key."
else
    echo ".env file already exists."
fi
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your HUNYUAN_API_KEY"
echo "2. Run: python run.py"
echo "3. Open browser: http://localhost:5000"
echo ""
