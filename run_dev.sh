#!/bin/bash

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if virtual environment is activated
check_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
        source venv/bin/activate || { echo -e "${RED}Failed to activate virtual environment.${NC}"; exit 1; }
    fi
}

# Function to check if all required directories exist
check_directories() {
    local dirs=("media" "static" "logs" "staticfiles")
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            echo -e "${YELLOW}🔧 Creating $dir directory...${NC}"
            mkdir -p "$dir"
        fi
    done
}

# Function to check if database exists
check_database() {
    if [ ! -f "db.sqlite3" ]; then
        echo -e "${YELLOW}🔧 Initializing database...${NC}"
        python manage.py makemigrations || { echo -e "${RED}Failed to make migrations.${NC}"; exit 1; }
        python manage.py migrate || { echo -e "${RED}Failed to apply migrations.${NC}"; exit 1; }
    fi
}

# Function to check if static files are collected
check_static_files() {
    if [ ! -d "staticfiles" ] || [ -z "$(ls -A staticfiles 2>/dev/null)" ]; then
        echo -e "${YELLOW}🔧 Collecting static files...${NC}"
        python manage.py collectstatic --noinput || { echo -e "${RED}Failed to collect static files.${NC}"; exit 1; }
    fi
}

# Function to check if .env file exists
check_env_file() {
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
}

# Main execution
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Starting Casino Partners Development   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Run all checks
check_venv
check_directories
check_database
check_static_files
check_env_file

echo -e "${GREEN}✓ All checks passed${NC}"
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Starting Development Server...        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

echo -e "${GREEN}The application will be available at:${NC}"
echo -e "${BLUE}• Main site: http://127.0.0.1:8000/${NC}"
echo -e "${BLUE}• Admin dashboard: http://127.0.0.1:8000/admin${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Start the development server with auto-reload
python manage.py runserver 