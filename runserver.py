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
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Casino.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Add --noreload flag if not present to prevent double reloading
    if 'runserver' in sys.argv and '--noreload' not in sys.argv:
        sys.argv.append('--noreload')
    
    # Add watchman for better file watching
    if 'runserver' in sys.argv and '--watchman' not in sys.argv:
        try:
            import watchman
            sys.argv.append('--watchman')
        except ImportError:
            pass
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
