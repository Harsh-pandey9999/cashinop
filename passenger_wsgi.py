import os
import sys
import site
from pathlib import Path

# Set the project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set the virtual environment path
INTERP = os.path.expanduser("~/venv/bin/python")
if sys.executable != INTERP and os.path.exists(INTERP):
    os.execl(INTERP, INTERP, *sys.argv)

# Add the site-packages of the virtual environment
site.addsitedir(os.path.expanduser('~/venv/lib/python3.8/site-packages'))

# Add the project directory to the Python path
sys.path.insert(0, PROJECT_DIR)

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Casino.settings')
os.environ['PYTHON_EGG_CACHE'] = os.path.join(PROJECT_DIR, '.python-egg')

# Create necessary directories
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(os.path.join(PROJECT_DIR, '.python-egg'), exist_ok=True)

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'passenger_wsgi.log')),
        logging.StreamHandler()
    ]
)

# Initialize WSGI application
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    logging.info('Application started successfully')
except Exception as e:
    logging.error('Error starting application: %s', str(e), exc_info=True)
    if 'APPLICATION_ROOT' in os.environ:
        raise
