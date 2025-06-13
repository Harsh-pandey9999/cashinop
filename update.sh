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

# Function to run migrations
run_migrations() {
    echo -e "${YELLOW}🔧 Running migrations...${NC}"
    python manage.py makemigrations || { echo -e "${RED}Failed to make migrations.${NC}"; exit 1; }
    python manage.py migrate || { echo -e "${RED}Failed to apply migrations.${NC}"; exit 1; }
    echo -e "${GREEN}✓ Migrations completed successfully${NC}"
}

# Function to collect static files
collect_static() {
    echo -e "${YELLOW}🔧 Collecting static files...${NC}"
    python manage.py collectstatic --noinput || { echo -e "${RED}Failed to collect static files.${NC}"; exit 1; }
    echo -e "${GREEN}✓ Static files collected successfully${NC}"
}

# Function to clear cache
clear_cache() {
    echo -e "${YELLOW}🔧 Clearing cache...${NC}"
    python manage.py clearcache || echo -e "${YELLOW}Warning: Cache clearing not available.${NC}"
    echo -e "${GREEN}✓ Cache cleared${NC}"
}

# Main execution
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Updating Casino Partners Project       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Run all updates
check_venv
run_migrations
collect_static
clear_cache

echo -e "${GREEN}✓ All updates completed successfully!${NC}"
echo -e "${YELLOW}You can now restart the development server if needed.${NC}" 