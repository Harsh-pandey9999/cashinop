import os
import sys
from pathlib import Path

# Add the project directory to the Python path
INTERP = os.path.expanduser("~/venv/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Casino.production_settings')

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Create necessary directories
BASE_DIR = Path(__file__).resolve().parent
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'django_cache'), exist_ok=True)

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
