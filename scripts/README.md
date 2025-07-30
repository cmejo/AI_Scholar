# Scripts

This directory contains all project scripts organized by purpose.

## Directory Structure

- **setup/** - Initial setup and configuration scripts
- **deployment/** - Production deployment and maintenance scripts
- **dev.sh** - Development environment script
- **setup.sh** - Main setup script

## Setup Scripts
- `setup/setup_github.sh` - GitHub repository setup (Linux/Mac)
- `setup/setup_github.bat` - GitHub repository setup (Windows)
- `setup/add_to_git.sh` - Add files to git repository

## Deployment Scripts
- `deployment/deploy.sh` - Main deployment script
- `deployment/production-deploy.sh` - Production deployment
- `deployment/backup.sh` - Backup script
- `deployment/health-check.sh` - Health check script
- `deployment/maintenance.sh` - Maintenance script
- `deployment/update.sh` - Update script
- `deployment/validate-deployment.sh` - Deployment validation

## Usage

Make scripts executable:
```bash
chmod +x scripts/**/*.sh
```

Run setup:
```bash
./scripts/setup.sh
```

Deploy to production:
```bash
./scripts/deployment/production-deploy.sh
```
