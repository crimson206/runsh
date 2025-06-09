# GitHub Integration

Use scripts directly from GitHub repositories with automatic caching and team collaboration.

## Overview

RunSH can fetch and execute scripts directly from GitHub repositories, making it perfect for:

- **Team collaboration** - Share scripts across team members
- **Centralized management** - Maintain scripts in version control
- **Automatic distribution** - Everyone gets updates automatically
- **Offline capability** - Cached scripts work without internet

## Quick Setup

### 1. Configure GitHub Source

```bash
# Initialize configuration
runsh config init

# Edit .runsh/config.yaml
nano .runsh/config.yaml
```

```yaml
scripts_dir: "https://github.com/user/repo/tree/main/scripts"
```

### 2. Use GitHub Scripts

```bash
# List available scripts (fetches from GitHub)
runsh list

# Run a script (uses cached version if available)
runsh deploy production --verbose
```

That's it! RunSH handles the rest automatically.

## GitHub URL Formats

### Standard Repository Structure

```
https://github.com/user/repo/tree/main/scripts
                   ↑    ↑    ↑     ↑      ↑
                owner  repo branch  path
```

### Examples

```yaml
# Main branch, scripts folder
scripts_dir: "https://github.com/company/devops/tree/main/scripts"

# Different branch
scripts_dir: "https://github.com/company/devops/tree/develop/scripts"

# Nested directory
scripts_dir: "https://github.com/company/tools/tree/main/deployment/scripts"

# Root directory
scripts_dir: "https://github.com/company/scripts/tree/main"
```

## Repository Setup

### 1. Create Scripts Repository

```bash
mkdir devops-scripts
cd devops-scripts
git init
```

### 2. Add Scripts with Metadata

Create `scripts/deploy.sh`:

```bash
#!/bin/bash

# @description: Deploy application to specified environment
# @arg environment: Target environment (dev/staging/prod)
# @option version,v [default=latest]: Version to deploy
# @option dry-run,d [flag]: Preview deployment without executing

echo "Deploying $VERSION to $ENVIRONMENT"
[ "$DRY_RUN" = "1" ] && echo "DRY RUN: Would deploy now"
```

### 3. Organize Your Scripts

```
scripts/
├── deploy.sh              # Deployment automation
├── backup.sh              # Database backup
├── monitor.sh             # Health monitoring
├── setup/
│   ├── provision.sh       # Infrastructure setup
│   └── configure.sh       # Configuration management
└── utils/
    ├── cleanup.sh         # Cleanup utilities
    └── logs.sh            # Log management
```

**Note**: RunSH only discovers `.sh` files in the specified directory, not subdirectories.

### 4. Push to GitHub

```bash
git add .
git commit -m "Add deployment scripts"
git push origin main
```

## Team Collaboration

### Setup for Teams

1. **Create shared repository**:
   ```bash
   git clone https://github.com/company/devops-scripts.git
   cd devops-scripts
   ```

2. **Add team scripts**:
   ```bash
   mkdir scripts
   # Add your scripts here
   git add scripts/
   git commit -m "Add team scripts"
   git push
   ```

3. **Configure team members**:
   Each team member creates `.runsh/config.yaml`:
   ```yaml
   scripts_dir: "https://github.com/company/devops-scripts/tree/main/scripts"
   ```

4. **Everyone gets the same tools**:
   ```bash
   runsh list  # Same scripts for everyone
   ```

### Version Management

#### Use Branches for Different Environments

```yaml
# Development team
scripts_dir: "https://github.com/company/scripts/tree/develop/scripts"

# Production team  
scripts_dir: "https://github.com/company/scripts/tree/main/scripts"

# Experimental features
scripts_dir: "https://github.com/company/scripts/tree/feature/new-tools/scripts"
```

#### Pin to Specific Commits

```yaml
# Pin to specific commit for stability
scripts_dir: "https://github.com/company/scripts/tree/abc123456/scripts"
```

### Script Updates

When scripts are updated in the repository:

1. **Automatic updates**: RunSH checks for updates every 24 hours
2. **Manual refresh**: `runsh cache clean --all`
3. **Check status**: `runsh cache list`

## Caching System

### How It Works

1. **First run**: Scripts downloaded from GitHub API
2. **Cached locally**: Stored in `.runsh/cache/`
3. **Subsequent runs**: Use cached versions (fast!)
4. **Auto-refresh**: Cache expires after 24 hours

### Cache Management

```bash
# View cached scripts
runsh cache list

# Cache information
runsh cache info

# Clear expired cache
runsh cache clean

# Clear all cache (force refresh)
runsh cache clean --all
```

### Cache Location

```
.runsh/
└── cache/
    └── github_user_repo_main_scripts/
        ├── deploy.sh           # Cached script
        ├── backup.sh           # Cached script
        └── .metadata           # Cache metadata
```

### Offline Usage

Once scripts are cached, you can work offline:

```bash
# Works offline (uses cache)
runsh deploy staging

# Shows cache status
runsh cache info
```

## Authentication

### Public Repositories

No authentication needed for public repositories.

### Private Repositories

For private repositories, you'll need GitHub authentication:

1. **Create Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create token with `repo` scope

2. **Set environment variable**:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```

3. **Use private repository**:
   ```yaml
   scripts_dir: "https://github.com/company/private-scripts/tree/main/scripts"
   ```

**Note**: Private repository support is planned for future versions.

## Advanced Usage

### Multiple Repositories

Use environment variables to switch between script sources:

```bash
# Development scripts
export RUNSH_SCRIPTS_DIR="https://github.com/team/dev-scripts/tree/main/scripts"
runsh deploy

# Production scripts
export RUNSH_SCRIPTS_DIR="https://github.com/team/prod-scripts/tree/main/scripts"  
runsh deploy
```

### Repository Structure Best Practices

#### Recommended Structure

```
devops-scripts/
├── README.md               # Documentation
├── scripts/                # RunSH scripts
│   ├── deploy.sh
│   ├── backup.sh
│   └── monitor.sh
├── docs/                   # Script documentation
├── configs/                # Configuration templates
└── examples/               # Usage examples
```

#### Script Documentation

Document your scripts in the repository:

```markdown
# DevOps Scripts

## Available Scripts

### deploy.sh
Deploy applications to various environments.

Usage: `runsh deploy <environment> --version <version>`

### backup.sh  
Backup databases with compression.

Usage: `runsh backup <database> --compress`

## Setup

1. Configure RunSH:
   ```yaml
   scripts_dir: "https://github.com/company/devops-scripts/tree/main/scripts"
   ```

2. Run scripts:
   ```bash
   runsh list
   runsh deploy production
   ```
```

## Security Considerations

### Script Review

Before using scripts from any repository:

1. **Review the scripts** - Check what they do
2. **Verify the source** - Ensure it's a trusted repository
3. **Check permissions** - Understand what access scripts need
4. **Test safely** - Use `--dry-run` flags when available

### Safe Practices

```bash
# Always review scripts first
runsh cache clean --all
git clone https://github.com/user/repo
cat repo/scripts/deploy.sh  # Review the script

# Test with dry run
runsh deploy staging --dry-run

# Use specific branches for stability
scripts_dir: "https://github.com/company/scripts/tree/v1.2.0/scripts"
```

### Access Control

- **Public repos**: Anyone can see and use scripts
- **Private repos**: Only authorized team members
- **Organization repos**: Controlled by organization membership

## Troubleshooting

### Common Issues

#### Repository Not Found

```
Error: Failed to fetch scripts from GitHub: 404
```

**Solutions**:
- Check repository exists and is public
- Verify URL format is correct
- Check network connectivity

#### Scripts Not Loading

```bash
# Clear cache and retry
runsh cache clean --all
runsh list
```

#### Network Issues

```bash
# Test GitHub API access
curl -I "https://api.github.com/repos/user/repo/contents/scripts"

# Check cache status
runsh cache info
```

#### Rate Limiting

GitHub API has rate limits (60 requests/hour for unauthenticated users).

**Solutions**:
- Use authentication (increases limit to 5000/hour)
- Use cache effectively (reduces API calls)
- Avoid frequent `cache clean --all`

### Debug Mode

```bash
# Enable verbose output
RUNSH_SHELL="bash -x" runsh deploy staging
```

## API Reference

### GitHub API Endpoints

RunSH uses these GitHub API endpoints:

```
GET https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}
```

Example:
```
GET https://api.github.com/repos/company/scripts/contents/scripts?ref=main
```

### Response Format

```json
[
  {
    "name": "deploy.sh",
    "path": "scripts/deploy.sh",
    "type": "file",
    "download_url": "https://raw.githubusercontent.com/company/scripts/main/scripts/deploy.sh"
  }
]
```

### Rate Limits

- **Unauthenticated**: 60 requests/hour
- **Authenticated**: 5000 requests/hour
- **Cached responses**: Don't count against limits

## Next Steps

- **[Cache Management](cache-management.md)** - Optimize performance and offline usage
- **[Examples](examples.md)** - Real-world GitHub integration examples
- **[Configuration](configuration.md)** - Advanced configuration options