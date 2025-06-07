# 🚀 Deployment Guide

This guide covers different deployment strategies for StatementSense, from local development to production deployment.

## Quick Reference

| Command | Description |
|---------|-------------|
| `make docker-dev` | Development with hot reload |
| `make docker-prod` | Production deployment |
| `make docker-prod-nginx` | Production with Nginx proxy |
| `make verify` | Test deployment health |
| `make docker-down` | Stop all services |

## 🏠 Local Development

### 1. Development with Docker (Recommended)

```bash
# Start development environment
make docker-dev

# Download AI model (first time only)
docker-compose exec ollama ollama pull llama3.2:1b

# Verify everything is working
make verify
```

**Features:**
- Hot reload for backend and frontend
- pgAdmin available at http://localhost:5050
- Source code mounted for real-time changes
- Debug logging enabled

### 2. Mixed Development (Services + Local Code)

```bash
# Start only database and AI services
docker-compose -f docker-compose.dev.yml up -d

# Copy local environment
cp .env.local .env

# Run backend locally
source .venv/bin/activate
uvicorn app.main:app --reload

# Run frontend locally (in another terminal)
cd frontend
npm run dev
```

**Use when:**
- You want to debug with IDE
- Need to test different Python versions
- Developing new features extensively

## 🏭 Production Deployment

### 1. Standard Production

```bash
# Copy and configure production environment
cp .env.production .env
# Edit .env with secure passwords and keys

# Start production services
make docker-prod

# Verify deployment
make verify
```

**Features:**
- Multi-worker FastAPI backend
- Optimized frontend build
- Automatic database migrations
- Health checks and restart policies

### 2. Production with Nginx Proxy

```bash
# Configure nginx (edit nginx/nginx.conf if needed)
# Update domain names and SSL certificates

# Start with reverse proxy
make docker-prod-nginx

# Services available at:
# - Frontend: http://localhost:80
# - API: http://localhost:80/api/
# - Docs: http://localhost:80/docs
```

**Features:**
- Load balancing and reverse proxy
- SSL termination (when configured)
- Rate limiting and security headers
- Static file serving optimization

## 🔧 Configuration Files

### Environment Files

| File | Purpose |
|------|---------|
| `.env` | Default (Docker development) |
| `.env.local` | Local development without Docker |
| `.env.docker` | Explicit Docker development |
| `.env.production` | Production deployment template |

### Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base development configuration |
| `docker-compose.override.yml` | Development overrides (auto-included) |
| `docker-compose.dev.yml` | Services-only for local development |
| `docker-compose.prod.yml` | Production configuration |

## 🐳 Docker Architecture

### Development Mode
```
┌─────────────────┐
│ docker-compose  │
│ override.yml    │ (automatic)
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ docker-compose  │
│     .yml        │ (base)
└─────────────────┘
```

### Production Mode
```
┌─────────────────┐
│ docker-compose  │
│   .prod.yml     │ (explicit)
└─────────────────┘
```

## 🔐 Security Considerations

### Development
- Default passwords (acceptable for local development)
- CORS allows all origins
- Debug mode enabled
- File mounts for hot reload

### Production
- ✅ **Required:** Change default passwords
- ✅ **Required:** Generate secure SECRET_KEY
- ✅ **Required:** Configure proper CORS origins
- ✅ **Required:** Disable debug mode
- ✅ **Recommended:** Use HTTPS with SSL certificates
- ✅ **Recommended:** Set up firewall rules
- ✅ **Recommended:** Configure log rotation

### Security Checklist

```bash
# 1. Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Create strong database password
python -c "import secrets; print(secrets.token_urlsafe(16))"

# 3. Update .env.production with secure values
# 4. Configure SSL certificates in nginx/ssl/
# 5. Update CORS origins in app/main.py
# 6. Set up regular backups
```

## 📊 Monitoring and Maintenance

### Health Checks

```bash
# Quick health check
make verify

# Manual service checks
curl http://localhost:8000/health
curl http://localhost:3000/
docker-compose ps
```

### Logs and Debugging

```bash
# View all logs
make docker-logs

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Check resource usage
docker stats

# Database access
docker-compose exec postgres psql -U statement_user -d statement_sense
```

### Backup and Recovery

```bash
# Database backup
docker-compose exec postgres pg_dump -U statement_user statement_sense > backup.sql

# Volume backup
docker run --rm -v statement_sense_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore database
docker-compose exec -T postgres psql -U statement_user statement_sense < backup.sql
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
systemctl status docker  # Linux
# or
docker version

# Check compose file syntax
docker-compose config

# Check available resources
docker system df
docker system prune  # Clean up if needed
```

#### Database Connection Issues
```bash
# Check database service
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres pg_isready -U statement_user

# Reset database (development only)
docker-compose down -v
docker-compose up -d postgres
```

#### AI Model Issues
```bash
# Check Ollama service
docker-compose logs ollama

# Download model manually
docker-compose exec ollama ollama pull llama3.2:1b

# List available models
docker-compose exec ollama ollama list
```

#### File Upload Issues
```bash
# Check uploads directory permissions
ls -la uploads/
docker-compose exec backend ls -la /app/uploads/

# Check file size limits in nginx/nginx.conf
# client_max_body_size 50M;
```

### Performance Optimization

#### Backend
```bash
# Increase worker processes (production)
# In docker-compose.prod.yml:
# CMD ["uvicorn", "app.main:app", "--workers", "8"]

# Enable database connection pooling
# Add to .env:
# DATABASE_POOL_SIZE=20
# DATABASE_MAX_OVERFLOW=30
```

#### Database
```bash
# Optimize PostgreSQL settings
# Add to docker-compose volume mount:
# - ./postgresql.conf:/etc/postgresql/postgresql.conf

# Database maintenance
docker-compose exec postgres psql -U statement_user -d statement_sense -c "VACUUM ANALYZE;"
```

## 🌐 Deployment Platforms

### Local/VPS Deployment
- Use `docker-compose.prod.yml`
- Set up reverse proxy with SSL
- Configure firewall and security

### Cloud Platforms

#### Docker Compose on VPS
```bash
# Example for Ubuntu VPS
sudo apt update && sudo apt install docker.io docker-compose
git clone <repository>
cd statement-sense
cp .env.production .env
# Edit .env with production values
make docker-prod
```

#### AWS/GCP/Azure
- Use container services (ECS, Cloud Run, Container Instances)
- Set up managed databases (RDS, Cloud SQL, etc.)
- Configure load balancers and CDN

#### Kubernetes
- Convert compose files to Kubernetes manifests
- Use Helm charts for easier deployment
- Set up persistent volumes for data

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Secure passwords and keys generated
- [ ] SSL certificates obtained (production)
- [ ] Backup strategy planned
- [ ] Monitoring set up

### Deployment
- [ ] Services started successfully
- [ ] Health checks passing
- [ ] AI model downloaded
- [ ] Database migrations applied
- [ ] File uploads working

### Post-deployment
- [ ] Performance testing
- [ ] Security scan
- [ ] Backup verification
- [ ] Monitoring alerts configured
- [ ] Documentation updated

---

## 🆘 Support

If you encounter issues:

1. **Check logs**: `make docker-logs`
2. **Verify health**: `make verify`
3. **Restart services**: `make docker-down && make docker-dev`
4. **Check documentation**: Visit `/docs` endpoint
5. **Report issues**: Create GitHub issue with logs

For additional help, see the main README.md file.
