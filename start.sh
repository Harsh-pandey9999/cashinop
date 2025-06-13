#!/bin/bash

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is in use. Attempting to free it..."
        sudo lsof -ti :$1 | xargs -r sudo kill -9
        sleep 2
    fi
}

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install/upgrade required packages
echo "Installing/upgrading required packages..."
pip install -r requirements.txt

# Check and free port 8000
check_port 8000

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Start the server
echo "Starting Django development server..."
python manage.py runserver 8000 