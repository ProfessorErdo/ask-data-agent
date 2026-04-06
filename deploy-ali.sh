#!/bin/bash

# Ask Data Deployment Script for Alibaba Cloud Lightweight Server
# Usage: ./deploy-ali.sh [start|stop|restart|status|build]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory (script location)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
ENV_FILE="$PROJECT_DIR/.env"
LOG_FILE="$PROJECT_DIR/deploy.log"
PID_FILE="$PROJECT_DIR/.server.pid"

# Default port
DEFAULT_PORT=8080

# Use uv for Python (auto-detected, falls back to pip)
USE_UV=false

log() {
    echo -e "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_python_deps() {
    log "${YELLOW}Checking Python dependencies...${NC}"

    # Check uv (preferred)
    if command -v uv &> /dev/null; then
        log "${GREEN}uv: $(uv --version)${NC}"
        USE_UV=true
        return
    fi

    # Fallback to pip
    log "${YELLOW}uv not found, falling back to pip3...${NC}"
    USE_UV=false

    if ! command -v pip3 &> /dev/null; then
        log "${RED}pip3 not found. Please install pip3 or uv.${NC}"
        exit 1
    fi
    log "${GREEN}pip3 available${NC}"
}

check_dependencies() {
    log "${YELLOW}Checking dependencies...${NC}"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log "${RED}Python3 not found. Please install Python3.${NC}"
        exit 1
    fi
    log "${GREEN}Python3: $(python3 --version)${NC}"

    check_python_deps

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log "${RED}Node.js not found. Please install Node.js.${NC}"
        exit 1
    fi
    log "${GREEN}Node.js: $(node --version)${NC}"

    # Check npm
    if ! command -v npm &> /dev/null; then
        log "${RED}npm not found. Please install npm.${NC}"
        exit 1
    fi
    log "${GREEN}npm: $(npm --version)${NC}"
}

check_env_file() {
    # Create .env if not exists
    if [ ! -f "$ENV_FILE" ]; then
        log "${YELLOW}Creating .env file...${NC}"
        cat > "$ENV_FILE" << EOF
OLLAMA_API_KEY=
OLLAMA_BASE_URL=https://ollama.com/api
SERVER_PORT=$DEFAULT_PORT
EOF
        log "${YELLOW}Created $ENV_FILE. Please add your OLLAMA_API_KEY.${NC}"
        exit 1
    fi

    # Ensure BASE_URL exists (add default if missing)
    if ! grep -q "OLLAMA_BASE_URL" "$ENV_FILE"; then
        echo "OLLAMA_BASE_URL=https://ollama.com/api" >> "$ENV_FILE"
        log "${GREEN}Added default OLLAMA_BASE_URL to .env${NC}"
    fi

    # Ensure SERVER_PORT exists (add default if missing)
    if ! grep -q "SERVER_PORT" "$ENV_FILE"; then
        echo "SERVER_PORT=$DEFAULT_PORT" >> "$ENV_FILE"
        log "${GREEN}Added default SERVER_PORT to .env${NC}"
    fi

    # Check if API key is set
    API_KEY=$(grep "OLLAMA_API_KEY" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
    if [ -z "$API_KEY" ]; then
        log "${RED}OLLAMA_API_KEY is not set in .env file. Please configure it first.${NC}"
        exit 1
    fi
    log "${GREEN}.env file configured${NC}"
}

install_backend_deps() {
    log "${YELLOW}Installing backend dependencies...${NC}"

    cd "$PROJECT_DIR"

    if [ "$USE_UV" = true ]; then
        # Use uv with pyproject.toml and uv.lock
        if [ -f "$PROJECT_DIR/pyproject.toml" ]; then
            uv sync --quiet
            log "${GREEN}Backend dependencies installed (uv)${NC}"
        elif [ -f "$BACKEND_DIR/requirements.txt" ]; then
            uv pip install -r "$BACKEND_DIR/requirements.txt" --quiet
            log "${GREEN}Backend dependencies installed (uv pip)${NC}"
        else
            log "${RED}No pyproject.toml or requirements.txt found${NC}"
            exit 1
        fi
    else
        # Fallback to pip
        if [ -f "$BACKEND_DIR/requirements.txt" ]; then
            pip3 install -r "$BACKEND_DIR/requirements.txt" --quiet
            log "${GREEN}Backend dependencies installed (pip)${NC}"
        else
            log "${RED}requirements.txt not found${NC}"
            exit 1
        fi
    fi
}

install_frontend_deps() {
    log "${YELLOW}Installing frontend dependencies...${NC}"

    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        npm install --silent
        log "${GREEN}Frontend dependencies installed${NC}"
    else
        log "${GREEN}Frontend dependencies already installed${NC}"
    fi
}

build_frontend() {
    log "${YELLOW}Building frontend...${NC}"

    cd "$FRONTEND_DIR"
    npm run build

    if [ -d "$FRONTEND_DIR/dist" ]; then
        log "${GREEN}Frontend built successfully${NC}"
    else
        log "${RED}Frontend build failed${NC}"
        exit 1
    fi

    cd "$PROJECT_DIR"
}

start_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log "${YELLOW}Server already running (PID: $PID)${NC}"
            return 0
        fi
    fi

    log "${YELLOW}Starting server...${NC}"

    # Get port from .env or use default
    PORT=$(grep SERVER_PORT "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' || echo "$DEFAULT_PORT")

    cd "$PROJECT_DIR"

    # Use uv run if uv is available, otherwise use python3 directly
    if [ "$USE_UV" = true ]; then
        nohup uv run python "$BACKEND_DIR/main.py" > "$LOG_FILE" 2>&1 &
    else
        nohup python3 "$BACKEND_DIR/main.py" > "$LOG_FILE" 2>&1 &
    fi

    PID=$!
    echo $PID > "$PID_FILE"

    sleep 2

    if ps -p $PID > /dev/null 2>&1; then
        log "${GREEN}Server started successfully (PID: $PID)${NC}"
        log "${GREEN}Server running on port $PORT${NC}"
        log "${GREEN}Access at: http://localhost:$PORT${NC}"
    else
        log "${RED}Server failed to start. Check $LOG_FILE for details.${NC}"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log "${YELLOW}Stopping server (PID: $PID)...${NC}"
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
            rm -f "$PID_FILE"
            log "${GREEN}Server stopped${NC}"
        else
            log "${YELLOW}Server not running (stale PID file removed)${NC}"
            rm -f "$PID_FILE"
        fi
    else
        log "${YELLOW}No PID file found. Server may not be running.${NC}"

        # Try to find and kill by port
        PORT=$(grep SERVER_PORT "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' || echo "$DEFAULT_PORT")
        PID_BY_PORT=$(lsof -ti:$PORT 2>/dev/null || true)
        if [ -n "$PID_BY_PORT" ]; then
            log "${YELLOW}Found process on port $PORT, stopping...${NC}"
            kill $PID_BY_PORT
            log "${GREEN}Process stopped${NC}"
        fi
    fi
}

show_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            PORT=$(grep SERVER_PORT "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' || echo "$DEFAULT_PORT")
            log "${GREEN}Server is running (PID: $PID, Port: $PORT)${NC}"

            # Show recent logs
            log "${YELLOW}Recent logs:${NC}"
            tail -5 "$LOG_FILE" 2>/dev/null || true
        else
            log "${RED}Server not running (stale PID file)${NC}"
        fi
    else
        log "${RED}Server not running${NC}"
    fi
}

build_all() {
    check_dependencies
    check_env_file
    install_backend_deps
    install_frontend_deps
    build_frontend
    log "${GREEN}Build completed successfully!${NC}"
}

full_deploy() {
    log "${GREEN}=== Starting full deployment ===${NC}"
    stop_server 2>/dev/null || true
    build_all
    start_server
    log "${GREEN}=== Deployment completed ===${NC}"
}

# Main command handler
case "$1" in
    start)
        check_dependencies
        check_env_file
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        check_dependencies
        check_env_file
        start_server
        ;;
    status)
        show_status
        ;;
    build)
        build_all
        ;;
    deploy|"")
        full_deploy
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|build|deploy}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (build + start) [default]"
        echo "  build   - Install dependencies and build frontend only"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Show server status and recent logs"
        exit 1
        ;;
esac