---
version: 1.0.0
---


# Getting Started

This guide will walk you through installing RunSH and creating your first script.

## Prerequisites

- Python 3.8 or higher
- Basic knowledge of shell scripting

## Installation

### From PyPI (Recommended)

```bash
pip install runsh
```

### From Source

```bash
git clone https://github.com/user/runsh.git
cd runsh
pip install -e .
```

### Verify Installation

```bash
runsh --help
```

You should see the RunSH command list.

## Your First Script

### Step 1: Create a Scripts Directory

```bash
mkdir scripts
cd scripts
```

### Step 2: Write a Simple Script

Create `scripts/hello.sh`:

```bash
#!/bin/bash

# @description: Say hello to someone
# @arg name: Person's name to greet
# @option loud,l [flag]: Print in uppercase

if [ "$LOUD" = "1" ]; then
    echo "HELLO, ${NAME^^}!"
else
    echo "Hello, $NAME!"
fi
```

### Step 3: Make It Executable

```bash
chmod +x scripts/hello.sh
```

### Step 4: Run with RunSH

```bash
# Go back to project root
cd ..

# List available scripts
runsh list

# Run the script
runsh hello "World"

# Use the flag option
runsh hello "World" --loud

# Get help
runsh hello --help
```

## Understanding the Output

When you run `runsh list`, you'll see:

```
Available commands:
  hello    Say hello to someone
  config   Manage runsh configuration
  cache    Manage script cache
```

The `hello` command was automatically created from your script!

## What Just Happened?

RunSH automatically:

1. **Discovered** your script in the `scripts/` directory
2. **Parsed** the metadata comments (`@description`, `@arg`, `@option`)
3. **Generated** a CLI command with proper argument validation
4. **Added** help documentation and autocompletion

## Script Metadata Explained

```bash
# @description: Say hello to someone
```
- Creates the command description shown in help

```bash
# @arg name: Person's name to greet
```
- Creates a required argument called `name`
- Sets `$NAME` variable in your script

```bash
# @option loud,l [flag]: Print in uppercase
```
- Creates a `--loud` option with `-l` shortcut
- Sets `$LOUD=1` when used, `$LOUD=0` otherwise

## Advanced First Script

Let's create something more useful - a git commit helper:

```bash
#!/bin/bash

# @description: Create a formatted git commit
# @arg message: Commit message
# @option type,t [default=feat]: Commit type (feat/fix/docs/style)
# @option scope,s: Commit scope (optional)
# @option breaking,b [flag]: Mark as breaking change

# Build commit message
COMMIT_MSG="$TYPE"

if [ -n "$SCOPE" ]; then
    COMMIT_MSG="$COMMIT_MSG($SCOPE)"
fi

if [ "$BREAKING" = "1" ]; then
    COMMIT_MSG="$COMMIT_MSG!"
fi

COMMIT_MSG="$COMMIT_MSG: $MESSAGE"

echo "Creating commit: $COMMIT_MSG"
git add .
git commit -m "$COMMIT_MSG"
```

Usage:
```bash
runsh git-commit "add new feature" --type feat --scope auth
# Creates: "feat(auth): add new feature"

runsh git-commit "remove deprecated API" --breaking
# Creates: "feat!: remove deprecated API"
```

## Next Steps

- **[Script Syntax](script-syntax.md)** - Learn all available metadata options
- **[Configuration](configuration.md)** - Customize RunSH behavior
- **[GitHub Integration](github-integration.md)** - Use scripts from GitHub
- **[Examples](examples.md)** - More real-world examples

## Troubleshooting

### Command Not Found

If `runsh` command is not found after installation:

```bash
# Check if it's in your PATH
pip show runsh

# Try running directly
python -m runsh
```

### Scripts Not Discovered

Make sure:
- Scripts are in `scripts/` directory (or configured path)
- Scripts have `.sh` extension
- Scripts have metadata comments
- Scripts are executable (`chmod +x`)

### Permission Denied

```bash
chmod +x scripts/*.sh
```

### Need Help?

- Check `runsh --help`
- Run `runsh <command> --help` for specific command help
- See [Configuration](configuration.md) for customization options