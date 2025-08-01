# Git Repository Update Scripts

This directory contains scripts for managing Git repository updates for the AI Scholar Advanced RAG project.

## Scripts Overview

### 🚀 `update_repo.sh` - Comprehensive Update Script

The main script for complete repository updates with full documentation and versioning.

**Features:**
- Comprehensive commit message generation
- Automatic file staging and organization
- Version tagging with semantic versioning
- Release notes generation
- Push to remote with error handling
- Repository status checking and validation

**Usage:**
```bash
# Full update (recommended)
./scripts/git/update_repo.sh

# Show repository status only
./scripts/git/update_repo.sh status

# Create commit without pushing
./scripts/git/update_repo.sh commit-only

# Push existing commits
./scripts/git/update_repo.sh push-only

# Create version tags only
./scripts/git/update_repo.sh tags-only

# Generate release notes only
./scripts/git/update_repo.sh release-notes

# Show help
./scripts/git/update_repo.sh help
```

### ⚡ `quick_update.sh` - Fast Update Script

A streamlined script for quick commits and pushes during development.

**Features:**
- Simple file staging and commit
- Custom or default commit messages
- Fast push to current branch
- Minimal user interaction

**Usage:**
```bash
# Quick update with default message
./scripts/git/quick_update.sh

# Quick update with custom message
./scripts/git/quick_update.sh "fix: resolve mobile responsiveness issues"
```

## When to Use Which Script

### Use `update_repo.sh` when:
- ✅ Completing major features or milestones
- ✅ Preparing for releases or deployments
- ✅ Need comprehensive documentation
- ✅ Want automatic version tagging
- ✅ Creating release notes for stakeholders

### Use `quick_update.sh` when:
- ⚡ Making small bug fixes or tweaks
- ⚡ Iterating during development
- ⚡ Need fast commits without ceremony
- ⚡ Working on experimental features

## Generated Files

The comprehensive update script creates several files:

### Version Tags
- **Version Tag**: `v2024.12.30-monitoring-pwa` (date-based with feature identifier)
- **Feature Tag**: `feature/production-monitoring-20241230` (feature-specific tag)

### Release Notes
- **File**: `RELEASE_NOTES_YYYYMMDD.md`
- **Content**: Comprehensive changelog with features, improvements, and migration notes

### Commit Messages
Structured commit messages following conventional commits format:
```
feat: Implement comprehensive production monitoring, testing, and PWA features

## Major Features Added:
- Production monitoring & testing system
- Progressive Web App infrastructure
- Enhanced user experience features

## Technical Implementation:
- Backend services and APIs
- Frontend PWA components
- Infrastructure improvements

## Benefits:
- Automated testing and monitoring
- Offline capabilities
- Enhanced performance
```

## Best Practices

### Commit Message Guidelines
- Use conventional commit format: `type: description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Keep first line under 50 characters
- Use body for detailed explanations

### Before Running Scripts
1. **Review Changes**: Check what files will be committed
2. **Test Locally**: Ensure all features work as expected
3. **Update Documentation**: Keep README and docs current
4. **Check Dependencies**: Verify all requirements are met

### After Running Scripts
1. **Verify Push**: Check that changes appear on remote repository
2. **Test Deployment**: Ensure deployment still works
3. **Monitor**: Check that monitoring systems detect the update
4. **Communicate**: Share release notes with team if needed

## Troubleshooting

### Common Issues

**Permission Denied:**
```bash
chmod +x scripts/git/update_repo.sh scripts/git/quick_update.sh
```

**Not in Git Repository:**
```bash
cd /path/to/your/ai-scholar-project
./scripts/git/update_repo.sh
```

**Remote Push Failed:**
```bash
# Check remote configuration
git remote -v

# Set up remote if missing
git remote add origin https://github.com/username/repo.git
```

**Merge Conflicts:**
```bash
# Pull latest changes first
git pull origin main

# Resolve conflicts, then run script again
./scripts/git/update_repo.sh
```

### Script Debugging

Enable verbose output:
```bash
bash -x ./scripts/git/update_repo.sh
```

Check script status:
```bash
./scripts/git/update_repo.sh status
```

## Security Considerations

- Scripts never commit sensitive files (`.env`, secrets, etc.)
- Always review staged files before committing
- Use SSH keys for authentication when possible
- Keep commit messages professional and informative

## Integration with CI/CD

These scripts work well with automated deployment:

```yaml
# Example GitHub Actions workflow
name: Deploy on Update
on:
  push:
    tags:
      - 'v*'
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: ./scripts/deployment/deploy.sh
```

## Customization

### Modify Commit Templates
Edit the commit message generation in `update_repo.sh`:
```bash
# Around line 150
cat > "$COMMIT_MESSAGE_FILE" << 'EOF'
# Your custom commit template here
EOF
```

### Change Version Format
Modify the version tag generation:
```bash
# Around line 200
VERSION_TAG="v$(date +%Y.%m.%d)-your-format"
```

### Add Custom Hooks
Add pre-commit or post-commit hooks:
```bash
# Before commit creation
./scripts/pre-commit-checks.sh

# After successful push
./scripts/post-push-notifications.sh
```

## Support

For issues with these scripts:
1. Check the troubleshooting section above
2. Review the script output for error messages
3. Ensure you have proper Git configuration
4. Verify repository permissions and access

---

**Happy coding! 🚀**