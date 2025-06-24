#!/bin/bash

# Casino Partners - GoDaddy cPanel Deployment Script
# This script automates the deployment process to a GoDaddy cPanel hosting account via SSH

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Casino Partners - cPanel Deployment Tool  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# Configuration variables - Edit these before running
CPANEL_USERNAME="ek98vz7vcj00"
CPANEL_DOMAIN="cashinopartners.com"
CPANEL_HOST="cashinopartners.com"  # Add your cPanel hostname
CPANEL_PORT="22"
REMOTE_DIR="/home/$CPANEL_USERNAME/public_html"  # Remote directory path
DB_NAME="cashinopartners"
DB_USER="cashinopartners"
DB_PASSWORD="cashinopartners"
PYTHON_VERSION="3.11.11"  # Specify the Python version available on your cPanel

# Check if configuration is set
if [ -z "$CPANEL_USERNAME" ] || [ -z "$CPANEL_DOMAIN" ] || [ -z "$CPANEL_HOST" ]; then
    echo -e "${YELLOW}Please edit this script to set your cPanel configuration variables before running.${NC}"
    echo -e "${YELLOW}Open deploy_to_cpanel.sh in a text editor and fill in the variables at the top.${NC}"
    exit 1
fi

# Function to display steps
show_step() {
    echo -e "\n${GREEN}Step $1: $2${NC}"
}

# Function to handle errors
handle_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Function to execute remote commands
execute_remote_command() {
    local command="$1"
    ssh -p "$CPANEL_PORT" "$CPANEL_USERNAME@$CPANEL_HOST" "$command" || handle_error "Failed to execute remote command: $command"
}

# Prepare local files for deployment
show_step 1 "Preparing local files for deployment"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    handle_error "Python 3 is not installed. Please install Python 3 and try again."
fi

# Create production settings if needed
if [ ! -f "Casino/production_settings.py" ]; then
    echo -e "${YELLOW}Creating production settings file...${NC}"
    cat > Casino/production_settings.py << EOF
from Casino.settings import *

DEBUG = False
ALLOWED_HOSTS = ['$CPANEL_DOMAIN', 'www.$CPANEL_DOMAIN']

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '$DB_NAME',
        'USER': '$DB_USER',
        'PASSWORD': '$DB_PASSWORD',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Update these with your email settings
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = 'noreply@$CPANEL_DOMAIN'
EOF
    echo -e "${GREEN}✅ Production settings created.${NC}"
else
    echo -e "${GREEN}✅ Production settings already exist.${NC}"
fi

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python3 manage.py collectstatic --noinput --settings=Casino.production_settings || handle_error "Failed to collect static files"
echo -e "${GREEN}✅ Static files collected.${NC}"

# Create .htaccess file for cPanel
echo -e "${YELLOW}Creating .htaccess file...${NC}"
cat > .htaccess << EOF
# Redirect to HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Serve static files directly
RewriteRule ^static/(.*)$ /staticfiles/\$1 [L]
RewriteRule ^media/(.*)$ /media/\$1 [L]

# Pass all other requests to Passenger
RewriteCond %{REQUEST_URI} !^/static/
RewriteCond %{REQUEST_URI} !^/media/
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [QSA,L]
EOF
echo -e "${GREEN}✅ .htaccess file created.${NC}"

# Create a deployment package
show_step 2 "Creating deployment package"
echo -e "${YELLOW}Creating deployment archive...${NC}"
DEPLOY_ARCHIVE="casino_deploy.tar.gz"
tar --exclude="venv" --exclude=".git" --exclude="*.pyc" --exclude="__pycache__" --exclude="$DEPLOY_ARCHIVE" -czf $DEPLOY_ARCHIVE .
echo -e "${GREEN}✅ Deployment archive created: $DEPLOY_ARCHIVE${NC}"

# Deploy to cPanel via SSH
show_step 3 "Deploying to cPanel via SSH"

# Upload the archive
echo -e "${YELLOW}Uploading deployment archive...${NC}"
scp -P "$CPANEL_PORT" "$DEPLOY_ARCHIVE" "$CPANEL_USERNAME@$CPANEL_HOST:$REMOTE_DIR/" || handle_error "Failed to upload deployment archive"
echo -e "${GREEN}✅ Archive uploaded successfully.${NC}"

# Remote deployment commands
echo -e "${YELLOW}Executing remote deployment steps...${NC}"

# Extract archive and run deployment commands
execute_remote_command "cd $REMOTE_DIR && \
    tar xzf $DEPLOY_ARCHIVE && \
    rm $DEPLOY_ARCHIVE && \
    source ~/virtualenv/python$PYTHON_VERSION/bin/activate && \
    pip install -r requirements.txt && \
    python manage.py migrate --settings=Casino.production_settings && \
    python manage.py collectstatic --noinput --settings=Casino.production_settings"

echo -e "${GREEN}✅ Remote deployment completed successfully.${NC}"

# Clean up local archive
show_step 4 "Cleaning up"
echo -e "${YELLOW}Removing local deployment archive...${NC}"
rm "$DEPLOY_ARCHIVE" || handle_error "Failed to remove local deployment archive"
echo -e "${GREEN}✅ Local cleanup completed.${NC}"

# Final instructions
show_step 5 "Final steps"
echo -e "${YELLOW}Deployment completed! Please verify:${NC}"
echo -e "1. Visit https://$CPANEL_DOMAIN to check if the site is working"
echo -e "2. Check the error logs in cPanel if you encounter any issues"
echo -e "3. Verify that SSL is properly configured"
echo -e "4. Test all critical functionality of your application"

echo -e "\n${GREEN}Deployment process completed successfully!${NC}"
