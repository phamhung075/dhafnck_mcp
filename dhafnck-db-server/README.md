# dhafnck-db-server

A scalable database server for the dhafnck_mcp project using Supabase/PostgreSQL.

## Overview

This project provides a separate database server that handles all database operations for the dhafnck_mcp project. It replaces the embedded SQLite database with a scalable PostgreSQL solution using Supabase local for development and production deployments.

## Architecture

- **Database**: PostgreSQL with Supabase
- **API**: FastAPI with async support
- **Authentication**: Supabase Auth with JWT tokens
- **Containerization**: Docker with multi-stage builds
- **Monitoring**: Structured logging and health checks

## Features

- RESTful API for all database operations
- Support for tasks, subtasks, templates, and checklists
- Authentication and authorization
- Connection pooling and caching
- Comprehensive error handling
- Performance monitoring
- Docker containerization

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Supabase CLI

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```

### Development

1. Start Supabase local:
   ```bash
   supabase start
   ```

2. Run migrations:
   ```bash
   alembic upgrade head
   ```

3. Start the server:
   ```bash
   uvicorn dhafnck_db_server.main:app --reload
   ```

### Docker

1. Build the container:
   ```bash
   docker build -t dhafnck-db-server .
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Configuration is handled through environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase API key
- `JWT_SECRET`: JWT signing secret
- `REDIS_URL`: Redis connection string (optional)

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src/dhafnck_db_server
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.