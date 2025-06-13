#!/bin/bash

# Casino Affiliate System Setup and Run Script
# Enhanced version with better error handling and additional features

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Setting up Casino Affiliate System...  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv || { echo -e "${RED}Failed to create virtual environment. Please check your Python installation.${NC}"; exit 1; }
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate || { echo -e "${RED}Failed to activate virtual environment.${NC}"; exit 1; }

# Verify Python version
python_version=$(python --version 2>&1)
echo -e "${GREEN}Using $python_version${NC}"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip || echo -e "${RED}Warning: Failed to upgrade pip. Continuing anyway...${NC}"
pip install -r requirements.txt || { echo -e "${RED}Failed to install dependencies. Please check your requirements.txt file.${NC}"; exit 1; }

# Create media directory if it doesn't exist
if [ ! -d "media" ]; then
    echo -e "${YELLOW}Creating media directory...${NC}"
    mkdir -p media
fi

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py makemigrations || { echo -e "${RED}Failed to make migrations.${NC}"; exit 1; }
python manage.py migrate || { echo -e "${RED}Failed to apply migrations.${NC}"; exit 1; }

# Create initial data if database is empty
python manage.py shell -c "from django.contrib.auth.models import User; exit(0 if User.objects.exists() else 1)" &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Would you like to create initial data (superuser, site settings, etc.)? (y/n)${NC}"
    read create_initial_data
    if [ "$create_initial_data" = "y" ]; then
        # Create superuser
        echo -e "${YELLOW}Creating superuser...${NC}"
        python manage.py createsuperuser || echo -e "${RED}Warning: Failed to create superuser.${NC}"
        
        # Create initial site settings
        echo -e "${YELLOW}Creating initial site settings...${NC}"
        python manage.py shell -c "from Core.models import SiteSettings; SiteSettings.objects.get_or_create(site_name='Casino Admin Dashboard', description='Casino Admin Dashboard')" || echo -e "${RED}Warning: Failed to create initial site settings.${NC}"
        
        # Create initial contact info
        echo -e "${YELLOW}Creating initial contact information...${NC}"
        python manage.py shell -c "from Core.models import Contact; Contact.objects.get_or_create(email='contact@example.com', phone='+1234567890', address='123 Casino Street, Las Vegas, NV')" || echo -e "${RED}Warning: Failed to create initial contact information.${NC}"
        
        touch .initial_setup_complete
    fi
fi

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput || { echo -e "${RED}Failed to collect static files.${NC}"; exit 1; }

# Run the development server
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}Starting development server...${NC}"
echo -e "${BLUE}The application will be available at http://127.0.0.1:8000/${NC}"
echo -e "${YELLOW}Admin dashboard: http://127.0.0.1:8000/dashboard${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
python manage.py runserver
