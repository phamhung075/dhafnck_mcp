#!/bin/bash
# development.sh - Development commands

# Ensure SCRIPT_DIR is set
[[ -z "$SCRIPT_DIR" ]] && SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

source "${SCRIPT_DIR}/lib/common.sh"
source "${SCRIPT_DIR}/lib/database/interface.sh"
source "${SCRIPT_DIR}/lib/core.sh"

# Development command dispatcher
dev_command() {
    local subcommand="$1"
    shift
    
    case "$subcommand" in
        setup)
            dev_setup "$@"
            ;;
        reset)
            dev_reset "$@"
            ;;
        seed)
            dev_seed "$@"
            ;;
        *)
            error "Unknown dev command: $subcommand"
            echo "Valid commands: setup, reset, seed"
            return 1
            ;;
    esac
}

# Setup development environment
dev_setup() {
    info "Setting up development environment..."
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Create necessary directories
    mkdir -p "${PROJECT_ROOT}/dhafnck_mcp_main/data"
    mkdir -p "${PROJECT_ROOT}/backups"
    mkdir -p "${PROJECT_ROOT}/logs"
    
    # Copy dev environment if not exists
    if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
        cp "${ENV_DIR}/dev.env" "${PROJECT_ROOT}/.env"
        info "Created .env file from dev template"
    fi
    
    # Load development environment
    load_environment "dev"
    
    # Ensure network
    ensure_network "dhafnck-network"
    
    # Start services
    start_command
    
    # Seed data if enabled
    if [[ "${SEED_DATA:-true}" == "true" ]]; then
        dev_seed
    fi
    
    success "Development environment setup complete!"
    echo ""
    echo "🚀 Quick start:"
    echo "  Backend API: http://localhost:8000"
    echo "  Frontend:    http://localhost:3000"
    echo "  Database:    postgresql://dhafnck_user:dev_password@localhost:5432/dhafnck_mcp"
    echo ""
    echo "📝 Useful commands:"
    echo "  ./docker-cli.sh logs backend     # View backend logs"
    echo "  ./docker-cli.sh shell backend    # Access backend shell"
    echo "  ./docker-cli.sh db shell         # Access database shell"
}

# Reset development data
dev_reset() {
    warning "This will reset all development data!"
    
    if ! confirm "Continue?"; then
        info "Operation cancelled"
        return 0
    fi
    
    info "Resetting development environment..."
    
    # Stop services
    stop_command
    
    # Remove volumes
    info "Removing development volumes..."
    docker volume rm dhafnck-postgres-data 2>/dev/null || true
    docker volume rm dhafnck-redis-data 2>/dev/null || true
    
    # Start services
    start_command
    
    # Reset database
    db_operation reset
    
    # Seed data
    dev_seed
    
    success "Development environment reset complete"
}

# Seed development data
dev_seed() {
    info "Seeding development data..."
    
    local backend_container=$(get_container_id "backend")
    if [[ -z "$backend_container" ]]; then
        error "Backend container not found"
        return 1
    fi
    
    # Run seed script
    docker exec "$backend_container" python scripts/seed_data.py || {
        warning "Seed script not found or failed"
        # Create basic seed data manually if script doesn't exist
        cat <<'EOF' | docker exec -i "$backend_container" python
import os
import sys
sys.path.append('/app')

from fastmcp.task_management.infrastructure.config.database import get_db
from fastmcp.task_management.domain.entities import Project, GitBranch, Task

try:
    db = next(get_db())
    
    # Create sample project
    project = Project(
        name="Sample Project",
        description="A sample project for development"
    )
    db.add(project)
    db.commit()
    
    # Create sample branch
    branch = GitBranch(
        project_id=project.id,
        git_branch_name="main",
        git_branch_description="Main development branch"
    )
    db.add(branch)
    db.commit()
    
    # Create sample tasks
    tasks = [
        Task(
            git_branch_id=branch.id,
            title="Setup development environment",
            description="Configure local development setup",
            status="done"
        ),
        Task(
            git_branch_id=branch.id,
            title="Implement user authentication",
            description="Add JWT-based authentication",
            status="in_progress"
        ),
        Task(
            git_branch_id=branch.id,
            title="Add unit tests",
            description="Write comprehensive test suite",
            status="todo"
        )
    ]
    
    for task in tasks:
        db.add(task)
    
    db.commit()
    print("✅ Development data seeded successfully")
    
except Exception as e:
    print(f"❌ Error seeding data: {e}")
    sys.exit(1)
EOF
    }
    
    success "Development data seeded"
}

# Build command
build_command() {
    local service="${1:-all}"
    
    info "Building Docker images..."
    
    check_docker
    check_docker_compose
    
    local compose_args=$(compose_file_args)
    cd "$SCRIPT_DIR"
    
    if [[ "$service" == "all" ]]; then
        docker compose $compose_args build --parallel
    else
        validate_service_name "$service" || return 1
        docker compose $compose_args build "$service"
    fi
    
    success "Build completed"
}

# Test command
test_command() {
    local test_type="${1:-all}"
    
    source "${SCRIPT_DIR}/test/test-runner.sh"
    run_tests "$test_type"
}