#!/bin/bash
# core.sh - Core Docker operations

source "${SCRIPT_DIR}/lib/common.sh"
source "${SCRIPT_DIR}/lib/database/interface.sh"

# Start services
start_command() {
    info "Starting DhafnckMCP services..."
    
    check_docker
    check_docker_compose
    
    # Ensure network exists
    ensure_network "dhafnck-network"
    
    # Load environment
    load_environment
    
    # Start services
    local compose_args=$(compose_file_args)
    cd "$SCRIPT_DIR"
    
    if is_development; then
        info "Starting in development mode with hot reload..."
        docker compose $compose_args up -d --build
    else
        docker compose $compose_args up -d
    fi
    
    # Wait for services to be ready
    wait_for_services
    
    # Initialize database if needed
    if ! db_operation test_connection &>/dev/null; then
        info "Initializing database..."
        db_operation init
        db_operation migrate
    fi
    
    success "All services started successfully"
    
    # Show status
    status_command
}

# Stop services
stop_command() {
    info "Stopping DhafnckMCP services..."
    
    check_docker
    check_docker_compose
    
    local compose_args=$(compose_file_args)
    cd "$SCRIPT_DIR"
    
    docker compose $compose_args down
    
    success "All services stopped"
}

# Restart services
restart_command() {
    info "Restarting DhafnckMCP services..."
    
    stop_command
    sleep 2
    start_command
}

# Show status
status_command() {
    info "DhafnckMCP Service Status"
    echo "========================="
    
    check_docker
    check_docker_compose
    
    # Load environment
    load_environment
    
    local compose_args=$(compose_file_args)
    cd "$SCRIPT_DIR"
    
    # Show service status
    docker compose $compose_args ps
    
    echo ""
    
    # Show resource usage
    info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        $(docker compose $compose_args ps -q 2>/dev/null) 2>/dev/null || true
}

# View logs
logs_command() {
    local service="${1:-}"
    local tail="${2:-100}"
    
    check_docker
    check_docker_compose
    
    local compose_args=$(compose_file_args)
    cd "$SCRIPT_DIR"
    
    if [[ -n "$service" ]]; then
        validate_service_name "$service" || return 1
        docker compose $compose_args logs -f --tail="$tail" "$service"
    else
        docker compose $compose_args logs -f --tail="$tail"
    fi
}

# Access shell
shell_command() {
    local service="${1:-backend}"
    
    check_docker
    check_docker_compose
    
    validate_service_name "$service" || return 1
    
    local container_id=$(get_container_id "$service")
    if [[ -z "$container_id" ]]; then
        error "Container for service '$service' not found"
        return 1
    fi
    
    info "Accessing shell for $service..."
    
    # Determine shell based on service
    local shell="/bin/bash"
    case "$service" in
        postgres)
            shell="/bin/sh"
            ;;
        redis)
            shell="/bin/sh"
            ;;
        frontend|nginx)
            shell="/bin/sh"
            ;;
    esac
    
    docker exec -it "$container_id" "$shell" || docker exec -it "$container_id" /bin/sh
}