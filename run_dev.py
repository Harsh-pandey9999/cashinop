#!/usr/bin/env python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Set default settings module if not set
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Use runserver_plus if available, otherwise use runserver
    try:
        from django_extensions.management.commands.runserver_plus import Command
        runserver = 'runserver_plus'
    except ImportError:
        runserver = 'runserver'
    
    # Start development server with auto-reload
    execute_from_command_line([sys.argv[0], 'runserver', '0.0.0.0:8000', '--noreload'])

if __name__ == '__main__':
    main()
