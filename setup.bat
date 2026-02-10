@echo off
echo ========================================
echo AI Question Testing System - Setup
echo ========================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Step 3: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo Step 4: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created. Please edit it with your Hunyuan API key.
) else (
    echo .env file already exists.
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your HUNYUAN_API_KEY
echo 2. Run: python run.py
echo 3. Open browser: http://localhost:5000
echo.
pause
