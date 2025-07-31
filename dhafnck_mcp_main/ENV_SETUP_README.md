# Environment Setup for DhafnckMCP Multi-Project AI Orchestration Platform

This directory contains comprehensive environment configuration files for the DhafnckMCP platform with PostgreSQL database, 4-tier hierarchical context system, Vision System integration, and 60+ specialized AI agents.

## 📁 Files

- **`env.example`** - Comprehensive environment variables template
- **`setup_env.sh`** - Interactive setup script
- **`ENV_SETUP_README.md`** - This file
- **`.env`** - Your local configuration (created from template)

## 🚀 Quick Setup

### Prerequisites

- **Python 3.12+** - Required for the platform
- **PostgreSQL 14+** - Primary database (migrated from SQLite)
- **Redis** (optional) - For session persistence and caching
- **Docker** (optional) - For containerized deployment

### Option 1: Interactive Setup (Recommended)

Run the interactive setup script:

```bash
cd dhafnck_mcp_main
./setup_env.sh
```

This script will:
- ✅ Create your `.env` file from the template
- ✅ Configure PostgreSQL database connection
- ✅ Set up 4-tier context system parameters
- ✅ Configure Vision System integration
- ✅ Help configure AI provider API keys
- ✅ Set up session persistence options
- ✅ Validate your configuration
- ✅ Provide Cursor MCP integration examples

### Option 2: Manual Setup

1. **Copy the template**:
   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file**:
   ```bash
   nano .env  # or your preferred editor
   ```

3. **Configure the essential variables**:
   ```bash
   # PostgreSQL Database (REQUIRED)
   DATABASE_URL=postgresql://user:password@localhost:5432/dhafnck_mcp
   DATABASE_MODE=local  # Options: local, container, mcp_stdin, test
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=40
   
   # 4-Tier Context System
   CONTEXT_CACHE_TTL=3600
   CONTEXT_INHERITANCE_ENABLED=true
   CONTEXT_DELEGATION_ENABLED=true
   
   # Vision System (Auto-enabled)
   VISION_SYSTEM_ENABLED=true
   VISION_PERFORMANCE_TARGET=5  # ms overhead target
   
   # Session Persistence (Redis recommended, memory fallback available)
   REDIS_URL=redis://localhost:6379/0
   
   # At least one AI provider (for agent capabilities)
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   # OR
   ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
   
   # Basic server settings
   MCP_ENVIRONMENT=development
   MCP_DEBUG=true
   MCP_LOG_LEVEL=INFO
   ```

## 🔧 Key Configuration Sections

### 💾 PostgreSQL Database (Required)
```bash
# Primary database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dhafnck_mcp
DATABASE_MODE=local                    # local, container, mcp_stdin, test
DB_POOL_SIZE=20                       # Connection pool size
DB_MAX_OVERFLOW=40                    # Max overflow connections
DB_POOL_TIMEOUT=30                    # Pool timeout in seconds
DB_ECHO=false                         # Log SQL queries (debug only)
```

### 🏗️ 4-Tier Context System
```bash
# Hierarchical context configuration
CONTEXT_CACHE_TTL=3600                # Cache time-to-live (seconds)
CONTEXT_INHERITANCE_ENABLED=true      # Enable context inheritance
CONTEXT_DELEGATION_ENABLED=true       # Enable upward delegation
CONTEXT_AUTO_CREATE=true              # Auto-create contexts
CONTEXT_SYNC_ENABLED=true             # Enable context synchronization
```

### 👁️ Vision System
```bash
# Strategic AI orchestration (auto-enabled)
VISION_SYSTEM_ENABLED=true            # Enable Vision System
VISION_PERFORMANCE_TARGET=5           # Target overhead in ms
VISION_CACHE_ENABLED=true             # Cache vision insights
VISION_WORKFLOW_HINTS=true            # Enable workflow guidance
VISION_PROGRESS_TRACKING=true         # Rich progress tracking
```

### 🔄 Session Persistence
```bash
# Redis for session and cache management
REDIS_URL=redis://localhost:6379/0    # Redis connection URL
SESSION_TTL=3600                      # 1 hour session lifetime
MAX_EVENTS_PER_SESSION=1000          # Max events per session
SESSION_COMPRESSION=true              # Enable compression
CACHE_ENABLED=true                    # Enable caching layer
```

### 🤖 AI Providers
```bash
# Configure for agent capabilities (at least one required)
OPENAI_API_KEY=sk-your-key-here      # OpenAI GPT models
ANTHROPIC_API_KEY=sk-ant-your-key    # Claude models
GOOGLE_API_KEY=your-key-here         # Gemini models
PERPLEXITY_API_KEY=pplx-your-key     # Perplexity AI
```

### 🖥️ Server Settings
```bash
MCP_HOST=localhost                    # Server host
MCP_PORT=8000                        # Server port
MCP_ENVIRONMENT=development          # Environment mode
MCP_DEBUG=true                       # Debug logging
MCP_LOG_LEVEL=INFO                   # Log level
PERFORMANCE_TARGET_RPS=15000         # Target requests per second
```

## 🔗 Cursor Integration

After setting up your `.env` file, update your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dhafnck_mcp_http": {
      "command": "python",
      "args": ["-m", "fastmcp.server"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/dhafnck_mcp",
        "DATABASE_MODE": "local",
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "your-actual-api-key-here",
        "ANTHROPIC_API_KEY": "your-actual-api-key-here",
        "CONTEXT_AUTO_CREATE": "true",
        "VISION_SYSTEM_ENABLED": "true",
        "MCP_DEBUG": "true",
        "MCP_LOG_LEVEL": "INFO",
        "SESSION_TTL": "3600",
        "MAX_EVENTS_PER_SESSION": "1000"
      }
    }
  }
}
```

## 🧪 Testing Your Setup

### Test PostgreSQL Connection
```bash
cd dhafnck_mcp_main
python -c "
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/dhafnck_mcp')
engine = create_engine(db_url)
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ PostgreSQL connection successful')
except Exception as e:
    print('❌ PostgreSQL connection failed:', e)
"
```

### Test Context System
```bash
# Test 4-tier context hierarchy
python -c "
from src.fastmcp.task_management.infrastructure.repositories import *
print('✅ Context system modules loaded successfully')
print('   - Global Context ✓')
print('   - Project Context ✓')
print('   - Branch Context ✓')
print('   - Task Context ✓')
"
```

### Test Session Store
```bash
cd dhafnck_mcp_main
python -c "
from src.fastmcp.server.session_store import get_global_event_store
import asyncio
store = asyncio.run(get_global_event_store())
print('✅ Session store initialized:', type(store).__name__)
"
```

### Test Health Check
```bash
# After starting your MCP server, use the health check tool in Cursor:
manage_connection action="health_check"
```

## 🛠️ Environment Examples

### Minimal Setup (Development)
```bash
# PostgreSQL + Basic functionality
DATABASE_URL=postgresql://postgres:password@localhost:5432/dhafnck_mcp_dev
DATABASE_MODE=local
OPENAI_API_KEY=sk-your-key-here
MCP_DEBUG=true
MCP_ENVIRONMENT=development
```

### Full Development Setup
```bash
# Complete development environment
DATABASE_URL=postgresql://postgres:password@localhost:5432/dhafnck_mcp_dev
DATABASE_MODE=local
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
MCP_ENVIRONMENT=development
MCP_DEBUG=true
DEV_MODE=true
HOT_RELOAD=true
CONTEXT_AUTO_CREATE=true
VISION_SYSTEM_ENABLED=true
DB_ECHO=true  # Enable SQL logging for debugging
```

### Production Setup
```bash
# Production environment with all features
DATABASE_URL=postgresql://prod_user:secure_password@db.example.com:5432/dhafnck_mcp_prod
DATABASE_MODE=container
REDIS_URL=redis://prod-redis.example.com:6379/0
OPENAI_API_KEY=sk-your-production-key
ANTHROPIC_API_KEY=sk-ant-your-production-key
MCP_ENVIRONMENT=production
MCP_DEBUG=false
MCP_LOG_LEVEL=WARNING
HTTPS_ENABLED=true
RATE_LIMIT_ENABLED=true
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
PERFORMANCE_TARGET_RPS=20000
VISION_PERFORMANCE_TARGET=3  # Stricter target for production
```

### Docker Setup
```bash
# Docker containerized environment
DATABASE_URL=postgresql://postgres:password@postgres:5432/dhafnck_mcp
DATABASE_MODE=container
REDIS_URL=redis://redis:6379/0
# Mount secrets as files in Docker
OPENAI_API_KEY_FILE=/run/secrets/openai_key
ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key
MCP_ENVIRONMENT=production
MCP_HOST=0.0.0.0  # Listen on all interfaces in container
```

## 🔐 Security Notes

- ✅ **Never commit `.env` files** - They're automatically added to `.gitignore`
- ✅ **Use different API keys** for development and production
- ✅ **Rotate API keys regularly**
- ✅ **Use environment-specific Redis instances**
- ✅ **Enable rate limiting in production**

## 🐛 Troubleshooting

### PostgreSQL Connection Issues
```bash
# Test PostgreSQL connection
psql -U postgres -d dhafnck_mcp -c "SELECT 1;"

# If PostgreSQL isn't running:
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database if it doesn't exist:
createdb -U postgres dhafnck_mcp

# Grant permissions:
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE dhafnck_mcp TO your_user;"
```

### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# If Redis isn't running:
sudo systemctl start redis  # Linux
brew services start redis   # macOS
```

### Database Migration Issues
```bash
# Run migrations manually
cd dhafnck_mcp_main
python -m alembic upgrade head

# Check migration status
python -m alembic current
```

### Context System Issues
```bash
# Verify context hierarchy
python -c "
from src.fastmcp.task_management.application.use_cases.context import *
print('✅ Context use cases loaded')
from src.fastmcp.task_management.domain.services import *
print('✅ Domain services loaded')
"
```

### API Key Issues
```bash
# Test OpenAI key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test Anthropic key  
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages
```

### Performance Issues
```bash
# Check database performance
python -c "
import time
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url, pool_size=20)

start = time.time()
with engine.connect() as conn:
    for i in range(100):
        conn.execute(text('SELECT 1'))
elapsed = time.time() - start
print(f'✅ 100 queries in {elapsed:.2f}s ({100/elapsed:.0f} qps)')
"
```

## 📞 Support

If you encounter issues:

1. **Check the logs**: Look for error messages in your MCP server logs
2. **Verify configuration**: Run `./setup_env.sh` again to validate settings
3. **Test components**: Use the test commands above to isolate issues
4. **Use health check**: Run `manage_connection action="health_check"` for diagnostics
5. **Check documentation**: See [Comprehensive Troubleshooting Guide](docs/COMPREHENSIVE_TROUBLESHOOTING_GUIDE.md)

## 🎉 Next Steps

After setup:
1. ✅ Initialize PostgreSQL database and run migrations
2. ✅ Start your MCP server with the configuration
3. ✅ Test connection from Cursor with `manage_connection action="health_check"`
4. ✅ Create your first project with `manage_project action="create"`
5. ✅ Call your first agent with `call_agent name_agent="@uber_orchestrator_agent"`
6. ✅ Enjoy the full DhafnckMCP Multi-Project AI Orchestration Platform! 🚀

## 📚 Additional Resources

- [Architecture Overview](docs/architecture.md) - System design and components
- [API Reference](docs/api-reference.md) - Complete MCP tools documentation
- [Vision System Guide](docs/vision/README.md) - Strategic AI orchestration
- [Domain-Driven Design](docs/domain-driven-design.md) - DDD implementation
- [Docker Deployment](docs/docker-deployment.md) - Production deployment guide

---
*Last Updated: 2025-01-31 - Updated for PostgreSQL, 4-Tier Context, and Vision System* 