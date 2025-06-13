# Casino Partners - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Casino Partners Django application to a production environment. Follow these steps carefully to ensure a secure and optimized deployment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Application Deployment](#application-deployment)
5. [Security Configuration](#security-configuration)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Python 3.10 or higher
- MySQL 8.0 or higher
- Redis 6.0 or higher
- Nginx 1.18 or higher
- Supervisor 4.2 or higher
- Git

### Required Accounts/Services
- GoDaddy cPanel account
- MySQL database
- Redis server
- SMTP email service
- Sentry account (for error tracking)
- SSL certificate

## Environment Setup

### 1. Server Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv nginx redis-server mysql-server supervisor

# Create application directory
sudo mkdir -p /var/www/casino
sudo chown -R $USER:$USER /var/www/casino
```

### 2. Python Environment
```bash
# Create and activate virtual environment
python3 -m venv /var/www/casino/venv
source /var/www/casino/venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root:
```bash
# Django Settings
DJANGO_ENVIRONMENT=production
DJANGO_SECRET_KEY=your-secure-secret-key
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Database Settings
DB_NAME=casino_db
DB_USER=casino_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=3306

# Redis Settings
REDIS_URL=redis://localhost:6379/1
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Sentry Settings
SENTRY_DSN=your-sentry-dsn

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Database Configuration

### 1. MySQL Setup
```sql
-- Create database and user
CREATE DATABASE casino_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'casino_user'@'localhost' IDENTIFIED BY 'your-secure-password';
GRANT ALL PRIVILEGES ON casino_db.* TO 'casino_user'@'localhost';
FLUSH PRIVILEGES;

-- Create required indexes
ALTER TABLE Core_gamecards ADD INDEX idx_slug (slug);
ALTER TABLE Core_casinouser ADD INDEX idx_username (username);
ALTER TABLE Core_sitesetting ADD INDEX idx_key (key);
```

### 2. Database Migration
```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (if any)
python manage.py loaddata initial_data.json
```

## Application Deployment

### 1. Static Files
```bash
# Collect static files
python manage.py collectstatic --noinput

# Compress static files
python manage.py compress --force
```

### 2. Nginx Configuration
Create `/etc/nginx/sites-available/casino`:
```nginx
upstream casino_app {
    server unix:/var/www/casino/gunicorn.sock;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_stapling on;
    ssl_stapling_verify on;
    add_header Strict-Transport-Security "max-age=31536000" always;

    client_max_body_size 10M;
    keepalive_timeout 65;

    # Static files
    location /static/ {
        alias /var/www/casino/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Media files
    location /media/ {
        alias /var/www/casino/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Django application
    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://casino_app;
        proxy_redirect off;
    }

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:; connect-src 'self' https:; frame-ancestors 'none';" always;
}
```

### 3. Gunicorn Configuration
Create `/var/www/casino/gunicorn_config.py`:
```python
import multiprocessing
import os

# Server socket
bind = "unix:/var/www/casino/gunicorn.sock"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/www/casino/logs/gunicorn-access.log"
errorlog = "/var/www/casino/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "casino_gunicorn"

# SSL
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = "/var/www/casino/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Casino.settings")
```

### 4. Supervisor Configuration
Create `/etc/supervisor/conf.d/casino.conf`:
```ini
[program:casino]
directory=/var/www/casino
command=/var/www/casino/venv/bin/gunicorn -c gunicorn_config.py Casino.wsgi:application
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/www/casino/logs/supervisor.err.log
stdout_logfile=/var/www/casino/logs/supervisor.out.log
environment=DJANGO_ENVIRONMENT="production"
```

## Security Configuration

### 1. SSL Certificate
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 2. Firewall Configuration
```bash
# Configure UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Security Headers
Verify all security headers are properly set in Nginx configuration and Django settings.

## Performance Optimization

### 1. Redis Caching
```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Add/modify these settings:
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
```

### 2. Database Optimization
```sql
-- Add indexes for frequently queried fields
ALTER TABLE Core_gamecards ADD INDEX idx_created_at (created_at);
ALTER TABLE Core_casinouser ADD INDEX idx_last_login (last_login);
ALTER TABLE Core_pagevisit ADD INDEX idx_timestamp (timestamp);

-- Optimize tables
OPTIMIZE TABLE Core_gamecards, Core_casinouser, Core_pagevisit;
```

### 3. Static File Optimization
```bash
# Install and configure django-compressor
pip install django-compressor

# Add to INSTALLED_APPS in settings.py
INSTALLED_APPS += ['compressor']

# Configure compression
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]
```

## Monitoring and Maintenance

### 1. Log Rotation
Create `/etc/logrotate.d/casino`:
```
/var/www/casino/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        [ -f /var/www/casino/gunicorn.pid ] && kill -USR1 $(cat /var/www/casino/gunicorn.pid)
    endscript
}
```

### 2. Backup Strategy
Create `/var/www/casino/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/www/casino/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u casino_user -p casino_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/casino/media

# Backup code
tar -czf $BACKUP_DIR/code_$DATE.tar.gz /var/www/casino

# Remove backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

### 3. Monitoring Setup
```bash
# Install monitoring tools
pip install django-prometheus

# Add to INSTALLED_APPS
INSTALLED_APPS += ['django_prometheus']

# Configure Prometheus metrics endpoint
urlpatterns += [
    path('', include('django_prometheus.urls')),
]
```

## Troubleshooting

### Common Issues and Solutions

1. **Database Connection Issues**
   - Check MySQL service status: `sudo systemctl status mysql`
   - Verify database credentials in `.env`
   - Check database connection: `mysql -u casino_user -p casino_db`

2. **Static Files Not Loading**
   - Verify static files collection: `python manage.py collectstatic --dry-run`
   - Check Nginx configuration for static file paths
   - Verify file permissions: `sudo chown -R www-data:www-data /var/www/casino/staticfiles`

3. **Gunicorn Issues**
   - Check Gunicorn logs: `tail -f /var/www/casino/logs/gunicorn-error.log`
   - Verify socket file: `ls -l /var/www/casino/gunicorn.sock`
   - Restart Gunicorn: `sudo supervisorctl restart casino`

4. **Redis Connection Issues**
   - Check Redis service: `sudo systemctl status redis`
   - Test Redis connection: `redis-cli ping`
   - Verify Redis configuration: `redis-cli info`

5. **SSL Certificate Issues**
   - Check certificate status: `sudo certbot certificates`
   - Renew certificates: `sudo certbot renew --dry-run`
   - Verify SSL configuration: `curl -vI https://your-domain.com`

### Maintenance Commands

```bash
# Restart services
sudo systemctl restart nginx
sudo supervisorctl restart casino
sudo systemctl restart redis
sudo systemctl restart mysql

# Check logs
tail -f /var/www/casino/logs/gunicorn-error.log
tail -f /var/www/casino/logs/nginx-error.log
tail -f /var/www/casino/logs/django.log

# Database maintenance
python manage.py dbshell
python manage.py check --deploy
python manage.py showmigrations

# Cache maintenance
redis-cli FLUSHALL
python manage.py clearcache

# Static files
python manage.py collectstatic --noinput
python manage.py compress --force
```

## Regular Maintenance Tasks

1. **Daily Tasks**
   - Monitor error logs
   - Check backup status
   - Verify SSL certificate validity
   - Monitor server resources

2. **Weekly Tasks**
   - Review and rotate logs
   - Check database performance
   - Verify security updates
   - Monitor disk usage

3. **Monthly Tasks**
   - Update system packages
   - Review and update dependencies
   - Perform database optimization
   - Review and update SSL certificates

4. **Quarterly Tasks**
   - Security audit
   - Performance review
   - Backup restoration test
   - Update deployment documentation

## Emergency Procedures

1. **Server Down**
   ```bash
   # Check service status
   sudo systemctl status nginx
   sudo systemctl status gunicorn
   sudo systemctl status redis
   sudo systemctl status mysql

   # Restart services
   sudo systemctl restart nginx
   sudo supervisorctl restart casino
   ```

2. **Database Issues**
   ```bash
   # Check database status
   sudo systemctl status mysql
   mysql -u casino_user -p -e "SHOW PROCESSLIST;"

   # Repair database
   mysqlcheck -u casino_user -p --repair casino_db
   ```

3. **Security Breach**
   - Immediately change all passwords
   - Review access logs
   - Check for unauthorized changes
   - Restore from backup if necessary
   - Update security measures

## Support and Resources

- Django Documentation: https://docs.djangoproject.com/
- Nginx Documentation: https://nginx.org/en/docs/
- MySQL Documentation: https://dev.mysql.com/doc/
- Redis Documentation: https://redis.io/documentation
- Gunicorn Documentation: https://docs.gunicorn.org/
- Supervisor Documentation: http://supervisord.org/

## Contact Information

For deployment support or emergencies, contact:
- Technical Support: support@your-domain.com
- Emergency Contact: emergency@your-domain.com
- System Administrator: admin@your-domain.com
