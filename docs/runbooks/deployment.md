# Runbook: Deployment

This runbook covers deployment procedures for the Analytics Portfolio application.

## Environments

| Environment | Branch | Server | URL |
|-------------|--------|--------|-----|
| Development | `development` | Local | http://localhost:8050 |
| Staging | `staging` | Homelab (hotserv) | Internal |
| Production | `main` | Bandit Labs VPS | https://leodata.science |

## CI/CD Pipeline

### Automatic Deployment

Deployments are triggered automatically via Gitea Actions:

1. **Push to `staging`** → Deploys to staging server
2. **Push to `main`** → Deploys to production server

### Workflow Files

- `.gitea/workflows/ci.yml` - Runs linting and tests on all branches
- `.gitea/workflows/deploy-staging.yml` - Staging deployment
- `.gitea/workflows/deploy-production.yml` - Production deployment

### Required Secrets

Configure these in Gitea repository settings:

| Secret | Description |
|--------|-------------|
| `STAGING_HOST` | Staging server hostname/IP |
| `STAGING_USER` | SSH username for staging |
| `STAGING_SSH_KEY` | Private key for staging SSH |
| `PROD_HOST` | Production server hostname/IP |
| `PROD_USER` | SSH username for production |
| `PROD_SSH_KEY` | Private key for production SSH |

## Manual Deployment

### Prerequisites

- SSH access to target server
- Repository cloned at `~/apps/personal-portfolio`
- Virtual environment created at `.venv`
- Docker and Docker Compose installed
- PostgreSQL container running

### Steps

```bash
# 1. SSH to server
ssh user@server

# 2. Navigate to app directory
cd ~/apps/personal-portfolio

# 3. Pull latest changes
git fetch origin {branch}
git reset --hard origin/{branch}

# 4. Activate virtual environment
source .venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run database migrations (if any)
# python -m alembic upgrade head

# 7. Run dbt models
cd dbt && dbt run --profiles-dir . && cd ..

# 8. Restart application
docker compose down
docker compose up -d

# 9. Verify health
curl http://localhost:8050/health
```

## Rollback Procedure

### Quick Rollback

If deployment fails, rollback to previous commit:

```bash
# 1. Find previous working commit
git log --oneline -10

# 2. Reset to that commit
git reset --hard {commit_hash}

# 3. Restart services
docker compose down
docker compose up -d

# 4. Verify
curl http://localhost:8050/health
```

### Full Rollback (Database)

If database changes need to be reverted:

```bash
# 1. Stop application
docker compose down

# 2. Restore database backup
pg_restore -h localhost -U portfolio -d portfolio backup.dump

# 3. Revert code
git reset --hard {commit_hash}

# 4. Run dbt at that version
cd dbt && dbt run --profiles-dir . && cd ..

# 5. Restart
docker compose up -d
```

## Health Checks

### Application Health

```bash
curl http://localhost:8050/health
```

Expected response:
```json
{"status": "healthy"}
```

### Database Health

```bash
docker compose exec postgres pg_isready -U portfolio
```

### Container Status

```bash
docker compose ps
```

## Monitoring

### View Logs

```bash
# All services
make logs

# Specific service
make logs SERVICE=postgres

# Or directly
docker compose logs -f
```

### Check Resource Usage

```bash
docker stats
```

## Troubleshooting

### Application Won't Start

1. Check container logs: `docker compose logs app`
2. Verify environment variables: `cat .env`
3. Check database connectivity: `docker compose exec postgres pg_isready`
4. Verify port availability: `lsof -i :8050`

### Database Connection Errors

1. Check postgres container: `docker compose ps postgres`
2. Verify DATABASE_URL in `.env`
3. Check postgres logs: `docker compose logs postgres`
4. Test connection: `docker compose exec postgres psql -U portfolio -c '\l'`

### dbt Failures

1. Check dbt logs: `cd dbt && dbt debug`
2. Verify profiles.yml: `cat dbt/profiles.yml`
3. Run with verbose output: `dbt run --debug`

### Out of Memory

1. Check memory usage: `free -h`
2. Review container limits in docker-compose.yml
3. Consider increasing swap or server resources

## Backup Procedures

### Database Backup

```bash
# Create backup
docker compose exec postgres pg_dump -U portfolio portfolio > backup_$(date +%Y%m%d).sql

# Compressed backup
docker compose exec postgres pg_dump -U portfolio -Fc portfolio > backup_$(date +%Y%m%d).dump
```

### Restore from Backup

```bash
# From SQL file
docker compose exec -T postgres psql -U portfolio portfolio < backup.sql

# From dump file
docker compose exec -T postgres pg_restore -U portfolio -d portfolio < backup.dump
```

## Deployment Checklist

Before deploying to production:

- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Staging deployment successful
- [ ] Manual testing on staging complete
- [ ] Database backup taken
- [ ] Rollback plan confirmed
- [ ] Team notified of deployment window
