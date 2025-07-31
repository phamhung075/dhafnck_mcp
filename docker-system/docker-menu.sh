#!/bin/bash
# docker-menu.sh - Interactive menu interface for Docker CLI

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common functions
source "${SCRIPT_DIR}/lib/common.sh"

# ANSI color codes for better UI
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly UNDERLINE='\033[4m'
readonly RESET='\033[0m'

# Clear screen and show header
show_header() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════╗"
    echo "║        DhafnckMCP Docker Management            ║"
    echo "║           PostgreSQL Edition v2.0              ║"
    echo "╚════════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

# Show main menu
show_main_menu() {
    echo -e "${MAGENTA}${BOLD}Main Menu${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) 🚀 Quick Actions"
    echo "  2) 🗄️  Database Operations"
    echo "  3) 🔧 Development Tools"
    echo "  4) 📦 Deployment & Scaling"
    echo "  5) 💾 Backup & Maintenance"
    echo "  6) ⚙️  Configuration"
    echo "  7) 🔍 Troubleshooting"
    echo "  8) 📊 Monitoring Dashboard"
    echo "  9) 📚 Help & Documentation"
    echo "  0) 🚪 Exit"
    echo "────────────────────────────────────────────────"
}

# Quick Actions Menu
quick_actions_menu() {
    show_header
    echo -e "${MAGENTA}${BOLD}Quick Actions${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) ▶️  Start all services"
    echo "  2) ⏹️  Stop all services"
    echo "  3) 🔄 Restart all services"
    echo "  4) 📊 Show status"
    echo "  5) 📜 View logs (all services)"
    echo "  6) 🚀 Run dev setup workflow"
    echo "  7) 🔥 Start with hot reload"
    echo "  0) ↩️  Back to main menu"
    echo "────────────────────────────────────────────────"
    
    read -p "Select option: " choice
    
    case $choice in
        1) ./docker-cli.sh start ;;
        2) ./docker-cli.sh stop ;;
        3) ./docker-cli.sh restart ;;
        4) ./docker-cli.sh status && read -p "Press Enter to continue..." ;;
        5) ./docker-cli.sh logs ;;
        6) ./docker-cli.sh workflow dev-setup ;;
        7) 
            echo "Starting with hot reload enabled..."
            ./docker-cli.sh start
            echo -e "\n${GREEN}✅ Services started with hot reload${RESET}"
            echo "Backend: http://localhost:8000"
            echo "Frontend: http://localhost:3000"
            read -p "Press Enter to continue..."
            ;;
        0) return ;;
        *) echo "Invalid option" && sleep 1 ;;
    esac
}

# Database Operations Menu
database_menu() {
    show_header
    echo -e "${MAGENTA}${BOLD}Database Operations${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) 📊 Database status"
    echo "  2) 🔧 Initialize database"
    echo "  3) 📈 Run migrations"
    echo "  4) 💾 Backup database"
    echo "  5) 📥 Restore database"
    echo "  6) 🖥️  Database shell (psql)"
    echo "  7) 🌱 Seed development data"
    echo "  8) ⚠️  Reset database (WARNING)"
    echo "  0) ↩️  Back to main menu"
    echo "────────────────────────────────────────────────"
    
    read -p "Select option: " choice
    
    case $choice in
        1) ./docker-cli.sh db status && read -p "Press Enter to continue..." ;;
        2) ./docker-cli.sh db init && read -p "Press Enter to continue..." ;;
        3) ./docker-cli.sh db migrate && read -p "Press Enter to continue..." ;;
        4) ./docker-cli.sh db backup && read -p "Press Enter to continue..." ;;
        5) 
            ./docker-cli.sh backup list
            read -p "Enter backup file name (or press Enter to cancel): " backup_file
            if [[ -n "$backup_file" ]]; then
                ./docker-cli.sh db restore "$backup_file"
            fi
            ;;
        6) ./docker-cli.sh db shell ;;
        7) ./docker-cli.sh dev seed && read -p "Press Enter to continue..." ;;
        8) 
            echo -e "${RED}${BOLD}⚠️  WARNING: This will DELETE ALL DATA!${RESET}"
            read -p "Type 'DELETE' to confirm: " confirm
            if [[ "$confirm" == "DELETE" ]]; then
                ./docker-cli.sh db reset
            fi
            ;;
        0) return ;;
        *) echo "Invalid option" && sleep 1 ;;
    esac
}

# Development Tools Menu
development_menu() {
    show_header
    echo -e "${MAGENTA}${BOLD}Development Tools${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) 🔧 Setup development environment"
    echo "  2) 🔄 Reset development data"
    echo "  3) 🌱 Seed sample data"
    echo "  4) 🏗️  Build images"
    echo "  5) 🧪 Run tests"
    echo "  6) 🖥️  Shell access (select service)"
    echo "  7) 📜 View logs (select service)"
    echo "  0) ↩️  Back to main menu"
    echo "────────────────────────────────────────────────"
    
    read -p "Select option: " choice
    
    case $choice in
        1) ./docker-cli.sh dev setup ;;
        2) ./docker-cli.sh dev reset ;;
        3) ./docker-cli.sh dev seed && read -p "Press Enter to continue..." ;;
        4) 
            echo "Select service to build:"
            echo "1) Backend"
            echo "2) Frontend"
            echo "3) All"
            read -p "Choice: " build_choice
            case $build_choice in
                1) ./docker-cli.sh build backend ;;
                2) ./docker-cli.sh build frontend ;;
                3) ./docker-cli.sh build all ;;
            esac
            ;;
        5) 
            echo "Select test type:"
            echo "1) Unit tests"
            echo "2) Integration tests"
            echo "3) E2E tests"
            echo "4) All tests"
            read -p "Choice: " test_choice
            case $test_choice in
                1) ./docker-cli.sh test unit ;;
                2) ./docker-cli.sh test integration ;;
                3) ./docker-cli.sh test e2e ;;
                4) ./docker-cli.sh test all ;;
            esac
            ;;
        6) 
            echo "Select service:"
            echo "1) Backend"
            echo "2) Frontend"
            echo "3) PostgreSQL"
            echo "4) Redis"
            read -p "Choice: " shell_choice
            case $shell_choice in
                1) ./docker-cli.sh shell backend ;;
                2) ./docker-cli.sh shell frontend ;;
                3) ./docker-cli.sh shell postgres ;;
                4) ./docker-cli.sh shell redis ;;
            esac
            ;;
        7) 
            echo "Select service:"
            echo "1) Backend"
            echo "2) Frontend"
            echo "3) PostgreSQL"
            echo "4) Redis"
            echo "5) All services"
            read -p "Choice: " log_choice
            case $log_choice in
                1) ./docker-cli.sh logs backend ;;
                2) ./docker-cli.sh logs frontend ;;
                3) ./docker-cli.sh logs postgres ;;
                4) ./docker-cli.sh logs redis ;;
                5) ./docker-cli.sh logs ;;
            esac
            ;;
        0) return ;;
        *) echo "Invalid option" && sleep 1 ;;
    esac
}

# Deployment & Scaling Menu
deployment_menu() {
    show_header
    echo -e "${MAGENTA}${BOLD}Deployment & Scaling${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) 🚀 Deploy to environment"
    echo "  2) 📈 Scale service"
    echo "  3) 🏥 Health check"
    echo "  4) 📊 Monitoring dashboard"
    echo "  5) 📋 Workflow: Production deploy"
    echo "  0) ↩️  Back to main menu"
    echo "────────────────────────────────────────────────"
    
    read -p "Select option: " choice
    
    case $choice in
        1) 
            echo "Select environment:"
            echo "1) Staging"
            echo "2) Production"
            read -p "Choice: " env_choice
            case $env_choice in
                1) ./docker-cli.sh deploy staging ;;
                2) ./docker-cli.sh deploy production ;;
            esac
            ;;
        2) 
            read -p "Service to scale (backend/frontend): " service
            read -p "Number of replicas: " replicas
            ./docker-cli.sh scale "$service" "$replicas"
            ;;
        3) ./docker-cli.sh health && read -p "Press Enter to continue..." ;;
        4) ./docker-cli.sh monitor ;;
        5) ./docker-cli.sh workflow prod-deploy ;;
        0) return ;;
        *) echo "Invalid option" && sleep 1 ;;
    esac
}

# Backup & Maintenance Menu
maintenance_menu() {
    show_header
    echo -e "${MAGENTA}${BOLD}Backup & Maintenance${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) 💾 Create backup"
    echo "  2) 📥 Restore backup"
    echo "  3) 📋 List backups"
    echo "  4) 🧹 Cleanup unused resources"
    echo "  5) 🔄 Update system"
    echo "  6) 📦 Emergency backup"
    echo "  0) ↩️  Back to main menu"
    echo "────────────────────────────────────────────────"
    
    read -p "Select option: " choice
    
    case $choice in
        1) 
            echo "Select backup type:"
            echo "1) Full backup"
            echo "2) Database only"
            echo "3) Volumes only"
            echo "4) Configs only"
            read -p "Choice: " backup_choice
            case $backup_choice in
                1) ./docker-cli.sh backup create full ;;
                2) ./docker-cli.sh backup create database ;;
                3) ./docker-cli.sh backup create volumes ;;
                4) ./docker-cli.sh backup create configs ;;
            esac
            read -p "Press Enter to continue..."
            ;;
        2) 
            ./docker-cli.sh backup list
            read -p "Enter backup file name: " backup_file
            if [[ -n "$backup_file" ]]; then
                ./docker-cli.sh backup restore "$backup_file"
            fi
            ;;
        3) ./docker-cli.sh backup list && read -p "Press Enter to continue..." ;;
        4) ./docker-cli.sh cleanup && read -p "Press Enter to continue..." ;;
        5) ./docker-cli.sh update && read -p "Press Enter to continue..." ;;
        6) ./docker-cli.sh emergency-backup && read -p "Press Enter to continue..." ;;
        0) return ;;
        *) echo "Invalid option" && sleep 1 ;;
    esac
}

# Configuration Menu
configuration_menu() {
    show_header
    echo -e "${MAGENTA}${BOLD}Configuration${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) 📋 Show configuration"
    echo "  2) ✏️  Set configuration value"
    echo "  3) ✅ Validate configuration"
    echo "  4) 🔄 Switch environment"
    echo "  5) 🔧 Fix permissions"
    echo "  0) ↩️  Back to main menu"
    echo "────────────────────────────────────────────────"
    
    read -p "Select option: " choice
    
    case $choice in
        1) ./docker-cli.sh config show && read -p "Press Enter to continue..." ;;
        2) 
            read -p "Enter key: " key
            read -p "Enter value: " value
            ./docker-cli.sh config set "$key" "$value"
            read -p "Press Enter to continue..."
            ;;
        3) ./docker-cli.sh config validate && read -p "Press Enter to continue..." ;;
        4) 
            echo "Select environment:"
            echo "1) Development"
            echo "2) Staging"
            echo "3) Production"
            read -p "Choice: " env_choice
            case $env_choice in
                1) ./docker-cli.sh env dev ;;
                2) ./docker-cli.sh env staging ;;
                3) ./docker-cli.sh env production ;;
            esac
            read -p "Press Enter to continue..."
            ;;
        5) ./docker-cli.sh fix-permissions && read -p "Press Enter to continue..." ;;
        0) return ;;
        *) echo "Invalid option" && sleep 1 ;;
    esac
}

# Troubleshooting Menu
troubleshooting_menu() {
    show_header
    echo -e "${MAGENTA}${BOLD}Troubleshooting${RESET}"
    echo "────────────────────────────────────────────────"
    echo "  1) 🔍 Run diagnostics"
    echo "  2) 🔧 Fix permissions"
    echo "  3) 💾 Create emergency backup"
    echo "  4) 📦 Generate support bundle"
    echo "  5) 🏥 Comprehensive health check"
    echo "  0) ↩️  Back to main menu"
    echo "────────────────────────────────────────────────"
    
    read -p "Select option: " choice
    
    case $choice in
        1) ./docker-cli.sh diagnose && read -p "Press Enter to continue..." ;;
        2) ./docker-cli.sh fix-permissions && read -p "Press Enter to continue..." ;;
        3) ./docker-cli.sh emergency-backup && read -p "Press Enter to continue..." ;;
        4) ./docker-cli.sh support-bundle && read -p "Press Enter to continue..." ;;
        5) ./docker-cli.sh workflow health-check && read -p "Press Enter to continue..." ;;
        0) return ;;
        *) echo "Invalid option" && sleep 1 ;;
    esac
}

# Main loop
main() {
    while true; do
        show_header
        show_main_menu
        
        read -p "Select option: " choice
        
        case $choice in
            1) quick_actions_menu ;;
            2) database_menu ;;
            3) development_menu ;;
            4) deployment_menu ;;
            5) maintenance_menu ;;
            6) configuration_menu ;;
            7) troubleshooting_menu ;;
            8) ./docker-cli.sh monitor ;;
            9) 
                show_header
                echo -e "${CYAN}📚 Help & Documentation${RESET}"
                echo ""
                ./docker-cli.sh help
                read -p "Press Enter to continue..."
                ;;
            0) 
                echo -e "\n${GREEN}👋 Goodbye!${RESET}\n"
                exit 0
                ;;
            *) 
                echo -e "${RED}Invalid option!${RESET}"
                sleep 1
                ;;
        esac
    done
}

# Run main function
main