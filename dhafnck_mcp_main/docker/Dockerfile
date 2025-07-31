# Multi-stage Dockerfile for DhafnckMCP Server
# Target: Image size under 200MB with full functionality

# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Set build arguments
ARG PYTHONUNBUFFERED=1
ARG PYTHONDONTWRITEBYTECODE=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install uv for faster dependency resolution
RUN pip install uv

# Copy dependency files and README (needed for package build)
# Build context is workspace root, so paths include dhafnck_mcp_main/
COPY dhafnck_mcp_main/pyproject.toml dhafnck_mcp_main/uv.lock* dhafnck_mcp_main/README.md ./

# Copy source code BEFORE creating virtual environment
COPY dhafnck_mcp_main/src/ src/

# Copy database schema files (needed for database initialization)
COPY dhafnck_mcp_main/database/ database/

# Copy agent library (needed for agent system)
COPY dhafnck_mcp_main/agent-library/ agent-library/

# Copy rule files (needed for runtime)
COPY 00_RULES/ ./00_RULES/

# Copy resource files (needed for MCP resources)
COPY 00_RESOURCES/ ./00_RESOURCES/

# Create virtual environment and install dependencies
RUN uv venv .venv

# First install specific critical dependencies
RUN uv pip install sqlalchemy==2.0.35 psycopg2-binary==2.9.10 pydantic==2.10.3 pydantic-settings==2.7.0

# Then sync the rest of the dependencies
RUN uv sync || echo "uv sync failed, continuing with pip install"

# Fallback: Install package in editable mode if sync failed
RUN uv pip install -e . || echo "editable install failed"

# Verify the installation worked
RUN .venv/bin/python -c "import sqlalchemy; print('✅ SQLAlchemy imported successfully')"
RUN .venv/bin/python -c "import fastmcp; print('✅ fastmcp module imported successfully')"

# Stage 2: Runtime stage
FROM python:3.11-slim AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src:/app
ENV FASTMCP_LOG_LEVEL=INFO
ENV FASTMCP_ENABLE_RICH_TRACEBACKS=0
ENV DATA_STORAGE_MODE=internal
ENV MCP_DB_PATH=/data/dhafnck_mcp.db
ENV DOCKER_CONTAINER=1
ENV LOG_DIR=/data/logs

# Create non-root user for security
RUN groupadd -r dhafnck && useradd -r -g dhafnck -s /bin/false dhafnck

# Create directories
WORKDIR /app
RUN mkdir -p /data /data/rules /data/resources /data/logs /app/logs /app/rules && \
    chown -R dhafnck:dhafnck /app /data

# Copy Python environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src /app/src
COPY --from=builder /app/README.md /app/
COPY --from=builder /app/pyproject.toml /app/
COPY --from=builder /app/database /app/database
COPY --from=builder /app/agent-library /app/agent-library
COPY --from=builder /app/00_RULES /app/rules
COPY --from=builder /app/00_RESOURCES /data/resources

# Create symbolic link from /data/rules to /app/rules for backward compatibility
# Remove /data/rules directory first, then create the symbolic link
RUN rm -rf /data/rules && ln -sf /app/rules /data/rules

# Copy startup scripts from scripts directory
COPY dhafnck_mcp_main/scripts/docker-entrypoint.sh /usr/local/bin/
COPY dhafnck_mcp_main/scripts/dev-entrypoint.sh /app/scripts/
COPY dhafnck_mcp_main/scripts/init_database.py /app/scripts/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /app/scripts/dev-entrypoint.sh /app/scripts/init_database.py

# Database files already copied from builder stage above

# Set proper ownership for both app and data directories
RUN chown -R dhafnck:dhafnck /app /data

# Switch to non-root user
USER dhafnck

# Expose port
EXPOSE 8000

# Activate virtual environment by updating PATH (must be after USER directive)
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Default command
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "-m", "fastmcp"] 