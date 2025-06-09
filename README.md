# RunSH

Transform your shell scripts into powerful CLI tools with autocomplete, help messages, and argument validation.

## ✨ Features

- **🔧 Zero Configuration**: Add simple comments to your scripts
- **🌍 GitHub Integration**: Run scripts directly from GitHub repositories  
- **💾 Smart Caching**: Offline support with automatic cache management
- **🎯 Auto-completion**: Rich CLI experience with argument validation
- **📁 Organized**: All files managed in `.runsh/` directory

## 🚀 Quick Start

### Installation

```bash
pip install runsh
```

### Basic Usage

1. **Create a script** with metadata comments:

```bash
#!/bin/bash
# @description: Deploy application to production
# @arg environment: Target environment (staging/prod)
# @option verbose,v [flag]: Show detailed output
# @option dry-run,d [flag]: Preview changes without executing

echo "Deploying to $ENVIRONMENT..."
[ "$VERBOSE" = "1" ] && echo "Verbose mode enabled"
```

2. **Run with RunSH**:

```bash
# Auto-discovers scripts in ./scripts/
runsh deploy production --verbose

# Get help automatically
runsh deploy --help
```

### GitHub Integration

```bash
# Initialize configuration
runsh config init

# Edit .runsh/config.yaml
scripts_dir: "https://github.com/user/repo/tree/main/scripts"

# Use scripts from GitHub
runsh list
runsh deploy --help
```

## 📖 Documentation

- **[Getting Started](docs/getting-started.md)** - Detailed setup and first script
- **[Script Syntax](docs/script-syntax.md)** - Complete metadata reference  
- **[Configuration](docs/configuration.md)** - Settings and customization
- **[GitHub Integration](docs/github-integration.md)** - Remote script management
- **[Cache Management](docs/cache-management.md)** - Offline usage and performance
- **[Examples](docs/examples.md)** - Real-world script examples

## 🎯 Key Commands

```bash
# Script Management
runsh list                    # List available scripts
runsh <script-name> --help    # Get script help

# Configuration  
runsh config show             # Show current config
runsh config init             # Create config file

# Cache Management
runsh cache list              # List cached scripts
runsh cache clean             # Clean expired cache
runsh cache clean --all       # Clean all cache
```

## 📁 Project Structure

```
.runsh/
├── config.yaml              # Main configuration
└── cache/                    # GitHub script cache
    └── github_user_repo_main_scripts/
        ├── script1.sh
        └── .metadata
```

## 🔧 Script Metadata

Add these comments to your shell scripts:

```bash
# @description: Brief description of what the script does
# @arg name [optional] [default=value]: Argument description  
# @option name,short [flag]: Option description
# @option timeout [default=30]: Value option with default
```

**[→ Complete syntax reference](docs/script-syntax.md)**

## 🌍 Remote Scripts

```yaml
# .runsh/config.yaml
scripts_dir: "https://github.com/team/devops-scripts/tree/main/tools"
default_shell: "bash"
```

**[→ GitHub integration guide](docs/github-integration.md)**

## 📚 Examples

### Python Package Publishing

```bash
#!/bin/bash
# @description: Publish Python package to PyPI
# @option test,t [flag]: Upload to TestPyPI instead
# @option skip-build,s [flag]: Skip building step

# Build and publish logic here...
```

```bash
runsh publish-python --test  # Test on TestPyPI first
runsh publish-python         # Publish to PyPI
```

**[→ More examples](docs/examples.md)**

## 🛠️ Configuration

### Environment Variables

```bash
export RUNSH_SCRIPTS_DIR="~/my-scripts"
export RUNSH_SHELL="zsh"
```

### Config File

```yaml
# .runsh/config.yaml
scripts_dir: "./tools"        # Local directory
# scripts_dir: "https://github.com/user/repo/tree/main/scripts"  # GitHub
default_shell: "bash"
```

**[→ Full configuration options](docs/configuration.md)**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/user/runsh/issues)
- **PyPI**: [https://pypi.org/project/runsh/](https://pypi.org/project/runsh/)

---

**Transform your shell scripts into professional CLI tools! 🚀**