---
version: 1.0.0
---


# Script Syntax Reference

Complete guide to RunSH metadata comments and variable handling.

## Overview

RunSH uses special comments in your shell scripts to generate CLI interfaces. These comments start with `# @` and define how your script should be called.

## Basic Structure

```bash
#!/bin/bash

# @description: Brief description of what the script does
# @arg argument_name [modifiers]: Description of the argument
# @option option_name,short [modifiers]: Description of the option

# USER SETTING
# Your custom configuration goes here

# Script logic here
echo "Hello, $ARGUMENT_NAME!"
```

## @description

Defines the command description shown in help and command listings.

### Syntax
```bash
# @description: Your description here
```

### Example
```bash
# @description: Deploy application to specified environment
```

**Result:** Shows "Deploy application to specified environment" in `runsh list` and `runsh deploy --help`

## @arg - Arguments

Defines positional arguments for your script.

### Syntax
```bash
# @arg name [modifiers]: Description
```

### Modifiers

- `[optional]` - Makes the argument optional
- `[default=value]` - Sets default value (implies optional)

### Examples

#### Required Argument
```bash
# @arg environment: Target environment (staging/prod)
```
- Usage: `runsh deploy production`
- Variable: `$ENVIRONMENT="production"`

#### Optional Argument
```bash
# @arg version [optional]: Version to deploy
```
- Usage: `runsh deploy production v1.2.0` or `runsh deploy production`
- Variable: `$VERSION="v1.2.0"` or `$VERSION=""`

#### Default Value
```bash
# @arg port [default=8080]: Port number to use
```
- Usage: `runsh serve` or `runsh serve 3000`
- Variable: `$PORT="8080"` or `$PORT="3000"`

### Variable Names

Arguments are converted to uppercase environment variables:
- `user_name` → `$USER_NAME`
- `api-key` → `$API_KEY`
- `file` → `$FILE`

## @option - Options

Defines named options (flags and values) for your script.

### Syntax
```bash
# @option name,short [modifiers]: Description
```

### Types

#### Flag Options
```bash
# @option verbose,v [flag]: Enable verbose output
```
- Usage: `runsh deploy --verbose` or `runsh deploy -v`
- Variable: `$VERBOSE="1"` (if used) or `$VERBOSE="0"` (if not used)

#### Value Options
```bash
# @option timeout,t [default=30]: Request timeout in seconds
```
- Usage: `runsh deploy --timeout 60` or `runsh deploy -t 60`
- Variable: `$TIMEOUT="60"` or `$TIMEOUT="30"` (default)

#### Required Value Options
```bash
# @option api-key: API key for authentication
```
- Usage: `runsh deploy --api-key abc123` (required)
- Variable: `$API_KEY="abc123"`

### Modifiers

- `[flag]` - Boolean flag option (no value needed)
- `[default=value]` - Value option with default
- No modifier - Required value option

### Shortcuts

- Single letter after comma: `verbose,v` → `-v` and `--verbose`
- If shortcut conflicts with RunSH built-ins, a warning is shown

### Built-in Options (Reserved)

These shortcuts are reserved by RunSH:
- `-h`, `--help` - Show help
- `-v`, `--verbose` - RunSH verbose mode
- `-q`, `--quiet` - RunSH quiet mode
- `-V`, `--version` - Show version

If your option conflicts, use a different shortcut or omit it.

## Complete Examples

### Deployment Script
```bash
#!/bin/bash

# @description: Deploy application with full configuration
# @arg environment: Target environment (dev/staging/prod)  
# @arg version [optional]: Version to deploy
# @option config,c [default=config.yaml]: Configuration file
# @option dry-run,d [flag]: Preview changes without executing
# @option force,f [flag]: Force deployment even with warnings
# @option timeout [default=300]: Deployment timeout in seconds

echo "Deploying to: $ENVIRONMENT"
echo "Version: ${VERSION:-latest}"
echo "Config: $CONFIG"
echo "Dry run: $DRY_RUN"
echo "Force: $FORCE"  
echo "Timeout: $TIMEOUT"
```

Usage examples:
```bash
runsh deploy prod v1.2.0
runsh deploy staging --dry-run
runsh deploy prod --force --timeout 600
runsh deploy dev --config custom.yaml -d
```

### File Processing Script
```bash
#!/bin/bash

# @description: Process files with various options
# @arg input_file: Input file path
# @arg output_file [optional]: Output file path
# @option format,f [default=json]: Output format (json/yaml/csv)
# @option verbose,v [flag]: Show detailed processing info
# @option overwrite [flag]: Overwrite output file if exists

INPUT="$INPUT_FILE"
OUTPUT="${OUTPUT_FILE:-processed_${INPUT}}"

echo "Processing $INPUT → $OUTPUT"
echo "Format: $FORMAT"
[ "$VERBOSE" = "1" ] && echo "Verbose mode enabled"
[ "$OVERWRITE" = "1" ] && echo "Will overwrite existing files"
```

## Variable Environment

### Automatic Variables

RunSH automatically sets these variables in your script:

- **Arguments**: Converted to uppercase with underscores
- **Options**: Converted to uppercase with underscores  
- **Flags**: Set to "1" if used, "0" if not used
- **Values**: Set to provided value or default

### Script-Runner Block (Auto-generated)

RunSH may add a block like this to handle variables:

```bash
# <SCRIPT-RUNNER>
VERBOSE=${CLI_VERBOSE:-0}
DRY_RUN=${CLI_DRY_RUN:-0}
ENVIRONMENT=${1:-.}
# </SCRIPT-RUNNER>
```

**Note**: This block is auto-generated and should not be edited manually.

## Best Practices

### Naming Conventions
```bash
# Good
# @arg file_path: Path to input file
# @option retry_count,r [default=3]: Number of retries

# Avoid
# @arg FilePath: Path to input file (inconsistent casing)
# @option retry-count-max: Max retries (too verbose)
```

### Descriptions
```bash
# Good
# @description: Backup database to S3 with compression
# @arg database_name: Name of database to backup
# @option compression,c [flag]: Enable gzip compression

# Too brief
# @description: Backup
# @arg db: Database

# Too verbose  
# @description: This script will backup the specified database to Amazon S3 with optional compression using gzip algorithm
```

### Default Values
```bash
# Good - sensible defaults
# @option timeout [default=30]: Request timeout
# @option retries [default=3]: Number of retry attempts

# Consider carefully
# @option api_key [default=secret]: API key (security risk!)
```

## Error Handling

### Invalid Syntax
If metadata syntax is invalid, RunSH will:
- Show a warning message
- Skip the invalid line
- Continue processing other metadata

### Conflicting Options
If option shortcuts conflict:
- RunSH shows a warning
- Removes the conflicting shortcut
- Long option name still works

### Missing Required Arguments
RunSH automatically validates:
- Required arguments are provided
- Required options have values
- Shows helpful error messages

## Advanced Features

### Complex Validation
For complex validation, use your script logic:

```bash
#!/bin/bash
# @description: Deploy with environment validation
# @arg environment: Target environment

case "$ENVIRONMENT" in
    dev|staging|prod)
        echo "Deploying to $ENVIRONMENT"
        ;;
    *)
        echo "Error: Invalid environment '$ENVIRONMENT'"
        echo "Valid options: dev, staging, prod"
        exit 1
        ;;
esac
```

### Dynamic Behavior
```bash
#!/bin/bash
# @description: Flexible build script
# @option target [default=all]: Build target
# @option parallel,p [flag]: Enable parallel build

JOBS=1
[ "$PARALLEL" = "1" ] && JOBS=$(nproc)

make -j$JOBS $TARGET
```

## Next Steps

- **[Configuration](configuration.md)** - Customize RunSH behavior
- **[GitHub Integration](github-integration.md)** - Use remote scripts
- **[Examples](examples.md)** - Real-world script examples