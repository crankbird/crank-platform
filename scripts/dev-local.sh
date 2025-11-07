#!/bin/bash

# 🍎 Crank Platform Local Development Manager
# 
# This script helps manage local development on Docker Desktop for macOS
# including pulling images from Azure Container Registry and managing services

set -e

# Color output
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

# Functions
show_help() {
    echo_purple "🍎 Crank Platform Local Development Manager"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Initial setup for local development"
    echo "  start     - Start all services"
    echo "  start-min - Start minimal services (no image classifier)"
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
    echo_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo_error "Docker is not installed. Please install Docker Desktop for macOS."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo_error "Docker Compose is not available. Please update Docker Desktop."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    echo_success "All requirements satisfied"
}

setup_local_env() {
    echo_info "Setting up local development environment..."
    
    # Copy local environment file
    if [ ! -f "$ENV_FILE" ]; then
        cp .env.local .env
        echo_success "Created .env file from .env.local"
    else
        echo_warning ".env file already exists, keeping current configuration"
    fi
    
    # Login to Azure Container Registry
    echo_info "Logging into Azure Container Registry..."
    if az account show &> /dev/null; then
        az acr login --name crankplatformregistry || echo_warning "ACR login failed, you may need to manually docker login"
    else
        echo_warning "Azure CLI not configured. You may need to manually login to ACR:"
        echo "  docker login $REGISTRY"
    fi
    
    echo_success "Local environment setup complete"
}

start_services() {
    local profile=""
    if [ "$1" = "minimal" ]; then
        profile="--profile minimal"
        echo_info "Starting minimal services (excluding image classifier)..."
    else
        echo_info "Starting all services..."
    fi
    
    docker-compose -f "$COMPOSE_FILE" $profile up -d
    
    if [ $? -eq 0 ]; then
        echo_success "Services started successfully!"
        echo_info "Platform will be available at: https://localhost:8443"
        echo_info "Run '$0 status' to check service health"
    else
        echo_error "Failed to start services"
        exit 1
    fi
}

stop_services() {
    echo_info "Stopping all services..."
    docker-compose -f "$COMPOSE_FILE" down
    echo_success "All services stopped"
}

restart_services() {
    echo_info "Restarting services..."
    stop_services
    sleep 2
    start_services
}

show_logs() {
    echo_info "Showing logs for all services (Ctrl+C to exit)..."
    docker-compose -f "$COMPOSE_FILE" logs -f
}

show_status() {
    echo_info "Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
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
        if curl -k -s "https://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo_success "$name is healthy"
        else
            echo_warning "$name is not responding"
        fi
    done
}

update_images() {
    echo_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
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
        
        if curl -k -s -w "Status: %{http_code}\n" "$url" | grep -q "200\|healthy"; then
            echo_success "$name is working correctly"
        else
            echo_error "$name failed health check"
        fi
    done
    
    # Test worker registration
    echo_info "Testing worker registration..."
    if curl -k -s -H "Authorization: Bearer local-dev-key-secure" \
            "https://localhost:8443/v1/workers" | grep -q "workers"; then
        echo_success "Worker registration is working"
    else
        echo_warning "Worker registration may not be ready yet"
    fi
}

clean_environment() {
    echo_warning "This will remove all containers, volumes, and images. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo_info "Cleaning up environment..."
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
        docker system prune -f
        echo_success "Environment cleaned"
    else
        echo_info "Clean cancelled"
    fi
}

monitor_services() {
    echo_info "Monitoring services (Ctrl+C to exit)..."
    watch -n 2 "docker-compose -f $COMPOSE_FILE ps && echo '' && docker stats --no-stream"
}

# Main script logic
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