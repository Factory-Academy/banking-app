@echo off
REM Transaction Monitoring System - Setup Script (Windows)
REM This script automates the initial setup process

echo ==================================
echo Transaction Monitoring System
echo Setup Script for Windows
echo ==================================
echo.

REM Check prerequisites
echo Checking prerequisites...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo Python found
echo Node.js found
echo.

REM Backend setup
echo Setting up backend...
cd backend

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt -r requirements-dev.txt

echo Backend dependencies installed
echo.

REM Seed database
echo Seeding database with sample data...
python -m app.utils.seed_data
echo Database seeded successfully
echo.

cd ..

REM Frontend setup
echo Setting up frontend...
cd frontend

echo Installing Node.js dependencies...
call npm install --silent

echo Frontend dependencies installed
echo.

cd ..

REM Success message
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo To start the application:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   venv\Scripts\activate
echo   python -m uvicorn app.main:app --reload
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Then open http://localhost:5173 in your browser
echo.
echo For the full demo guide, see: docs\demo.md
echo ==================================
pause
