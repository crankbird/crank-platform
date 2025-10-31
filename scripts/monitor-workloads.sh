#!/bin/bash
# Monitor container workloads across platforms from WSL control plane

set -euo pipefail

PLATFORM="all"
WATCH_MODE=false
REFRESH_INTERVAL=5

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --interval)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

show_platform_status() {
    local platform=$1
    
    echo "════════════════════════════════════════"
    echo "📊 $platform Platform Status"
    echo "════════════════════════════════════════"
    
    case $platform in
        "windows")
            if docker -H "npipe:////./pipe/docker_engine" version >/dev/null 2>&1; then
                echo "✅ Windows Docker Desktop: Connected"
                DOCKER_HOST="npipe:////./pipe/docker_engine" docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            else
                echo "❌ Windows Docker Desktop: Disconnected"
            fi
            ;;
        "mac")
            # This would need SSH configuration to your Mac
            echo "🍎 Mac Docker Desktop: Configure SSH access"
            ;;
        "local")
            echo "✅ Local WSL Docker: Connected"
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            ;;
    esac
    echo ""
}

show_resource_usage() {
    echo "🔧 Resource Usage:"
    echo "CPU: $(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5)} END {print usage "%"}')"
    echo "Memory: $(free | grep Mem | awk '{printf "%.1f%%\n", $3/$2 * 100.0}')"
    echo "Disk: $(df -h / | awk 'NR==2{printf "%s\n", $5}')"
    echo ""
}

if [[ "$WATCH_MODE" == "true" ]]; then
    echo "👀 Watching workloads (Ctrl+C to exit)..."
    while true; do
        clear
        echo "🕐 $(date)"
        echo ""
        
        if [[ "$PLATFORM" == "all" ]]; then
            show_platform_status "local"
            show_platform_status "windows"
            show_resource_usage
        else
            show_platform_status "$PLATFORM"
            show_resource_usage
        fi
        
        sleep "$REFRESH_INTERVAL"
    done
else
    if [[ "$PLATFORM" == "all" ]]; then
        show_platform_status "local"
        show_platform_status "windows"
        show_resource_usage
    else
        show_platform_status "$PLATFORM"
        show_resource_usage
    fi
fi