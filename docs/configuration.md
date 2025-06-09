# Configuration

Complete guide to configuring RunSH for your needs.

## Configuration Methods

RunSH supports multiple configuration methods with the following priority order:

1. **Environment Variables** (highest priority)
2. **Config File** (`.runsh/config.yaml`)
3. **Default Values** (lowest priority)

## Quick Setup

```bash
# Create configuration file
runsh config init

# Edit the generated file
nano .runsh/config.yaml
```

## Configuration File

### Location

RunSH looks for configuration files in this order:

1. `./.runsh/config.yaml` (current directory)
2. `../.runsh/config.yaml` (parent directory)
3. `../../.runsh/config.yaml` (grandparent directory)
4. `../../../.runsh/config.yaml` (great-grandparent directory)

This allows you to have project-specific or workspace-wide configurations.

### Basic Structure

```yaml
# .runsh/config.yaml
scripts_dir: "./scripts"
default_shell: "bash"
```

### All Options

```yaml
# Script source configuration
scripts_dir: "./scripts"              # Local directory
# scripts_dir: "https://github.com/user/repo/tree/main/scripts"  # GitHub repo

# Shell configuration  
default_shell: "bash"                 # bash, sh, or zsh

# Cache settings (future)
# cache_ttl: 24                       # Hours to keep cache
# auto_update: true                    # Auto-update remote scripts
```

## Environment Variables

Override any configuration with environment variables:

```bash
# Script source
export RUNSH_SCRIPTS_DIR="~/my-scripts"
export RUNSH_SCRIPTS_DIR="https://github.com/team/tools/tree/main/scripts"

# Shell preference
export RUNSH_SHELL="zsh"
```

### Temporary Override

```bash
# Use different scripts for one command
RUNSH_SCRIPTS_DIR="./build-scripts" runsh deploy

# Use different shell for one command  
RUNSH_SHELL="zsh" runsh deploy
```

## Scripts Directory Options

### Local Directory

```yaml
scripts_dir: "./scripts"              # Relative to current directory
scripts_dir: "/usr/local/scripts"     # Absolute path
scripts_dir: "~/scripts"              # Home directory relative
```

### GitHub Repository

```yaml
# Full GitHub URL
scripts_dir: "https://github.com/user/repo/tree/main/scripts"

# Different branches
scripts_dir: "https://github.com/user/repo/tree/develop/tools"

# Nested directories
scripts_dir: "https://github.com/user/repo/tree/main/deployment/scripts"
```

### Environment-Based Selection

```yaml
# Development
scripts_dir: "./scripts"

# Production (comment/uncomment as needed)
# scripts_dir: "https://github.com/company/prod-scripts/tree/main/scripts"
```

Or use environment variables:

```bash
# Development environment
export RUNSH_SCRIPTS_DIR="./dev-scripts"

# Production environment  
export RUNSH_SCRIPTS_DIR="https://github.com/company/prod-scripts/tree/main/scripts"
```

## Shell Configuration

### Supported Shells

- `bash` (default)
- `sh` 
- `zsh`

### Configuration

```yaml
default_shell: "bash"
```

### Per-Script Override

You can override the shell in individual scripts:

```bash
#!/bin/zsh
# @description: Script that requires zsh features

# Use zsh-specific features here
```

## Project Structure

### Single Project

```
my-project/
├── .runsh/
│   └── config.yaml           # Project-specific config
├── scripts/
│   ├── build.sh
│   └── deploy.sh
└── src/
```

### Workspace with Multiple Projects

```
workspace/
├── .runsh/
│   └── config.yaml           # Workspace-wide config
├── project-a/
│   └── scripts/
├── project-b/
│   └── scripts/
└── shared-scripts/
```

Configuration:
```yaml
# workspace/.runsh/config.yaml
scripts_dir: "./shared-scripts"
```

### Team Setup

```yaml
# .runsh/config.yaml (committed to git)
scripts_dir: "https://github.com/team/devops-tools/tree/main/scripts"
default_shell: "bash"
```

Each team member gets the same scripts automatically!

## Configuration Commands

### View Current Configuration

```bash
runsh config show
```

Output:
```
Current configuration:
  Scripts source: ./scripts
  Default shell: bash
  Source type: Local directory
  Config file: /current/path/.runsh/config.yaml
  Status: ✓ Available
```

### Initialize Configuration

```bash
runsh config init
```

Creates `.runsh/config.yaml` with sample configuration.

### Validate Configuration

```bash
runsh config show
```

Shows configuration status and any issues.

## Advanced Configuration

### Multiple Script Sources (Future Feature)

```yaml
# Future: Multiple script collections
script_collections:
  default:
    name: "Local Scripts"
    scripts_dir: "./scripts"
    
  devops:
    name: "DevOps Tools"
    scripts_dir: "https://github.com/team/devops/tree/main/scripts"
    
  build:
    name: "Build Tools"  
    scripts_dir: "https://github.com/team/build-tools/tree/main/scripts"

current_collection: "default"
```

### Cache Configuration (Future Feature)

```yaml
cache:
  ttl_hours: 24                # Cache expiry time
  auto_update: true            # Auto-update on expiry
  offline_mode: false          # Work offline only
```

## Configuration Examples

### Frontend Development Team

```yaml
# .runsh/config.yaml
scripts_dir: "https://github.com/frontend-team/scripts/tree/main/tools"
default_shell: "bash"
```

Scripts might include:
- `build.sh` - Build assets
- `deploy.sh` - Deploy to staging
- `test.sh` - Run tests

### DevOps Team

```yaml
# .runsh/config.yaml  
scripts_dir: "https://github.com/devops/automation/tree/main/scripts"
default_shell: "bash"
```

Scripts might include:
- `provision.sh` - Provision infrastructure
- `backup.sh` - Backup databases
- `monitor.sh` - Check system health

### Personal Development

```yaml
# .runsh/config.yaml
scripts_dir: "./scripts"
default_shell: "zsh"
```

Local scripts for personal workflow automation.

## Troubleshooting

### Configuration Not Found

```bash
runsh config show
```

If no config file is found, RunSH uses defaults:
- `scripts_dir: "./scripts"`
- `default_shell: "bash"`

### GitHub Repository Not Accessible

Check:
- Repository is public
- URL format is correct
- Network connectivity
- GitHub API limits

```bash
# Test GitHub access
curl -I "https://api.github.com/repos/user/repo/contents/scripts"
```

### Cache Issues

```bash
# Clear cache and retry
runsh cache clean --all
runsh list
```

### Permission Issues

```bash
# Check .runsh directory permissions
ls -la .runsh/

# Fix permissions if needed
chmod 755 .runsh/
chmod 644 .runsh/config.yaml
```

## Best Practices

### Team Collaboration

1. **Commit config file** to version control
2. **Use GitHub for shared scripts** 
3. **Document script collections** in README
4. **Version your script repositories**

### Security

1. **Never commit secrets** in config files
2. **Use environment variables** for sensitive data
3. **Review remote scripts** before use
4. **Pin to specific branches/tags** for stability

### Performance

1. **Use local scripts** for frequent operations
2. **Cache remote scripts** for offline work
3. **Clean cache regularly** to save space

## Next Steps

- **[GitHub Integration](github-integration.md)** - Detailed remote script setup
- **[Cache Management](cache-management.md)** - Optimize performance
- **[Examples](examples.md)** - Real-world configurations