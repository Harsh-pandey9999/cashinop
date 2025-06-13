#!/bin/bash

# Casino Partners Setup Script
# This script helps set up the development environment for the Casino Partners application

echo "===== Casino Partners Setup Script ====="
echo "This script will help you set up the development environment."

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo "✅ Python is installed."
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    echo "✅ Python is installed."
    PYTHON_CMD="python"
else
    echo "❌ Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📊 Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists."
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "🔧 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file from example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists."
fi

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo "🔧 Creating logs directory..."
    mkdir -p logs
    echo "✅ Logs directory created."
else
    echo "✅ Logs directory already exists."
fi

# Apply migrations
echo "🔧 Applying database migrations..."
$PYTHON_CMD manage.py migrate

# Collect static files
echo "🔧 Collecting static files..."
$PYTHON_CMD manage.py collectstatic --noinput

# Create superuser if needed
echo "Do you want to create a superuser? (y/n)"
read -r CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ] || [ "$CREATE_SUPERUSER" = "Y" ]; then
    echo "🔧 Creating superuser..."
    $PYTHON_CMD manage.py createsuperuser
fi

echo "===== Setup Complete ====="
echo "To run the development server, use:"
echo "source venv/bin/activate"
echo "$PYTHON_CMD manage.py runserver --noreload"
echo ""
echo "Do you want to run the development server now? (y/n)"
read -r RUN_SERVER
if [ "$RUN_SERVER" = "y" ] || [ "$RUN_SERVER" = "Y" ]; then
    echo "🚀 Starting development server..."
    $PYTHON_CMD manage.py runserver --noreload
fi
