#!/bin/bash

# Kill any existing Django server processes
pkill -f "python manage.py runserver"

# Activate virtual environment
source venv/bin/activate

# Clear Django cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Clear Python cache files
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

# Start Django server
python manage.py runserver --noreload 