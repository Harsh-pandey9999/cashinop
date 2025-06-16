#!/bin/bash

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

<<<<<<< HEAD
=======
# Configuration
PROJECT_NAME="Casino"
VENV_DIR="venv"
PROJECT_DIR=$(pwd)
RUN_DIR="$PROJECT_DIR/run"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$RUN_DIR/$PROJECT_NAME.pid"
LOG_FILE="$LOG_DIR/development.log"
PORT=8080

# Ensure required directories exist
mkdir -p "$LOG_DIR" "$RUN_DIR"
chmod 755 "$LOG_DIR" "$RUN_DIR"

>>>>>>> e2fe89af (Initial commit with cleaned .gitignore)
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

<<<<<<< HEAD
# Main execution
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Starting Casino Partners Development   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
=======
# Function to check if port is in use
is_port_in_use() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i ":$port" -sTCP:LISTEN -t >/dev/null; then
            echo "Port $port is in use by:"
            lsof -i ":$port" -sTCP:LISTEN
            return 0
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -tuln | grep -q ":$port .*LISTEN"; then
            echo "Port $port is in use"
            return 0
        fi
    fi
    return 1
}

# Function to kill process on a port
kill_process_on_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        local pid=$(lsof -t -i ":$port" -sTCP:LISTEN)
        if [ -n "$pid" ]; then
            echo -e "${YELLOW}⚠️  Killing process $pid on port $port...${NC}"
            kill -9 "$pid"
            sleep 1
            # Verify process was killed
            if lsof -t -i ":$port" -sTCP:LISTEN >/dev/null; then
                echo -e "${RED}❌ Failed to kill process on port $port${NC}"
                return 1
            fi
        fi
    fi
    return 0
}

# Function to start the development server
start_server() {
    # Check if port is in use
    if is_port_in_use $PORT; then
        echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
        read -p "Do you want to kill the process using port $PORT? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if ! kill_process_on_port $PORT; then
                echo -e "${RED}❌ Failed to free up port $PORT${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  Please free port $PORT and try again${NC}"
            exit 1
        fi
    fi

    echo -e "${GREEN}🚀 Starting $PROJECT_NAME development server...${NC}"
    
    # Activate virtual environment
    check_venv
    
    # Install/update dependencies
    echo -e "${YELLOW}🔧 Checking dependencies...${NC}"
    pip install -r requirements.txt
    
    # Run database migrations
    echo -e "${YELLOW}🔄 Applying database migrations...${NC}"
    python manage.py migrate --noinput
    
    # Collect static files
    echo -e "${YELLOW}📦 Collecting static files...${NC}"
    python manage.py collectstatic --noinput
    
    # Start the development server with auto-reload
    echo -e "${GREEN}🚀 Starting development server with auto-reload on port $PORT...${NC}"
    nohup python manage.py runserver 0.0.0.0:$PORT >> "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    
    # Verify server started
    sleep 2
    if ! ps -p $SERVER_PID > /dev/null; then
        echo -e "${RED}❌ Failed to start server. Check logs at $LOG_FILE${NC}"
        tail -n 20 "$LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Server started successfully! (PID: $SERVER_PID)${NC}"
    echo -e "${BLUE}🌐 Access the site at: http://localhost:$PORT${NC}"
    echo -e "${YELLOW}📝 View logs at: $LOG_FILE${NC}"
}

# Function to stop the server
stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && ps -p $PID > /dev/null; then
            echo -e "${YELLOW}🛑 Stopping $PROJECT_NAME server (PID: $PID)...${NC}"
            kill $PID 2>/dev/null || true
            
            # Wait for process to terminate
            local timeout=5
            while [ $timeout -gt 0 ] && ps -p $PID > /dev/null; do
                echo -n "."
                sleep 1
                ((timeout--))
            done
            
            if ps -p $PID > /dev/null; then
                echo -e "\n${YELLOW}⚠️  Server did not stop gracefully, forcing termination...${NC}"
                kill -9 $PID 2>/dev/null || true
            fi
            
            echo -e "\n${GREEN}✅ Server stopped successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  Server PID file exists but process $PID is not running${NC}"
        fi
        rm -f "$PID_FILE"
    else
        echo -e "${YELLOW}ℹ️  No running server found (no PID file at $PID_FILE)${NC}"
        
        # Try to find and kill any remaining server processes
        local server_pids=$(pgrep -f "python.*manage.py runserver" || true)
        if [ -n "$server_pids" ]; then
            echo -e "${YELLOW}⚠️  Found potential orphaned server processes, cleaning up...${NC}"
            echo $server_pids | xargs kill -9 2>/dev/null || true
            echo -e "${GREEN}✅ Cleaned up orphaned processes${NC}"
        fi
    fi
}

# Function to check server status
status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo -e "${GREEN}✅ $PROJECT_NAME server is running (PID: $PID)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Server PID file exists but process is not running${NC}"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo -e "${YELLOW}ℹ️  $PROJECT_NAME server is not running${NC}"
        return 1
    fi
}

# Main execution
case "$1" in
    start)
        if status_server; then
            echo -e "${YELLOW}ℹ️  Server is already running${NC}"
            exit 1
        fi
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        start_server
        ;;
    status)
        status_server
        ;;
    *)
        echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║  $PROJECT_NAME Development Manager       ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
        echo -e "Usage: $0 {start|stop|restart|status}"
        echo -e "  start   - Start the development server"
        echo -e "  stop    - Stop the development server"
        echo -e "  restart - Restart the development server"
        echo -e "  status  - Check server status"
        exit 1
        ;;
esac
>>>>>>> e2fe89af (Initial commit with cleaned .gitignore)

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

<<<<<<< HEAD
# Start the development server with auto-reload
python manage.py runserver 
=======
# Start the development server with auto-reload on port 8000
python manage.py runserver 0.0.0.0:8000
>>>>>>> e2fe89af (Initial commit with cleaned .gitignore)
