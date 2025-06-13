#!/bin/bash

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Setting up Casino Partners Locally...  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✓ Using Python $PYTHON_VERSION${NC}"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv || { echo -e "${RED}Failed to create virtual environment.${NC}"; exit 1; }
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate || { echo -e "${RED}Failed to activate virtual environment.${NC}"; exit 1; }

# Upgrade pip
echo -e "${YELLOW}🔧 Upgrading pip...${NC}"
pip install --upgrade pip || echo -e "${RED}Warning: Failed to upgrade pip. Continuing anyway...${NC}"

# Install dependencies
echo -e "${YELLOW}🔧 Installing dependencies...${NC}"
pip install -r requirements.txt || { echo -e "${RED}Failed to install dependencies.${NC}"; exit 1; }

# Create necessary directories
echo -e "${YELLOW}🔧 Creating necessary directories...${NC}"
mkdir -p media static logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}🔧 Creating .env file...${NC}"
    cat > .env << EOL
DJANGO_ENVIRONMENT=development
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
EOL
    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Run migrations
echo -e "${YELLOW}🔧 Running database migrations...${NC}"
python manage.py makemigrations || { echo -e "${RED}Failed to make migrations.${NC}"; exit 1; }
python manage.py migrate || { echo -e "${RED}Failed to apply migrations.${NC}"; exit 1; }

# Collect static files
echo -e "${YELLOW}🔧 Collecting static files...${NC}"
python manage.py collectstatic --noinput || { echo -e "${RED}Failed to collect static files.${NC}"; exit 1; }

# Create superuser if needed
echo -e "${YELLOW}Would you like to create a superuser? (y/n)${NC}"
read -r CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ] || [ "$CREATE_SUPERUSER" = "Y" ]; then
    echo -e "${YELLOW}🔧 Creating superuser...${NC}"
    python manage.py createsuperuser || echo -e "${RED}Warning: Failed to create superuser.${NC}"
fi

# Create initial data
echo -e "${YELLOW}🔧 Creating initial data...${NC}"
python manage.py shell -c "from Core.models import SiteSettings; SiteSettings.objects.get_or_create(site_name='Casino Partners', description='Casino Partners Admin Dashboard')" || echo -e "${RED}Warning: Failed to create initial site settings.${NC}"
python manage.py shell -c "from Core.models import Contact; Contact.objects.get_or_create(email='contact@example.com', phone='+1234567890', address='123 Casino Street, Las Vegas, NV')" || echo -e "${RED}Warning: Failed to create initial contact information.${NC}"

echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Starting Development Server...        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

echo -e "${GREEN}The application will be available at:${NC}"
echo -e "${BLUE}• Main site: http://127.0.0.1:8000/${NC}"
echo -e "${BLUE}• Admin dashboard: http://127.0.0.1:8000/admin${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Start the development server with --noreload to prevent auto-reloading
python manage.py runserver --noreload 