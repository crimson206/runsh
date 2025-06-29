# RunSH Script Writing Prompt

## Overview
RunSH transforms shell scripts into CLI tools using metadata comments. Add `# @` comments to your scripts for automatic CLI generation.

## Basic Syntax

```bash
#!/bin/bash

# @description: Brief description of what the script does
# @arg name [optional] [default=value]: Argument description
# @option name,short [flag] [default=value]: Option description

# Your script logic here
echo "Hello, $ARGUMENT_NAME!"
```

## Key Metadata

### @description
```bash
# @description: Deploy application to production
```

### @arg (Arguments)
```bash
# @arg environment: Target environment (staging/prod)
# @arg version [optional]: Version to deploy
# @arg port [default=8080]: Port number
```

### @option (Options)
```bash
# @option verbose,v [flag]: Enable verbose output
# @option timeout,t [default=30]: Request timeout
# @option config,c: Configuration file (required)
```

## Variable Names
- Arguments/options become uppercase environment variables
- `user_name` → `$USER_NAME`
- `api-key` → `$API_KEY`

## Usage Examples

### Simple Script
```bash
#!/bin/bash
# @description: Backup database
# @arg database: Database name
# @option compress,c [flag]: Enable compression

echo "Backing up $DATABASE"
[ "$COMPRESS" = "1" ] && echo "Compression enabled"
```

### Complex Script
```bash
#!/bin/bash
# @description: Deploy with full configuration
# @arg environment: Target environment
# @arg version [optional]: Version to deploy
# @option config,c [default=config.yaml]: Config file
# @option dry-run,d [flag]: Preview changes
# @option force,f [flag]: Force deployment

echo "Deploying $ENVIRONMENT"
echo "Version: ${VERSION:-latest}"
echo "Config: $CONFIG"
[ "$DRY_RUN" = "1" ] && echo "DRY RUN MODE"
```

## Best Practices

1. **Clear descriptions**: Be specific but concise
2. **Sensible defaults**: Use `[default=value]` for common cases
3. **Flag options**: Use `[flag]` for boolean switches
4. **Shortcuts**: Add single-letter shortcuts with comma
5. **Validation**: Handle invalid inputs in your script logic

## Reserved Options
Avoid these shortcuts (reserved by RunSH):
- `-h`, `--help`
- `-v`, `--verbose` 
- `-q`, `--quiet`
- `-V`, `--version`

## Result
Your script becomes a CLI command:
```bash
runsh backup mydb --compress
runsh deploy prod v1.2.0 --dry-run --force
```
