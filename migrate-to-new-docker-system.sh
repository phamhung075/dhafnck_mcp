#!/bin/bash
# migrate-to-new-docker-system.sh - Migrate from old Docker system to new PostgreSQL-first system

set -euo pipefail

echo "🔄 DhafnckMCP Docker System Migration"
echo "===================================="
echo ""
echo "This script will migrate your existing Docker setup to the new PostgreSQL-first system."
echo ""

# Check if old system exists
if [[ ! -f "run_docker.sh" ]]; then
    echo "⚠️  Old system (run_docker.sh) not found. Nothing to migrate."
    echo "   You can start using the new system directly:"
    echo "   cd docker-system && ./docker-cli.sh workflow dev-setup"
    exit 0
fi

# Confirmation
read -p "This will replace the old Docker system. Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled."
    exit 0
fi

# 1. Create backup directory
echo ""
echo "1️⃣ Creating backup directory..."
BACKUP_DIR="migration-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 2. Backup existing data
echo "2️⃣ Backing up existing data..."

# Check if SQLite database exists
if [[ -f "dhafnck_mcp_main/data/dhafnck_mcp.db" ]]; then
    echo "  → Backing up SQLite database..."
    cp "dhafnck_mcp_main/data/dhafnck_mcp.db" "$BACKUP_DIR/sqlite-backup.db"
    echo "    ✅ SQLite database backed up"
fi

# Backup existing Docker volumes
echo "  → Checking for existing Docker volumes..."
for volume in $(docker volume ls -q | grep -E "dhafnck|mcp" || true); do
    echo "    → Backing up volume: $volume"
    docker run --rm \
        -v "$volume:/source:ro" \
        -v "$(pwd)/$BACKUP_DIR:/backup" \
        alpine tar czf "/backup/${volume}-backup.tar.gz" -C /source . || true
done

# Backup configurations
echo "  → Backing up configurations..."
cp -r .env* "$BACKUP_DIR/" 2>/dev/null || true
cp -r dhafnck_mcp_main/docker/*.yml "$BACKUP_DIR/" 2>/dev/null || true

# 3. Stop old system
echo ""
echo "3️⃣ Stopping old Docker containers..."
# Try different methods to stop containers
docker compose down 2>/dev/null || true
docker-compose down 2>/dev/null || true
./run_docker.sh stop 2>/dev/null || true

# Stop any remaining dhafnck containers
docker ps -a --format '{{.Names}}' | grep -E "dhafnck|mcp" | xargs -r docker stop
docker ps -a --format '{{.Names}}' | grep -E "dhafnck|mcp" | xargs -r docker rm

# 4. Archive old system
echo ""
echo "4️⃣ Archiving old system..."
mkdir -p "archive/old-docker-system"
mv run_docker.sh "archive/old-docker-system/" 2>/dev/null || true
mv dhafnck_mcp_main/docker/mcp-docker.py "archive/old-docker-system/" 2>/dev/null || true
echo "   ✅ Old system archived to archive/old-docker-system/"

# 5. Setup new system
echo ""
echo "5️⃣ Setting up new Docker CLI system..."

# Make new CLI executable
chmod +x docker-system/docker-cli.sh

# Create symbolic link for easy access
ln -sf docker-system/docker-cli.sh docker-cli.sh 2>/dev/null || true

# 6. Prepare environment
echo ""
echo "6️⃣ Preparing environment..."

# Copy dev environment if no .env exists
if [[ ! -f ".env" ]]; then
    cp docker-system/environments/dev.env .env
    echo "   ✅ Created .env from development template"
fi

# Update database configuration to PostgreSQL
if grep -q "DATABASE_TYPE=sqlite" .env 2>/dev/null; then
    sed -i.bak 's/DATABASE_TYPE=sqlite/DATABASE_TYPE=postgresql/g' .env
    echo "   ✅ Updated DATABASE_TYPE to postgresql"
fi

# 7. Convert SQLite to PostgreSQL (if needed)
if [[ -f "$BACKUP_DIR/sqlite-backup.db" ]]; then
    echo ""
    echo "7️⃣ SQLite database detected. Conversion to PostgreSQL required."
    echo "   Note: Automatic conversion requires additional tools."
    echo ""
    echo "   Options:"
    echo "   1. Manual migration using pgloader"
    echo "   2. Fresh start with PostgreSQL (recommended for development)"
    echo ""
    read -p "Start fresh with PostgreSQL? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        FRESH_START=true
    else
        echo "   ⚠️  Manual migration required. See documentation for pgloader usage."
        FRESH_START=false
    fi
else
    FRESH_START=true
fi

# 8. Initialize new system
echo ""
echo "8️⃣ Initializing new Docker system..."

cd docker-system

if [[ "$FRESH_START" == "true" ]]; then
    ./docker-cli.sh workflow dev-setup
else
    ./docker-cli.sh start
    ./docker-cli.sh db init
fi

cd ..

# 9. Show summary
echo ""
echo "✅ Migration complete!"
echo ""
echo "📋 Summary:"
echo "  - Old system backed up to: $BACKUP_DIR/"
echo "  - Old scripts archived to: archive/old-docker-system/"
echo "  - New CLI available at: ./docker-cli.sh"
echo ""
echo "🚀 Quick Start Guide:"
echo "  ./docker-cli.sh start        # Start all services"
echo "  ./docker-cli.sh status       # Check status"
echo "  ./docker-cli.sh help         # Show all commands"
echo "  ./docker-cli.sh monitor      # Real-time monitoring"
echo ""
echo "📚 Documentation: docker-system/README.md"
echo ""

if [[ "$FRESH_START" != "true" ]] && [[ -f "$BACKUP_DIR/sqlite-backup.db" ]]; then
    echo "⚠️  Note: SQLite data was not migrated automatically."
    echo "   To migrate data, use pgloader or similar tools."
    echo "   SQLite backup: $BACKUP_DIR/sqlite-backup.db"
    echo ""
fi

echo "Happy coding with the new PostgreSQL-first Docker system! 🎉"