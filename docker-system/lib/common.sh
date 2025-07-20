#!/bin/bash
# common.sh - Common functions and utilities

# Guard against multiple inclusion
if [[ -n "${_COMMON_SH_LOADED:-}" ]]; then
    return 0
fi
_COMMON_SH_LOADED=1

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info() {
    echo -e "${BLUE}ℹ️  ${NC}$*"
}

success() {
    echo -e "${GREEN}✅ ${NC}$*"
}

warning() {
    echo -e "${YELLOW}⚠️  ${NC}$*"
}

error() {
    echo -e "${RED}❌ ${NC}$*" >&2
}

# Utility functions
confirm() {
    local prompt="${1:-Continue?}"
    read -p "$prompt [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
}

check_docker_compose() {
    if ! command -v docker compose &> /dev/null; then
        if command -v docker-compose &> /dev/null; then
            # Use docker-compose as fallback
            alias docker compose='docker-compose'
        else
            error "Docker Compose is not installed"
            exit 1
        fi
    fi
}

wait_for_service() {
    local service="$1"
    local max_attempts="${2:-30}"
    local attempt=0
    
    info "Waiting for $service to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if docker compose ps --format json | jq -r '.[] | select(.Service == "'$service'") | .Health' | grep -q "healthy"; then
            success "$service is ready"
            return 0
        fi
        
        sleep 2
        ((attempt++))
    done
    
    error "$service failed to become ready within $(($max_attempts * 2)) seconds"
    return 1
}

wait_for_services() {
    local services=("backend" "frontend" "postgres" "redis")
    
    for service in "${services[@]}"; do
        if docker compose ps --format json | jq -r '.[].Service' | grep -q "^$service$"; then
            wait_for_service "$service" || return 1
        fi
    done
}

get_container_id() {
    local service="$1"
    # Try with docker ps first (more reliable)
    docker ps -q --filter "name=dhafnck-$service" 2>/dev/null | head -1
}

get_version() {
    if [[ -f "${PROJECT_ROOT}/VERSION" ]]; then
        cat "${PROJECT_ROOT}/VERSION"
    else
        echo "dev"
    fi
}

# Environment helpers
is_production() {
    [[ "${ENV:-}" == "production" ]]
}

is_development() {
    [[ "${ENV:-dev}" == "dev" ]]
}

# Network helpers
ensure_network() {
    local network_name="${1:-dhafnck-network}"
    
    if ! docker network ls --format '{{.Name}}' | grep -q "^${network_name}$"; then
        info "Creating network: $network_name"
        docker network create "$network_name" --driver bridge
    fi
}

# Volume helpers
ensure_volume() {
    local volume_name="$1"
    
    if ! docker volume ls --format '{{.Name}}' | grep -q "^${volume_name}$"; then
        info "Creating volume: $volume_name"
        docker volume create "$volume_name"
    fi
}

# Compose helpers
compose_file_args() {
    # Use the new docker-system compose files
    local args="-f ${SCRIPT_DIR}/docker/docker-compose.yml"
    
    # Add environment-specific overrides
    if [[ -f "${SCRIPT_DIR}/docker/docker-compose.${ENV:-dev}.yml" ]]; then
        args="$args -f ${SCRIPT_DIR}/docker/docker-compose.${ENV:-dev}.yml"
    fi
    
    echo "$args"
}

# Validation helpers
validate_service_name() {
    local service="$1"
    local valid_services=("backend" "frontend" "postgres" "redis" "nginx")
    
    for valid in "${valid_services[@]}"; do
        if [[ "$service" == "$valid" ]]; then
            return 0
        fi
    done
    
    error "Invalid service name: $service"
    error "Valid services: ${valid_services[*]}"
    return 1
}

# Performance monitoring
measure_time() {
    local start=$(date +%s)
    "$@"
    local exit_code=$?
    local end=$(date +%s)
    local duration=$((end - start))
    
    if [[ $duration -gt 0 ]]; then
        info "Execution time: ${duration}s"
    fi
    
    return $exit_code
}

# Export all functions
export -f info success warning error confirm
export -f check_docker check_docker_compose
export -f wait_for_service wait_for_services
export -f get_container_id get_version
export -f is_production is_development
export -f ensure_network ensure_volume
export -f compose_file_args validate_service_name
export -f measure_time