#!/bin/bash

# 🚀 Crank Platform Development Manager
#
# Cross-platform script for local development environment management
# Compatible with: macOS, Linux (Ubuntu/Debian/RHEL/Alpine), WSL2
#
# ⚠️  ARCHITECTURE REFACTOR IN PROGRESS (Nov 2025)
# This script manages the OLD platform-centric architecture (archived).
# See docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md for new controller/worker model.
# Will be updated during Phase 2-3 to support controller/worker deployment.
#
# This script helps manage local development environments including:
# - Docker container orchestration (OLD: platform-centric, NEW: controller-centric)
# - Azure Container Registry integration
# - Multi-platform image support (ARM64/AMD64)
# - Health monitoring and testing

set -e

# Color output (works on all Unix-like systems)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }
echo_purple() { echo -e "${PURPLE}🚀 $1${NC}"; }

# Configuration
REGISTRY="crankplatformregistry.azurecr.io"
COMPOSE_FILE="docker-compose.local.yml"
ENV_FILE=".env.local"

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    PLATFORM="macOS" ;;
        Linux*)     PLATFORM="Linux" ;;
        MINGW*)     PLATFORM="Windows" ;;
        CYGWIN*)    PLATFORM="Windows" ;;
        *)          PLATFORM="Unknown" ;;
    esac

    # Check if running in WSL
    if [[ -n "${WSL_DISTRO_NAME:-}" ]] || grep -q Microsoft /proc/version 2>/dev/null; then
        PLATFORM="WSL2"
    fi

    echo_info "Detected platform: $PLATFORM"
}

# Functions
show_help() {
    echo_purple "🚀 Crank Platform Development Manager"
    echo ""
    echo "Cross-platform local development environment manager"
    echo "Compatible with: macOS, Linux (Ubuntu/Debian/RHEL/Alpine), WSL2"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Initial setup for local development"
    echo "  start     - Start all services"
    echo "  start-min - Start minimal services (no ML/CV services)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  logs      - Show logs for all services"
    echo "  status    - Show status of all services"
    echo "  update    - Pull latest images and restart"
    echo "  test      - Test all service endpoints"
    echo "  clean     - Clean up containers and volumes"
    echo "  monitor   - Monitor services in real-time"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # First time setup"
    echo "  $0 start     # Start development environment"
    echo "  $0 logs      # Watch logs"
}

check_requirements() {
    echo_info "Checking requirements for $PLATFORM..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        case $PLATFORM in
            "macOS")
                echo_error "Docker is not installed. Please install Docker Desktop for macOS from:"
                echo "https://docs.docker.com/desktop/install/mac-install/"
                ;;
            "Linux")
                echo_error "Docker is not installed. Install with:"
                echo "  # Ubuntu/Debian: sudo apt-get install docker.io docker-compose"
                echo "  # RHEL/CentOS:   sudo yum install docker docker-compose"
                echo "  # Arch:          sudo pacman -S docker docker-compose"
                ;;
            "WSL2")
                echo_error "Docker is not installed. Please install Docker Desktop for Windows with WSL2 backend:"
                echo "https://docs.docker.com/desktop/install/windows-install/"
                ;;
            *)
                echo_error "Docker is not installed. Please install Docker for your platform."
                ;;
        esac
        exit 1
    fi

    # Check Docker Compose (handle both old and new syntax)
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        case $PLATFORM in
            "macOS"|"WSL2")
                echo_error "Docker Compose is not available. Please update Docker Desktop."
                ;;
            "Linux")
                echo_error "Docker Compose is not available. Install with:"
                echo "  sudo apt-get install docker-compose  # or"
                echo "  sudo pip3 install docker-compose"
                ;;
        esac
        exit 1
    fi

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        case $PLATFORM in
            "macOS"|"WSL2")
                echo_error "Docker is not running. Please start Docker Desktop."
                ;;
            "Linux")
                echo_error "Docker is not running. Start with:"
                echo "  sudo systemctl start docker"
                echo "  sudo usermod -aG docker \$USER  # Add yourself to docker group"
                ;;
        esac
        exit 1
    fi

    # Check for required utilities
    missing_utils=()

    if ! command -v curl &> /dev/null; then
        missing_utils+=("curl")
    fi

    # Check for watch command (optional for monitor function)
    if ! command -v watch &> /dev/null; then
        echo_warning "Warning: 'watch' command not found. Monitor function will be limited."
        echo_info "Install watch with:"
        case $PLATFORM in
            "macOS")
                echo "  brew install watch"
                ;;
            "Linux")
                echo "  sudo apt-get install procps  # Ubuntu/Debian"
                echo "  sudo yum install procps-ng   # RHEL/CentOS"
                ;;
        esac
    fi

    if [ ${#missing_utils[@]} -ne 0 ]; then
        echo_error "Missing required utilities: ${missing_utils[*]}"
        case $PLATFORM in
            "macOS")
                echo "Install with: brew install ${missing_utils[*]}"
                ;;
            "Linux")
                echo "Install with: sudo apt-get install ${missing_utils[*]}  # Ubuntu/Debian"
                echo "         or: sudo yum install ${missing_utils[*]}       # RHEL/CentOS"
                ;;
        esac
        exit 1
    fi

    echo_success "All requirements satisfied for $PLATFORM"
}

# Use docker compose or docker-compose based on availability
get_compose_command() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo_error "Neither 'docker-compose' nor 'docker compose' is available"
        exit 1
    fi
}

setup_local_env() {
    echo_info "Setting up local development environment for $PLATFORM..."

    # Check for Python virtual environment
    if [ ! -d ".venv" ]; then
        echo_warning "No Python virtual environment found."
        echo_info "Setting up venv with uv (required for Phase 0+ development)..."

        if command -v uv &> /dev/null; then
            uv venv --python 3.11
            echo_success "Created .venv with Python 3.11"
            echo_info "Activate with: source .venv/bin/activate"
            echo_info "Installing dependencies: uv sync --all-extras"
            uv sync --all-extras
            echo_success "Dependencies installed"

            # Install package in editable mode for import resolution
            echo_info "Installing crank package in editable mode..."
            source .venv/bin/activate
            uv pip install -e .
            echo_success "Editable install complete - crank.* imports will now resolve"
            echo_info "See pyrightconfig.json and .vscode/settings.json for import path config"
        else
            echo_warning "uv not found. Install with:"
            case $PLATFORM in
                "macOS")
                    echo "  brew install uv"
                    ;;
                "Linux"|"WSL2")
                    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
                    ;;
            esac
            echo_info "After installing uv, run: uv venv --python 3.11 && uv sync --all-extras && uv pip install -e ."
        fi
    else
        echo_success "Python virtual environment exists at .venv"
        echo_info "To update dependencies: source .venv/bin/activate && uv sync --all-extras"

        # Check if editable install exists
        if [ -f ".venv/bin/python" ]; then
            if ! .venv/bin/python -c "import crank" 2>/dev/null; then
                echo_warning "crank package not installed in editable mode"
                echo_info "Installing editable package for import resolution..."
                source .venv/bin/activate
                uv pip install -e .
                echo_success "Editable install complete - crank.* imports will now resolve"
            else
                echo_success "crank package is installed and importable"
            fi
        fi
    fi

    # Copy local environment file
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.local" ]; then
            cp .env.local .env
            echo_success "Created .env file from .env.local"
        else
            echo_warning ".env.local template not found, creating basic .env"
            cat > .env << EOF
# Basic local development configuration
PLATFORM_PORT=8000
PLATFORM_HTTPS_PORT=8443
PLATFORM_AUTH_TOKEN=local-dev-key-secure
REGISTRY=crankplatformregistry.azurecr.io
TAG=latest
CRANK_ENVIRONMENT=development
LOG_LEVEL=DEBUG
EOF
        fi
    else
        echo_warning ".env file already exists, keeping current configuration"
    fi

    # Try to login to Azure Container Registry
    echo_info "Attempting to login to Azure Container Registry..."
    if command -v az &> /dev/null && az account show &> /dev/null; then
        if az acr login --name crankplatformregistry; then
            echo_success "Successfully logged into Azure Container Registry"
        else
            echo_warning "ACR login failed via Azure CLI"
        fi
    else
        echo_warning "Azure CLI not configured. You may need to manually login to ACR:"
        echo "  docker login $REGISTRY"
        echo_info "Or install Azure CLI:"
        case $PLATFORM in
            "macOS")
                echo "  brew install azure-cli"
                ;;
            "Linux")
                echo "  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
                ;;
            "WSL2")
                echo "  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
                ;;
        esac
    fi

    echo_success "Local environment setup complete for $PLATFORM"
}

start_services() {
    local profile=""
    local compose_cmd=$(get_compose_command)

    if [ "$1" = "minimal" ]; then
        profile="--profile minimal"
        echo_info "Starting minimal services (excluding resource-intensive ML/CV services)..."
    else
        echo_info "Starting all services..."
    fi

    $compose_cmd -f "$COMPOSE_FILE" $profile up -d

    if [ $? -eq 0 ]; then
        echo_success "Services started successfully!"
        echo_info "Platform will be available at: https://localhost:8443"
        echo_info "Run '$0 status' to check service health"

        # Platform-specific post-start info
        case $PLATFORM in
            "macOS")
                echo_info "💡 Tip: Monitor Docker Desktop resources if performance is slow"
                ;;
            "Linux")
                echo_info "💡 Tip: Use 'docker stats' to monitor resource usage"
                ;;
            "WSL2")
                echo_info "💡 Tip: Ensure WSL2 has enough memory allocated in .wslconfig"
                ;;
        esac
    else
        echo_error "Failed to start services"
        exit 1
    fi
}

stop_services() {
    local compose_cmd=$(get_compose_command)
    echo_info "Stopping all services..."
    $compose_cmd -f "$COMPOSE_FILE" down
    echo_success "All services stopped"
}

restart_services() {
    echo_info "Restarting services..."
    stop_services
    sleep 2
    start_services
}

show_logs() {
    local compose_cmd=$(get_compose_command)
    echo_info "Showing logs for all services (Ctrl+C to exit)..."
    $compose_cmd -f "$COMPOSE_FILE" logs -f
}

show_status() {
    local compose_cmd=$(get_compose_command)
    echo_info "Service Status:"
    $compose_cmd -f "$COMPOSE_FILE" ps

    echo ""
    echo_info "Quick Health Check:"

    services=(
        "platform:8443:/health/live"
        "doc-converter:8101:/health"
        "email-classifier:8201:/health"
        "email-parser:8301:/health"
        "streaming:8501:/health"
    )

    for service in "${services[@]}"; do
        IFS=':' read -r name port endpoint <<< "$service"
        if curl -k -s --max-time 5 "https://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo_success "$name is healthy"
        else
            echo_warning "$name is not responding"
        fi
    done
}

update_images() {
    local compose_cmd=$(get_compose_command)
    echo_info "Pulling latest images..."
    $compose_cmd -f "$COMPOSE_FILE" pull

    echo_info "Restarting services with updated images..."
    restart_services

    echo_success "Update complete!"
}

test_endpoints() {
    echo_info "Testing all service endpoints..."

    # Wait for services to be ready
    echo_info "Waiting for services to be ready..."
    sleep 10

    services=(
        "Platform API:https://localhost:8443/health/live"
        "Document Converter:https://localhost:8101/health"
        "Email Classifier:https://localhost:8201/health"
        "Email Parser:https://localhost:8301/health"
        "Streaming Service:https://localhost:8501/health"
    )

    for service in "${services[@]}"; do
        IFS=':' read -r name url <<< "$service"
        echo_info "Testing $name..."

        if curl -k -s --max-time 10 -w "Status: %{http_code}\n" "$url" | grep -q "200\|healthy"; then
            echo_success "$name is working correctly"
        else
            echo_error "$name failed health check"
        fi
    done

    # Test worker registration
    echo_info "Testing worker registration..."
    auth_token=$(grep PLATFORM_AUTH_TOKEN .env 2>/dev/null | cut -d= -f2 || echo "local-dev-key-secure")
    if curl -k -s --max-time 10 -H "Authorization: Bearer $auth_token" \
            "https://localhost:8443/v1/workers" | grep -q "workers"; then
        echo_success "Worker registration is working"
    else
        echo_warning "Worker registration may not be ready yet"
    fi
}

clean_environment() {
    local compose_cmd=$(get_compose_command)
    echo_warning "This will remove all containers, volumes, and images. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo_info "Cleaning up environment..."
        $compose_cmd -f "$COMPOSE_FILE" down -v --remove-orphans
        docker system prune -f
        echo_success "Environment cleaned"
    else
        echo_info "Clean cancelled"
    fi
}

monitor_services() {
    local compose_cmd=$(get_compose_command)
    echo_info "Monitoring services (Ctrl+C to exit)..."

    if command -v watch &> /dev/null; then
        watch -n 2 "$compose_cmd -f $COMPOSE_FILE ps && echo '' && docker stats --no-stream"
    else
        echo_warning "'watch' command not available. Using simple monitoring loop..."
        while true; do
            clear
            echo "$(date): Service Status"
            echo "========================"
            $compose_cmd -f "$COMPOSE_FILE" ps
            echo ""
            echo "Container Stats:"
            echo "==============="
            docker stats --no-stream
            echo ""
            echo "Press Ctrl+C to exit..."
            sleep 3
        done
    fi
}

# Main script logic
main() {
    # Detect platform first
    detect_platform

    case "${1:-help}" in
        setup)
            check_requirements
            setup_local_env
            ;;
        start)
            check_requirements
            start_services
            ;;
        start-min|start-minimal)
            check_requirements
            start_services minimal
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_requirements
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        update)
            check_requirements
            update_images
            ;;
        test)
            test_endpoints
            ;;
        clean)
            clean_environment
            ;;
        monitor)
            monitor_services
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
