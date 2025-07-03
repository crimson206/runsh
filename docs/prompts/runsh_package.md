# RunSH Package Creation Guide

## Overview

RunSH packages are collections of shell scripts wrapped with specific CLI interfaces, designed to create focused, purpose-driven tools from complex or diverse CLI operations. Each package transforms general-purpose tools into specific, user-friendly commands.

## Package Structure

```
my-runsh-package/
├── runsh.json          # Package metadata
├── scripts/            # Shell scripts with RunSH syntax
│   ├── deploy.sh
│   ├── backup.sh
│   └── monitor.sh
└── README.md           # Package documentation
```

## runsh.json Format

```json
{
  "name": "package-name",
  "version": "0.1.0",
  "description": "Brief description of what this package does",
  "author": "Your Name",
  "repository": "https://github.com/user/repo",
  "scripts": {
    "deploy": "Deploy application to specified environment",
    "backup": "Create database backup with compression",
    "monitor": "Monitor system resources and services"
  }
}
```

## RunSH Script Syntax

### Basic Template
```bash
#!/bin/bash

# @description: Brief description of what the script does
# @arg name [optional] [default=value]: Argument description
# @option name,short [flag] [default=value]: Option description

# Your script logic here
echo "Executing $SCRIPT_NAME with $ARGUMENT_NAME"
```

### Example: Deployment Script
```bash
#!/bin/bash

# @description: Deploy application to specified environment
# @arg environment: Target environment (dev/staging/prod)
# @arg version [optional]: Version to deploy
# @option config,c [default=config.yaml]: Configuration file
# @option dry-run,d [flag]: Preview changes without executing
# @option force,f [flag]: Force deployment even with warnings

echo "Deploying to: $ENVIRONMENT"
echo "Version: ${VERSION:-latest}"
echo "Config: $CONFIG"

if [ "$DRY_RUN" = "1" ]; then
    echo "DRY RUN MODE - No actual deployment"
    exit 0
fi

# Actual deployment logic here
echo "Starting deployment..."
```

## Package Creation Process

### 1. Define Package Purpose
- **Specific Goal**: What specific problem does this package solve?
- **Target Users**: Who will use this package?
- **Core Functions**: What are the main operations?

### 2. Identify CLI Tools to Wrap
- **Complex Commands**: Multi-step operations that can be simplified
- **Diverse Tools**: Different tools that work together for one purpose
- **Repetitive Tasks**: Commands that are used frequently with similar patterns

### 3. Create RunSH Scripts
- **Single Responsibility**: Each script should do one thing well
- **User-Friendly**: Clear descriptions and sensible defaults
- **Error Handling**: Graceful failure with helpful messages

## Example Packages

### DevOps Package
```json
{
  "name": "devops-tools",
  "version": "1.0.0",
  "description": "Streamlined DevOps operations for web applications",
  "scripts": {
    "deploy": "Deploy application with environment validation",
    "backup": "Create database and file backups",
    "monitor": "Check system health and performance",
    "rollback": "Rollback to previous deployment"
  }
}
```

### Data Processing Package
```json
{
  "name": "data-pipeline",
  "version": "0.2.0",
  "description": "Data processing and analysis workflows",
  "scripts": {
    "extract": "Extract data from various sources",
    "transform": "Transform and clean data",
    "load": "Load processed data to destination",
    "analyze": "Run data analysis and generate reports"
  }
}
```

## AI Assistant Prompt

When creating a RunSH package, provide the AI with:

```
I want to create a RunSH package for [specific purpose/domain].

My goals are:
- [Primary objective]
- [Secondary objectives]
- [Target users]

I currently use these tools/commands:
- [Tool 1]: [What it does]
- [Tool 2]: [What it does]
- [Tool 3]: [What it does]

Please help me create a RunSH package that:
1. Simplifies these operations
2. Provides clear, focused commands
3. Handles common use cases automatically
4. Includes proper error handling

Generate:
- runsh.json with appropriate metadata
- Shell scripts with RunSH syntax
- README.md with usage examples
```

## Package Installation

### Local Installation
```bash
# Clone or download package
git clone https://github.com/user/my-runsh-package
cd my-runsh-package

# Configure RunSH to use this package
echo "scripts_dir: './scripts'" > .runsh/config.yaml

# Use the package
runsh deploy prod --dry-run
runsh backup --compress
```

### GitHub Integration
```bash
# Configure RunSH to use GitHub repository
echo "scripts_dir: 'https://github.com/user/my-runsh-package/tree/main/scripts'" > .runsh/config.yaml

# Use the package
runsh list
runsh deploy --help
```

## Best Practices

### 1. Package Design
- **Focused Purpose**: Each package should solve one specific problem
- **Consistent Interface**: Use similar patterns across all scripts
- **Clear Naming**: Script names should be intuitive and memorable

### 2. Script Design
- **Descriptive Metadata**: Clear @description and argument descriptions
- **Sensible Defaults**: Provide useful default values for common cases
- **Error Messages**: Helpful error messages that guide users

### 3. Documentation
- **Usage Examples**: Show common use cases
- **Configuration**: Explain any required setup
- **Troubleshooting**: Common issues and solutions

## Common Patterns

### Environment Management
```bash
# @arg environment: Target environment
# @option config,c [default=config.yaml]: Environment config

case "$ENVIRONMENT" in
    dev|staging|prod)
        echo "Using environment: $ENVIRONMENT"
        ;;
    *)
        echo "Error: Invalid environment '$ENVIRONMENT'"
        echo "Valid options: dev, staging, prod"
        exit 1
        ;;
esac
```

### Conditional Execution
```bash
# @option dry-run,d [flag]: Preview changes
# @option force,f [flag]: Skip confirmations

if [ "$DRY_RUN" = "1" ]; then
    echo "DRY RUN: Would execute..."
    exit 0
fi

if [ "$FORCE" != "1" ]; then
    read -p "Continue? (y/N): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Aborted"
        exit 1
    fi
fi
```

## Next Steps

1. **Define Your Package**: What specific problem are you solving?
2. **Identify Tools**: What CLI tools can be simplified?
3. **Create Scripts**: Write RunSH scripts with clear metadata
4. **Test and Iterate**: Use the package and refine based on feedback
5. **Share**: Publish your package for others to use

---

**Transform complex CLI operations into simple, focused commands with RunSH packages!**
