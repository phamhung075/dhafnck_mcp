# Environment Configuration Guide

## 🔐 Single Source of Truth: `.env` File

This project uses a **SINGLE `.env` file** at the root of the project as the unique source for all environment variables across all services, Docker containers, tests, and deployments.

## 📋 Quick Setup

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your values:**
   ```bash
   nano .env  # or use your favorite editor
   ```

3. **NEVER commit `.env` to version control** (it's already in `.gitignore`)

## 🔑 Critical Variables to Configure

### Database Credentials
```bash
DATABASE_PASSWORD=your_secure_password_here    # Change this!
POSTGRES_PASSWORD=${DATABASE_PASSWORD}         # Docker uses this
REDIS_PASSWORD=your_redis_password_here        # Change this!
```

### Security Keys
```bash
JWT_SECRET_KEY=generate_32_char_random_string      # Change this!
JWT_SECRET=generate_32_char_random_string      # Change this!
DHAFNCK_TOKEN=generate_your_token_here         # Change this!
```

### API Keys (if using AI features)
```bash
OPENAI_API_KEY=sk-your-actual-key              # From OpenAI
ANTHROPIC_API_KEY=sk-ant-your-actual-key       # From Anthropic
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token    # From GitHub
```

### Supabase (for cloud deployment)
```bash
SUPABASE_PROJECT_REF=your_project_ref
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
SUPABASE_DB_PASSWORD=your_db_password
```

## 🐳 Docker Integration

Docker Compose automatically reads from `.env`:

```yaml
# docker-compose.yml uses variables like:
DATABASE_URL: postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@postgres:5432/${DATABASE_NAME}
```

Start services with:
```bash
docker-compose up -d
```

## 🧪 Test Environment

Tests use the same `.env` but with test database:
```bash
TEST_DATABASE_NAME=dhafnck_mcp_test
TEST_DATABASE_URL=postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${TEST_DATABASE_NAME}
```

## 🚀 Production Deployment

For production, uncomment the production overrides section in `.env`:

```bash
ENV=production
NODE_ENV=production
APP_DEBUG=false
DHAFNCK_AUTH_ENABLED=true
ENABLE_METRICS=true
BACKUP_ENABLED=true
```

## 📝 Environment Variable Categories

### Core Settings
- `ENV`: Environment (dev/staging/production)
- `DATABASE_TYPE`: Database type (postgresql/supabase)
- `APP_DEBUG`: Debug mode (true/false)

### Database
- `DATABASE_HOST`: PostgreSQL host
- `DATABASE_PORT`: PostgreSQL port (5432)
- `DATABASE_NAME`: Database name
- `DATABASE_USER`: Database username
- `DATABASE_PASSWORD`: Database password

### Redis Cache
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port (6379)
- `REDIS_PASSWORD`: Redis password

### Security
- `JWT_SECRET_KEY`: Application secret key
- `JWT_SECRET`: JWT signing secret
- `DHAFNCK_TOKEN`: Application token

### Features
- `FEATURE_VISION_SYSTEM`: Enable vision system
- `FEATURE_HIERARCHICAL_CONTEXT`: Enable hierarchical context
- `FEATURE_MULTI_AGENT`: Enable multi-agent support

## 🔍 Validation

Check your configuration:

```bash
# Verify environment variables are loaded
source .env && echo $DATABASE_TYPE

# Test database connection
docker exec dhafnck-postgres pg_isready -U $DATABASE_USER

# Test Redis connection
docker exec dhafnck-redis redis-cli ping
```

## ⚠️ Security Best Practices

1. **Never commit `.env` to version control**
2. **Use strong, unique passwords** (minimum 16 characters)
3. **Rotate keys regularly** in production
4. **Use different credentials** for dev/staging/production
5. **Store production secrets** in secure vaults (AWS Secrets Manager, HashiCorp Vault)
6. **Limit API key permissions** to minimum required

## 🆘 Troubleshooting

### Database connection fails
- Check `DATABASE_HOST` is correct (localhost for local, postgres for Docker)
- Verify `DATABASE_PASSWORD` matches PostgreSQL configuration
- Ensure PostgreSQL is running: `docker ps`

### Redis connection fails
- Check `REDIS_PASSWORD` is set correctly
- Verify Redis is running: `docker ps`
- Test connection: `redis-cli -a $REDIS_PASSWORD ping`

### API keys not working
- Verify keys are valid and not expired
- Check key permissions/scopes
- Ensure no extra spaces or quotes in values

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Supabase Setup Guide](https://supabase.com/docs)