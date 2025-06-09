# Cache Management

Understand and optimize RunSH's caching system for better performance and offline usage.

## Overview

RunSH automatically caches scripts from remote sources (like GitHub) to provide:

- **Fast execution** - No network delays after first download
- **Offline capability** - Work without internet connection
- **Reduced API calls** - Avoid GitHub rate limits
- **Reliability** - Scripts work even if remote source is temporarily unavailable

## How Caching Works

### Automatic Process

1. **First access**: Script downloaded from remote source
2. **Local storage**: Cached in `.runsh/cache/`
3. **Subsequent access**: Uses cached version (instant)
4. **Auto-refresh**: Cache expires after 24 hours
5. **Background update**: New version downloaded when cache expires

### Cache Structure

```
.runsh/
└── cache/
    ├── github_user_repo_main_scripts/
    │   ├── deploy.sh                    # Cached script
    │   ├── backup.sh                    # Cached script
    │   ├── monitor.sh                   # Cached script
    │   └── .metadata                    # Cache metadata
    └── github_company_tools_main_utils/
        ├── cleanup.sh
        └── .metadata
```

### Metadata Format

```json
{
  "url": "https://github.com/user/repo/tree/main/scripts",
  "api_url": "https://api.github.com/repos/user/repo/contents/scripts",
  "cached_at": "2024-01-15T10:30:00",
  "script_count": 3
}
```

## Cache Commands

### List Cached Scripts

```bash
runsh cache list
```

Output:
```
Found 2 cache entries:

  github_user_repo_main_scripts
    URL: https://github.com/user/repo/tree/main/scripts
    Scripts: 3
    Cached: 2024-01-15T10:30:00
    Status: valid

  github_company_tools_main_utils
    URL: https://github.com/company/tools/tree/main/utils
    Scripts: 5
    Cached: 2024-01-14T08:15:00
    Status: expired
```

### View Cache Information

```bash
runsh cache info
```

Output:
```
Cache Information:
  Location: /current/path/.runsh/cache
  Total entries: 2
  Valid entries: 1
  Expired entries: 1
  Total size: 45.2 KB
```

### Clean Expired Cache

```bash
runsh cache clean
```

Removes only expired cache entries (older than 24 hours).

### Clean All Cache

```bash
runsh cache clean --all
```

Removes all cache entries, forcing fresh downloads on next use.

## Cache Lifecycle

### Cache States

#### Valid Cache
- **Age**: Less than 24 hours old
- **Behavior**: Scripts execute immediately from cache
- **Network**: No API calls made

#### Expired Cache
- **Age**: More than 24 hours old
- **Behavior**: RunSH attempts to refresh from remote source
- **Fallback**: Uses expired cache if network unavailable

#### Missing Cache
- **State**: No cached version exists
- **Behavior**: Downloads from remote source
- **Fallback**: Error if network unavailable

### Refresh Process

When cache expires, RunSH:

1. **Attempts download** from remote source
2. **Updates cache** if successful
3. **Uses old cache** if download fails
4. **Shows warning** about stale cache

```bash
Warning: Using stale cache for github_user_repo_main_scripts
Last updated: 2 days ago
Try: runsh cache clean --all
```

## Performance Optimization

### Best Practices

#### For Frequent Use
```bash
# Keep cache fresh
runsh cache clean
runsh list  # Refreshes cache

# Check cache status regularly
runsh cache info
```

#### For Offline Work
```bash
# Pre-cache everything before going offline
runsh list  # Downloads all scripts
runsh cache info  # Verify all cached

# Work offline
# (network disconnected)
runsh deploy staging  # Works from cache
```

#### For Development
```bash
# Rapid testing with cache clearing
runsh cache clean --all
runsh deploy staging  # Fresh version

# Edit scripts remotely, then refresh
runsh cache clean --all
runsh deploy staging  # Updated version
```

### Cache Size Management

#### Monitor Size
```bash
runsh cache info  # Shows total cache size
```

#### Clean Periodically
```bash
# Weekly cleanup
runsh cache clean

# Monthly full cleanup
runsh cache clean --all
```

## Offline Usage

### Preparation

Before going offline, ensure scripts are cached:

```bash
# Download all available scripts
runsh list

# Verify cache status
runsh cache list

# Check for any expired entries
runsh cache info
```

### Offline Operations

All cached scripts work normally offline:

```bash
# These work offline (if cached)
runsh deploy staging
runsh backup database
runsh monitor --status

# This shows cached scripts only
runsh list
```

### Limitations When Offline

- **No cache refresh** - Expired cache won't update
- **No new scripts** - Can't discover newly added scripts
- **Stale versions** - May not have latest script versions

## Troubleshooting

### Cache Corruption

#### Symptoms
- Scripts fail to load
- Metadata errors
- Unexpected behavior

#### Solutions
```bash
# Clear all cache and start fresh
runsh cache clean --all
runsh list  # Re-download everything
```

### Network Issues

#### Symptoms
- Slow script loading
- Download failures
- Timeout errors

#### Solutions
```bash
# Use existing cache
runsh deploy staging  # Uses cache even if expired

# Check cache status
runsh cache list

# Manual refresh when network improves
runsh cache clean --all
```

### Disk Space Issues

#### Check Usage
```bash
runsh cache info
du -sh .runsh/cache/
```

#### Clean Up
```bash
# Remove expired entries
runsh cache clean

# Remove all cache
runsh cache clean --all

# Remove specific cache entry
rm -rf .runsh/cache/github_old_repo_main_scripts/
```

### Permission Issues

#### Symptoms
- Cannot write to cache
- Permission denied errors

#### Solutions
```bash
# Check permissions
ls -la .runsh/

# Fix permissions
chmod 755 .runsh/
chmod 755 .runsh/cache/
chmod 644 .runsh/cache/*/.metadata
```

## Advanced Configuration

### Cache Settings (Future Features)

```yaml
# .runsh/config.yaml (planned features)
cache:
  ttl_hours: 24           # Cache time-to-live
  max_size: "100MB"       # Maximum cache size
  auto_cleanup: true      # Auto-remove old entries
  offline_mode: false     # Never attempt downloads
```

### Environment Variables

```bash
# Force offline mode (use cache only)
export RUNSH_OFFLINE=1
runsh deploy staging

# Force online mode (always refresh)
export RUNSH_FORCE_REFRESH=1
runsh deploy staging
```

## Cache Directory Structure

### Detailed Layout

```
.runsh/
└── cache/
    ├── github_user_repo_main_scripts/          # Cache entry
    │   ├── deploy.sh                           # Cached script
    │   ├── backup.sh                           # Cached script
    │   └── .metadata                           # Entry metadata
    ├── github_company_tools_develop_utils/     # Different branch
    │   ├── cleanup.sh
    │   ├── monitor.sh
    │   └── .metadata
    └── github_team_devops_main_automation/     # Different repo
        ├── provision.sh
        ├── configure.sh
        └── .metadata
```

### Cache Entry Naming

Cache directories are named using this pattern:
```
github_{owner}_{repo}_{branch}_{path}
```

Examples:
- `github_user_repo_main_scripts`
- `github_company_tools_develop_utils`
- `github_team_devops_main_automation`

### Manual Cache Inspection

```bash
# List all cache entries
ls .runsh/cache/

# View cache metadata
cat .runsh/cache/github_user_repo_main_scripts/.metadata

# List cached scripts
ls .runsh/cache/github_user_repo_main_scripts/*.sh

# View cached script
cat .runsh/cache/github_user_repo_main_scripts/deploy.sh
```

## Performance Metrics

### Timing Comparison

#### Cold Start (No Cache)
```bash
time runsh deploy staging
# → 2.3 seconds (includes download)
```

#### Warm Start (With Cache)
```bash
time runsh deploy staging  
# → 0.1 seconds (cache only)
```

#### Cache Refresh
```bash
runsh cache clean --all
time runsh deploy staging
# → 1.8 seconds (download only new/changed scripts)
```

### Network Usage

- **Initial download**: ~2-5KB per script
- **Metadata check**: ~500 bytes per repository
- **Cache hit**: 0 bytes (fully offline)

## Best Practices

### For Teams

1. **Coordinate cache strategy**:
   ```bash
   # Team policy: refresh cache weekly
   runsh cache clean
   ```

2. **Document cache requirements**:
   ```markdown
   ## Setup
   1. Configure scripts: `runsh config init`
   2. Download scripts: `runsh list`
   3. Verify cache: `runsh cache info`
   ```

### For CI/CD

```bash
# In CI pipeline
runsh cache clean --all  # Always use fresh scripts
runsh deploy production
```

### For Development

```bash
# Local development workflow
runsh cache clean        # Refresh expired cache
runsh test-script        # Use updated scripts

# When testing script changes
runsh cache clean --all  # Force refresh
runsh test-script        # Test latest version
```

## Security Considerations

### Cache Validation

RunSH doesn't cryptographically verify cached scripts. For security:

1. **Use trusted sources** only
2. **Review scripts** before first use
3. **Monitor cache** for unexpected changes
4. **Use version control** for script repositories

### Cache Isolation

Each cache entry is isolated by:
- Repository owner/name
- Branch name  
- Directory path

This prevents cache pollution between different script sources.

## Next Steps

- **[GitHub Integration](github-integration.md)** - Set up remote script sources
- **[Configuration](configuration.md)** - Optimize cache settings
- **[Examples](examples.md)** - Real-world cache usage patterns