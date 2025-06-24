#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export DJANGO_SETTINGS_MODULE=Casino.settings
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Install watchman for better file watching
pip install watchman

# Install watchman for auto-reload
if ! command -v watchman &> /dev/null; then
    echo "Installing watchman..."
    sudo apt-get update && sudo apt-get install -y watchman
fi

# Run the development server with auto-reload
echo "Starting development server with auto-reload..."
python runserver.py runserver 0.0.0.0:8000 --nothreading --noreload

echo "Development server stopped"
