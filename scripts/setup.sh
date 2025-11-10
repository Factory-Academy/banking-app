#!/bin/bash

# Transaction Monitoring System - Setup Script (macOS/Linux)
# This script automates the initial setup process

set -e  # Exit on error

echo "=================================="
echo "Transaction Monitoring System"
echo "Setup Script for macOS/Linux"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

echo "✅ Python $(python3 --version) found"
echo "✅ Node.js $(node --version) found"
echo ""

# Backend setup
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt -r requirements-dev.txt

echo "✅ Backend dependencies installed"
echo ""

# Seed database
echo "Seeding database with sample data..."
python -m app.utils.seed_data
echo "✅ Database seeded successfully"
echo ""

cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend

echo "Installing Node.js dependencies..."
npm install --silent

echo "✅ Frontend dependencies installed"
echo ""

cd ..

# Success message
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:5173 in your browser"
echo ""
echo "For the full demo guide, see: docs/demo.md"
echo "=================================="
