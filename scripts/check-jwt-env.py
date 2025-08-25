#!/usr/bin/env python3
"""
Check JWT configuration from .env file and Docker containers
"""

import os
import sys
import subprocess
from pathlib import Path

def read_env_file(env_path=".env"):
    """Read .env file and return as dictionary"""
    env_vars = {}
    
    if not Path(env_path).exists():
        print(f"❌ .env file not found at {env_path}")
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                env_vars[key.strip()] = value.strip()
    
    return env_vars

def check_docker_env():
    """Check JWT secrets in Docker container"""
    print("\n🐳 Checking Docker Container Environment:")
    print("=" * 60)
    
    try:
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=dhafnck-mcp-server", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if "dhafnck-mcp-server" not in result.stdout:
            print("⚠️  Docker container 'dhafnck-mcp-server' is not running")
            return
        
        # Check JWT secrets in container
        secrets_to_check = ["JWT_SECRET_KEY", "SUPABASE_JWT_SECRET", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
        
        for secret in secrets_to_check:
            result = subprocess.run(
                ["docker", "exec", "dhafnck-mcp-server", "sh", "-c", f"echo ${secret}"],
                capture_output=True,
                text=True
            )
            value = result.stdout.strip()
            
            if value and value != f"${secret}":
                # Show length but not the actual secret
                print(f"   ✅ {secret}: Defined (length: {len(value)})")
            else:
                print(f"   ❌ {secret}: Not defined in container")
                
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error checking Docker: {e}")
    except FileNotFoundError:
        print("   ❌ Docker command not found")

def main():
    print("=" * 60)
    print("JWT CONFIGURATION CHECKER")
    print("=" * 60)
    
    # Check .env file
    print("\n📄 Checking .env File:")
    print("-" * 60)
    
    env_vars = read_env_file()
    
    if not env_vars:
        print("❌ No environment variables found in .env file")
    else:
        print(f"✅ Found {len(env_vars)} environment variables in .env")
        
        # Check specific JWT-related variables
        jwt_vars = {
            "JWT_SECRET_KEY": None,
            "SUPABASE_JWT_SECRET": None,
            "SUPABASE_URL": None,
            "SUPABASE_ANON_KEY": None,
            "AUTH_ENABLED": None,
            "MVP_MODE": None
        }
        
        for key in jwt_vars.keys():
            if key in env_vars:
                value = env_vars[key]
                if key in ["JWT_SECRET_KEY", "SUPABASE_JWT_SECRET", "SUPABASE_ANON_KEY"]:
                    # Don't show actual secrets, just their length
                    print(f"   ✅ {key}: Defined (length: {len(value)})")
                    jwt_vars[key] = len(value)
                else:
                    # Safe to show non-secret values
                    print(f"   ✅ {key}: {value}")
                    jwt_vars[key] = value
            else:
                print(f"   ❌ {key}: Not found in .env")
    
    # Check if secrets match
    print("\n🔍 Secret Configuration Analysis:")
    print("-" * 60)
    
    jwt_secret_len = jwt_vars.get("JWT_SECRET_KEY")
    supabase_secret_len = jwt_vars.get("SUPABASE_JWT_SECRET")
    
    if jwt_secret_len and supabase_secret_len:
        if jwt_secret_len == supabase_secret_len:
            print(f"   ✅ Both secrets have same length ({jwt_secret_len} chars)")
            print("   ℹ️  If authentication still fails, secrets might be different")
            print("   💡 To use the same secret for both:")
            print("      1. Copy the SUPABASE_JWT_SECRET value")
            print("      2. Set JWT_SECRET_KEY to the same value")
        else:
            print(f"   ⚠️  Secrets have different lengths:")
            print(f"      - JWT_SECRET_KEY: {jwt_secret_len} chars")
            print(f"      - SUPABASE_JWT_SECRET: {supabase_secret_len} chars")
            print("   ❌ This WILL cause authentication failures!")
            print("\n   🔧 FIX: Make both secrets the same:")
            print("      In your .env file, set:")
            print("      JWT_SECRET_KEY=<copy your SUPABASE_JWT_SECRET here>")
    elif supabase_secret_len and not jwt_secret_len:
        print("   ❌ JWT_SECRET_KEY is missing!")
        print("   🔧 FIX: In your .env file, add:")
        print("      JWT_SECRET_KEY=<copy your SUPABASE_JWT_SECRET here>")
    elif jwt_secret_len and not supabase_secret_len:
        print("   ❌ SUPABASE_JWT_SECRET is missing!")
        print("   🔧 FIX: In your .env file, add:")
        print("      SUPABASE_JWT_SECRET=<copy your JWT_SECRET_KEY here>")
    else:
        print("   ❌ Both JWT secrets are missing!")
        print("   🔧 FIX: Add both to your .env file")
    
    # Check Docker environment
    check_docker_env()
    
    # Check if .env is being loaded by Docker
    print("\n📦 Docker Compose Configuration:")
    print("-" * 60)
    
    compose_files = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
    compose_found = False
    
    for compose_file in compose_files:
        if Path(compose_file).exists():
            compose_found = True
            print(f"   ✅ Found {compose_file}")
            
            # Check if it references .env
            with open(compose_file, 'r') as f:
                content = f.read()
                if "env_file" in content or ".env" in content:
                    print(f"   ✅ Docker Compose appears to load .env file")
                else:
                    print(f"   ⚠️  Docker Compose might not be loading .env file")
                    print(f"   💡 Add 'env_file: .env' to your service definition")
            break
    
    if not compose_found:
        print("   ℹ️  No docker-compose file found in current directory")
    
    # Final recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("=" * 60)
    
    if jwt_secret_len != supabase_secret_len:
        print("1. CRITICAL: Unify your JWT secrets in .env:")
        print("   - Copy SUPABASE_JWT_SECRET value")
        print("   - Set JWT_SECRET_KEY=<same value>")
        print()
        print("2. Restart Docker containers:")
        print("   docker-compose down")
        print("   docker-compose up -d")
        print()
        print("3. Verify the fix:")
        print("   python scripts/check-jwt-env.py")
    else:
        print("✅ JWT secrets appear to be configured correctly in .env")
        print()
        print("If authentication still fails:")
        print("1. Ensure Docker containers are using the .env file")
        print("2. Restart containers: docker-compose restart")
        print("3. Check container logs: docker logs dhafnck-mcp-server")

if __name__ == "__main__":
    main()