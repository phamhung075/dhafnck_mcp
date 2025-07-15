#!/usr/bin/env python3
import subprocess
import questionary
import datetime
import os
import signal
import sys

def get_compose_files(mode):
    """Get the appropriate compose files for each mode
    Returns a list of compose file arguments for Docker Compose.
    The order of files matters due to configuration overrides:
    - Base configuration is always included first (docker-compose.yml)
    - Mode-specific configurations are layered on top, overriding base settings if needed
    This ensures that mode-specific settings (like environment variables, volumes, or commands)
    take precedence over the base configuration.
    """
    base_files = ["-f", "dhafnck_mcp_main/docker/docker-compose.yml"]
    
    if mode == "normal":
        # Normal mode uses only the base configuration
        # No additional overrides; runs in production-like setup
        return base_files
    elif mode == "development":
        # Development mode builds on base configuration
        # Adds debug settings and possibly hot reload via volume mounts
        # Should run after base config is understood, as it overrides for dev environment
        return base_files + ["-f", "dhafnck_mcp_main/docker/docker-compose.dev.yml"]
    elif mode == "dev-fast":
        # Dev-fast mode is a variant of development, optimized for speed
        # Overrides base config with settings for quick iteration and debugging
        # Run after base config; assumes base services are defined
        return base_files + ["-f", "dhafnck_mcp_main/docker/docker-compose.dev-fast.yml"]
    elif mode == "local":
        # Local mode builds on base config but disables auth for ease of development
        # Intended for local testing without security overhead
        # Run after base config to ensure proper override of auth settings
        return base_files + ["-f", "dhafnck_mcp_main/docker/docker-compose.local.yml"]
    elif mode == "redis":
        # Redis mode extends base config with session persistence via Redis
        # Requires Redis service to be defined and started alongside main app
        # Run after base config; depends on main app setup before adding persistence layer
        return base_files + ["-f", "dhafnck_mcp_main/docker/docker-compose.redis.yml"]
    else:
        # Fallback to base config if mode is unrecognized
        return base_files

def fix_database_permissions():
    """Fix database file permissions in the Docker container.
    
    This addresses the issue where database backups/restores change file ownership
    from the container user (dhafnck) to the host user (UID 1000), causing 
    'readonly database' errors when the container tries to write to the database.
    """
    print("🔧 Fixing database permissions...")
    try:
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=dhafnck-mcp-server", "--format", "{{.Names}}"], 
            capture_output=True, text=True, check=True
        )
        
        if "dhafnck-mcp-server" in result.stdout:
            # Fix database file ownership and permissions
            subprocess.run([
                "docker", "exec", "--user", "root", "dhafnck-mcp-server", 
                "chown", "dhafnck:dhafnck", "/data/dhafnck_mcp.db"
            ], check=True)
            
            subprocess.run([
                "docker", "exec", "--user", "root", "dhafnck-mcp-server", 
                "chmod", "664", "/data/dhafnck_mcp.db"
            ], check=True)
            
            print("✅ Database permissions fixed successfully!")
        else:
            print("⚠️ Container 'dhafnck-mcp-server' not found or not running.")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fixing database permissions: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def rebuild_frontend_after_restore():
    """Rebuild frontend container after database restore to ensure UI shows new data.
    
    This ensures that the frontend displays the restored data correctly by:
    1. Stopping the current frontend container
    2. Rebuilding it with the latest code (no cache)
    3. Starting the updated container
    """
    print("  📦 Stopping current frontend container...")
    try:
        # Stop frontend container
        subprocess.run([
            "docker-compose", "-f", "dhafnck_mcp_main/docker/docker-compose.yml", 
            "down", "dhafnck-frontend"
        ], capture_output=True, text=True, check=True)
        
        print("  🔨 Rebuilding frontend with latest code...")
        # Rebuild frontend container without cache
        subprocess.run([
            "docker-compose", "-f", "dhafnck_mcp_main/docker/docker-compose.yml", 
            "build", "dhafnck-frontend", "--no-cache"
        ], check=True)
        
        print("  🚀 Starting updated frontend container...")
        # Start updated frontend
        subprocess.run([
            "docker-compose", "-f", "dhafnck_mcp_main/docker/docker-compose.yml", 
            "up", "-d", "dhafnck-frontend"
        ], check=True)
        
        print("✅ Frontend rebuilt successfully!")
        print("🌐 Frontend available at: http://localhost:3800")
        print("💡 Your restored data should now be visible in the UI")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Warning: Frontend rebuild failed: {e}")
        print("💡 You may need to manually rebuild the frontend container")
        print("   Run: docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml build dhafnck-frontend --no-cache")
    except Exception as e:
        print(f"❌ Unexpected error during frontend rebuild: {e}")

def main():
    choices = [
        "Start (normal - production mode) - Stable, production-ready setup",
        "Start (development - with debug & hot reload) - Debug mode with live code updates",
        "Start (local - no auth, local development) - Simplified, no-auth for local testing",
        "Start (redis - with Redis session persistence) - Adds Redis for session storage",
        "Run E2E tests - Execute end-to-end tests in dev mode",
        "Stop containers - Shutdown all running containers",
        "Show logs - View real-time output from containers",
        "Shell into container - Access bash shell inside container",
        "Restart containers - Stop and restart selected mode",
        "Build backend only - Rebuild just the backend container",
        "Build frontend only - Rebuild just the frontend container",
        "Build both - Rebuild both backend and frontend containers",
        "Clean backend only - Remove backend container and image",
        "Clean frontend only - Remove frontend container and image",
        "Clean both - Remove both backend and frontend containers/images",
        "Clean & Rebuild (full reset) - Remove and rebuild everything",
        "Import/Restore SQLite DB - Copy database into container and rebuild frontend",
        "Fix Database Permissions - Fix readonly database errors",
        "Inspect MCP Server - Open MCP inspector at http://localhost:8000/mcp/",
        "Exit - Close this menu"
    ]
    
    while True:
        choice = questionary.select(
            "Select a Docker action:",
            choices=choices
        ).ask()
        
        # Extract the main action text before the description for comparison
        choice_main = choice.split(" - ")[0]
        
        if choice_main == "Start (normal - production mode)":
            # Normal mode: Production-like environment
            # - Runs with default settings from base compose file
            # - No debug or hot reload; optimized for stability
            # - Should be started first to establish baseline functionality
            print("\nStarting in Normal Mode (Production-like environment):")
            print("- This mode uses the base configuration for a stable, production-ready setup.")
            print("- No debugging or hot reload features are enabled.")
            print("- Frontend will be available at http://localhost:3800")
            print("- Recommended to run this mode first to verify core functionality before other modes.\n")
            compose_files = get_compose_files("normal")
            subprocess.run(["docker", "compose"] + compose_files + ["up"])
            fix_database_permissions()
        elif choice_main == "Start (development - with debug & hot reload)":
            # Development mode: Enables debugging and hot reload
            # - Depends on base configuration being functional
            # - Run after testing normal mode to ensure base setup works
            # - Useful for developers needing live feedback on code changes
            print("\nStarting in Development Mode (with Debug & Hot Reload):")
            print("- This mode builds on the base configuration, adding debugging capabilities.")
            print("- Hot reload is enabled via volume mounts for immediate code change feedback.")
            print("- Frontend will be available at http://localhost:3800")
            print("- Ensure Normal Mode works first, as this mode depends on a stable base setup.\n")
            compose_files = get_compose_files("dev-fast")
            subprocess.run(["docker", "compose"] + compose_files + ["up"])
            fix_database_permissions()
        elif choice_main == "Start (local - no auth, local development)":
            # Local mode: Simplified setup for local development
            # - Disables authentication for ease of access
            # - Depends on base configuration; run after normal mode is verified
            # - Ideal for quick local testing without security barriers
            print("\nStarting in Local Mode (No Auth, Local Development):")
            print("- This mode uses the base configuration but disables authentication for simplicity.")
            print("- Designed for local testing without security overhead.")
            print("- Frontend will be available at http://localhost:3800")
            print("- Run after verifying Normal Mode to ensure the base setup is functional.\n")
            compose_files = get_compose_files("local")
            subprocess.run(["docker", "compose"] + compose_files + ["up"])
            fix_database_permissions()
        elif choice_main == "Start (redis - with Redis session persistence)":
            # Redis mode: Adds session persistence with Redis
            # - Depends on base configuration and Redis service availability
            # - Run after normal mode to ensure core app works before adding persistence
            # - Useful for testing session handling in a stateful environment
            print("\nStarting in Redis Mode (with Redis Session Persistence):")
            print("- This mode extends the base configuration to include Redis for session storage.")
            print("- Requires Redis service to be available alongside the main application.")
            print("- Frontend will be available at http://localhost:3800")
            print("- Run after Normal Mode to confirm core app functionality before adding persistence.\n")
            compose_files = get_compose_files("redis")
            subprocess.run(["docker", "compose"] + compose_files + ["up"])
            fix_database_permissions()
        elif choice_main == "Run E2E tests":
            # Use development mode for testing
            print("\nRunning End-to-End (E2E) Tests:")
            print("- This action starts containers in Development Mode (detached) for testing.")
            print("- Copies the latest E2E test files into the running container.")
            print("- Executes tests using pytest inside the container.")
            print("- Ensure Development Mode setup is functional before running tests.\n")
            compose_files = get_compose_files("dev-fast")
            subprocess.run(["docker", "compose"] + compose_files + ["up", "-d"])
            # Copy the latest e2e tests into the running container
            subprocess.run(["docker", "cp", "dhafnck_mcp_main/tests/e2e", "dhafnck-mcp-server:/app/tests/"])
            subprocess.run([
                "docker", "exec", "-it", "dhafnck-mcp-server",
                "pytest", "/app/tests/e2e"
            ])
        elif choice_main == "Stop containers":
            # Stop all possible configurations
            print("\nStopping All Containers:")
            print("- This action will stop containers across all modes (Normal, Development, Local, Redis).")
            print("- Ensures a clean shutdown of all running services.")
            print("- Run this before switching modes or to free up system resources.\n")
            for mode in ["normal", "development", "dev-fast", "local", "redis"]:
                compose_files = get_compose_files(mode)
                subprocess.run(["docker", "compose"] + compose_files + ["down"], 
                             capture_output=True, text=True)  # Suppress output for cleanup
        elif choice_main == "Show logs":
            # Ask which mode to show logs for
            print("\nShowing Container Logs:")
            print("- Logs provide real-time output from running containers.")
            print("- You will be prompted to select the mode for which to view logs.")
            print("- Ensure the relevant mode is running before attempting to view logs.\n")
            mode_choice = questionary.select(
                "Which mode's logs do you want to see?",
                choices=[
                    "Normal",
                    "Development",
                    "Local",
                    "Redis"
                ]
            ).ask()
            mode_map = {
                "Normal": "normal",
                "Development": "dev-fast",
                "Local": "local",
                "Redis": "redis"
            }
            mode_key = mode_map[mode_choice]
            compose_files = get_compose_files(mode_key)
            subprocess.run(["docker", "compose"] + compose_files + ["logs", "-f"])
        elif choice_main == "Shell into container":
            container_choice = questionary.select(
                "Which container do you want to shell into?",
                choices=[
                    "Backend (dhafnck-mcp-server)",
                    "Frontend (dhafnck-frontend)",
                    "Redis (dhafnck-redis)"
                ]
            ).ask()
            container_map = {
                "Backend (dhafnck-mcp-server)": "dhafnck-mcp-server",
                "Frontend (dhafnck-frontend)": "dhafnck-frontend",
                "Redis (dhafnck-redis)": "dhafnck-redis"
            }
            container_name = container_map[container_choice]
            print(f"\nOpening Shell into {container_choice}:")
            print(f"- This action opens a shell inside the {container_name} container.")
            print("- Useful for debugging or manual configuration within the container.")
            print("- Ensure the container is running before attempting to access the shell.\n")
            shell_cmd = "/bin/bash" if container_name != "dhafnck-frontend" else "/bin/sh"
            subprocess.run([
                "docker", "exec", "-it", container_name, shell_cmd
            ])
        elif choice_main == "Restart containers":
            # Ask which mode to restart
            print("\nRestarting Containers:")
            print("- This action stops and then restarts containers for the selected mode.")
            print("- You will be prompted to choose the mode to restart.")
            print("- Useful for applying configuration changes or recovering from errors.\n")
            mode_choice = questionary.select(
                "Which mode do you want to restart?",
                choices=[
                    "Normal",
                    "Development",
                    "Local",
                    "Redis"
                ]
            ).ask()
            mode_map = {
                "Normal": "normal",
                "Development": "dev-fast",
                "Local": "local",
                "Redis": "redis"
            }
            mode_key = mode_map[mode_choice]
            compose_files = get_compose_files(mode_key)
            subprocess.run(["docker", "compose"] + compose_files + ["down"])
            subprocess.run(["docker", "compose"] + compose_files + ["up", "-d"])
        elif choice_main == "Rebuild frontend only":
            print("\nRebuilding Frontend Container:")
            print("- This will stop, remove, and rebuild only the frontend container.")
            print("- The frontend will be available at http://localhost:3800 after rebuild.")
            print("- Other services will remain running.\n")
            
            # Stop and remove frontend container and image
            subprocess.run(["docker", "stop", "dhafnck-frontend"], capture_output=True, text=True)
            subprocess.run(["docker", "rm", "dhafnck-frontend"], capture_output=True, text=True)
            subprocess.run(["docker", "rmi", "dhafnck/frontend:latest"], capture_output=True, text=True)
            
            # Get current mode to rebuild with correct compose files
            mode_choice = questionary.select(
                "Which mode are you currently running?",
                choices=[
                    "Normal",
                    "Development",
                    "Local",
                    "Redis"
                ]
            ).ask()
            mode_map = {
                "Normal": "normal",
                "Development": "dev-fast",
                "Local": "local",
                "Redis": "redis"
            }
            mode_key = mode_map[mode_choice]
            compose_files = get_compose_files(mode_key)
            
            # Rebuild and start frontend
            print("Building frontend container...")
            subprocess.run(["docker", "compose"] + compose_files + ["build", "--no-cache", "dhafnck-frontend"])
            print("Starting frontend container...")
            subprocess.run(["docker", "compose"] + compose_files + ["up", "-d", "dhafnck-frontend"])
            print("\nFrontend rebuild complete! Available at http://localhost:3800")
        elif choice_main == "Clean & Rebuild (full reset)":
            # Ask which mode to clean and rebuild
            print("\nCleaning & Rebuilding (Full Reset):")
            print("- This action removes containers, images, and volumes, then rebuilds from scratch.")
            print("- Backups of databases are created before cleaning.")
            print("- You will be prompted to select the mode to reset or all modes for a complete cleanup.")
            print("- Run this to resolve persistent issues or start with a fresh environment.\n")
            mode_choice = questionary.select(
                "Which mode do you want to clean and rebuild?",
                choices=[
                    "Normal",
                    "Development", 
                    "Local",
                    "Redis",
                    "All modes (complete cleanup)"
                ]
            ).ask()
            
            # Map display names to mode keys
            mode_map = {
                "Normal": "normal",
                "Development": "dev-fast",
                "Local": "local", 
                "Redis": "redis",
                "All modes (complete cleanup)": "all"
            }
            mode_key = mode_map[mode_choice]
            
            # Backup current DBs before cleaning
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            dbs = [
                ("/data/dhafnck_mcp.db", f"dhafnck_mcp.db.bak-{timestamp}"),
                ("/data/dhafnck_mcp_test.db", f"dhafnck_mcp_test.db.bak-{timestamp}")
            ]
            for db_path, backup_name in dbs:
                print(f"Backing up {db_path} to {backup_name} (if exists)...")
                # Try to copy from container to host, ignore errors if file doesn't exist
                try:
                    subprocess.run([
                        "docker", "cp", f"dhafnck-mcp-server:{db_path}", backup_name
                    ], check=True)
                except subprocess.CalledProcessError:
                    print(f"  (No {db_path} found in container, skipping)")
            print("Backup complete. Proceeding with reset...\n")
            
            if mode_key == "all":
                print("\n⚠️  This will stop and remove all containers, images, volumes, and cache, then rebuild everything from scratch.\n")
                print("This includes the frontend container running on port 3800.\n")
                # Stop all configurations
                for mode in ["normal", "development", "dev-fast", "local", "redis"]:
                    compose_files = get_compose_files(mode)
                    subprocess.run(["docker", "compose"] + compose_files + ["down", "-v", "--rmi", "all", "--remove-orphans"], 
                                 capture_output=True, text=True)
                
                # Clean Docker system and remove frontend image
                subprocess.run(["docker", "rmi", "dhafnck/frontend:latest"], capture_output=True, text=True)
                subprocess.run(["docker", "builder", "prune", "-f"])
                
                # Ask which mode to rebuild after cleaning all
                rebuild_choice = questionary.select(
                    "Which mode do you want to rebuild and start?",
                    choices=[
                        "Normal",
                        "Development",
                        "Local", 
                        "Redis"
                    ]
                ).ask()
                rebuild_map = {
                    "Normal": "normal",
                    "Development": "dev-fast",
                    "Local": "local",
                    "Redis": "redis"
                }
                rebuild_key = rebuild_map[rebuild_choice]
                compose_files = get_compose_files(rebuild_key)
                subprocess.run(["docker", "compose"] + compose_files + ["build", "--no-cache"])
                subprocess.run(["docker", "compose"] + compose_files + ["up", "-d"])
            else:
                print(f"\n⚠️  This will stop and remove containers, images, and volumes for {mode_choice} mode, then rebuild.\n")
                # Clean only the selected mode
                compose_files = get_compose_files(mode_key)
                subprocess.run(["docker", "compose"] + compose_files + ["down", "-v", "--rmi", "all", "--remove-orphans"])
                subprocess.run(["docker", "builder", "prune", "-f"])
                subprocess.run(["docker", "compose"] + compose_files + ["build", "--no-cache"])
                subprocess.run(["docker", "compose"] + compose_files + ["up", "-d"])
        elif choice_main == "Import/Restore SQLite DB":
            print("\nImporting/Restoring SQLite Database:")
            print("- This action copies a SQLite database file into the container.")
            print("- Automatically fixes database permissions after import.")
            print("- Rebuilds the frontend container to ensure UI displays restored data.")
            print("- You will be prompted to select which database (Main or Test) to restore.")
            print("- Ensure the container is running to successfully import the database.\n")
            db_choice = questionary.select(
                "Which DB do you want to import/restore?",
                choices=[
                    "Main DB (production)",
                    "Test DB"
                ]
            ).ask()
            db_map = {
                "Main DB (production)": "/data/dhafnck_mcp.db",
                "Test DB": "/data/dhafnck_mcp_test.db"
            }
            db_path = db_map[db_choice]
            host_file = questionary.path(
                "Enter the path to the SQLite .db file to import (on your host):"
            ).ask()
            if not host_file or not os.path.isfile(host_file):
                print(f"File not found: {host_file}")
            else:
                print(f"Copying {host_file} to container:{db_path} ...")
                try:
                    subprocess.run([
                        "docker", "cp", host_file, f"dhafnck-mcp-server:{db_path}"
                    ], check=True)
                    print(f"Successfully imported {host_file} to {db_path} in container.")
                    print("🔧 Fixing permissions for imported database...")
                    fix_database_permissions()
                    
                    # Auto-rebuild frontend to ensure UI shows restored data
                    print("🔄 Rebuilding frontend to display restored data...")
                    rebuild_frontend_after_restore()
                    
                except subprocess.CalledProcessError as e:
                    print(f"Failed to import DB: {e}")
        elif choice_main == "Fix Database Permissions":
            print("\nFixing Database Permissions:")
            print("- This action fixes database file ownership issues that cause 'readonly database' errors.")
            print("- It changes the database file owner from host user to container user.")
            print("- This is especially useful after database backup/restore operations.\n")
            fix_database_permissions()
        elif choice_main == "Inspect MCP Server":
            print("\nStarting MCP Inspector:")
            print("- This will open the MCP inspector for your server at http://localhost:8000/mcp/")
            print("- Press Ctrl+C to stop the inspector and clean up resources.")
            print("- The inspector allows you to explore and test MCP server capabilities.\n")
            
            inspector_process = None
            try:
                # Define cleanup function
                def cleanup_inspector(signum=None, frame=None):
                    print("\n\n🛑 Stopping MCP Inspector...")
                    if inspector_process:
                        inspector_process.terminate()
                        try:
                            inspector_process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            inspector_process.kill()
                    print("✅ Inspector stopped and resources cleaned up.")
                    # Reset signal handler to default
                    signal.signal(signal.SIGINT, signal.default_int_handler)
                
                # Set up signal handler for Ctrl+C
                signal.signal(signal.SIGINT, cleanup_inspector)
                
                # Run the inspector
                inspector_process = subprocess.Popen([
                    "npx", "@modelcontextprotocol/inspector", "http://localhost:8000/mcp/"
                ])
                
                print("🔍 MCP Inspector is running...")
                print("🌐 Opening browser at http://localhost:5173 (default inspector port)")
                print("📡 Connecting to MCP server at http://localhost:8000/mcp/")
                print("\nPress Ctrl+C to stop the inspector...\n")
                
                # Wait for the process to complete
                inspector_process.wait()
                
            except KeyboardInterrupt:
                # This will be caught by our signal handler
                pass
            except Exception as e:
                print(f"❌ Error running MCP inspector: {e}")
                if inspector_process:
                    cleanup_inspector()
            finally:
                # Ensure cleanup even if something unexpected happens
                if inspector_process and inspector_process.poll() is None:
                    cleanup_inspector()
        elif choice_main == "Exit":
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()