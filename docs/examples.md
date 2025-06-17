---
version: 1.0.0
---


# Examples

Real-world RunSH usage examples for various scenarios and workflows.

## Table of Contents

- [Python Development](#python-development)
- [DevOps Automation](#devops-automation)  
- [Web Development](#web-development)
- [Database Management](#database-management)
- [Team Workflows](#team-workflows)
- [Personal Productivity](#personal-productivity)

## Python Development

### Package Publishing

```bash
#!/bin/bash
# scripts/publish.sh

# @description: Publish Python package to PyPI
# @arg version [optional]: Version to publish (auto-detect if not provided)
# @option test,t [flag]: Upload to TestPyPI instead of PyPI
# @option skip-build,s [flag]: Skip building, use existing dist files
# @option skip-tests [flag]: Skip running tests before publish

set -e

echo "=== Python Package Publishing ==="

# Run tests unless skipped
if [ "$SKIP_TESTS" != "1" ]; then
    echo "Running tests..."
    python -m pytest
    echo "✓ Tests passed"
fi

# Build package unless skipped
if [ "$SKIP_BUILD" != "1" ]; then
    echo "Building package..."
    rm -rf build/ dist/ *.egg-info/
    python -m build
    echo "✓ Build completed"
fi

# Validate package
echo "Validating package..."
twine check dist/*
echo "✓ Package validation passed"

# Upload
if [ "$TEST" = "1" ]; then
    echo "Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
    echo "✅ Published to TestPyPI"
else
    echo "Uploading to PyPI..."
    twine upload dist/*
    echo "✅ Published to PyPI"
fi
```

Usage:
```bash
runsh publish              # Publish to PyPI
runsh publish --test       # Test on TestPyPI first
runsh publish v1.2.0       # Publish specific version
runsh publish --skip-tests # Skip test run
```

### Environment Setup

```bash
#!/bin/bash
# scripts/setup-env.sh

# @description: Setup Python development environment
# @arg project_name: Name of the project
# @option python-version,p [default=3.11]: Python version to use
# @option venv-name,v: Virtual environment name (defaults to project name)
# @option install-deps,i [flag]: Install dependencies from requirements.txt

PROJECT_DIR="$PROJECT_NAME"
VENV_NAME="${VENV_NAME:-$PROJECT_NAME}"
PYTHON_VERSION="$PYTHON_VERSION"

echo "Setting up Python environment for $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create virtual environment
echo "Creating virtual environment with Python $PYTHON_VERSION"
python$PYTHON_VERSION -m venv "$VENV_NAME"
source "$VENV_NAME/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install dependencies if requested
if [ "$INSTALL_DEPS" = "1" ] && [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Environment setup complete"
echo "Activate with: source $VENV_NAME/bin/activate"
```

Usage:
```bash
runsh setup-env myproject --python-version 3.11
runsh setup-env webapp --install-deps
```

## DevOps Automation

### Docker Deployment

```bash
#!/bin/bash
# scripts/deploy.sh

# @description: Deploy application using Docker
# @arg environment: Target environment (dev/staging/prod)
# @arg service: Service name to deploy
# @option tag,t [default=latest]: Docker image tag
# @option replicas,r [default=1]: Number of replicas
# @option dry-run,d [flag]: Show what would be deployed
# @option force,f [flag]: Force deployment even with warnings

set -e

ENVIRONMENT="$ENVIRONMENT"
SERVICE="$SERVICE"
TAG="$TAG"
REPLICAS="$REPLICAS"

# Validate environment
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

# Build image name
IMAGE="mycompany/$SERVICE:$TAG"

echo "=== Docker Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "Service: $SERVICE"
echo "Image: $IMAGE"
echo "Replicas: $REPLICAS"

if [ "$DRY_RUN" = "1" ]; then
    echo "DRY RUN: Would execute:"
    echo "  docker service update --image $IMAGE --replicas $REPLICAS ${SERVICE}_${ENVIRONMENT}"
    exit 0
fi

# Check if image exists
if ! docker manifest inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Error: Image $IMAGE not found"
    exit 1
fi

# Deploy
echo "Deploying $SERVICE to $ENVIRONMENT..."
docker service update \
    --image "$IMAGE" \
    --replicas "$REPLICAS" \
    "${SERVICE}_${ENVIRONMENT}"

echo "✅ Deployment completed"

# Show status
docker service ps "${SERVICE}_${ENVIRONMENT}"
```

Usage:
```bash
runsh deploy prod api --tag v1.2.0 --replicas 3
runsh deploy staging web --dry-run
runsh deploy dev worker --force
```

### Infrastructure Provisioning

```bash
#!/bin/bash
# scripts/provision.sh

# @description: Provision cloud infrastructure with Terraform
# @arg stack: Infrastructure stack name
# @option workspace,w [default=default]: Terraform workspace
# @option auto-approve,y [flag]: Auto-approve changes
# @option destroy [flag]: Destroy infrastructure instead of creating
# @option var-file,f: Variables file path

set -e

STACK="$STACK"
WORKSPACE="$WORKSPACE"

echo "=== Infrastructure Provisioning ==="
echo "Stack: $STACK"
echo "Workspace: $WORKSPACE"

# Change to stack directory
cd "terraform/$STACK"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Select workspace
echo "Selecting workspace: $WORKSPACE"
terraform workspace select "$WORKSPACE" || terraform workspace new "$WORKSPACE"

# Plan
PLAN_ARGS=""
if [ -n "$VAR_FILE" ]; then
    PLAN_ARGS="-var-file=$VAR_FILE"
fi

if [ "$DESTROY" = "1" ]; then
    echo "Planning destroy..."
    terraform plan -destroy $PLAN_ARGS
    
    if [ "$AUTO_APPROVE" = "1" ]; then
        terraform destroy -auto-approve $PLAN_ARGS
    else
        read -p "Proceed with destroy? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            terraform destroy $PLAN_ARGS
        fi
    fi
else
    echo "Planning apply..."
    terraform plan $PLAN_ARGS
    
    if [ "$AUTO_APPROVE" = "1" ]; then
        terraform apply -auto-approve $PLAN_ARGS
    else
        read -p "Proceed with apply? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            terraform apply $PLAN_ARGS
        fi
    fi
fi

echo "✅ Provisioning completed"
```

Usage:
```bash
runsh provision database --workspace prod --auto-approve
runsh provision network --var-file prod.tfvars
runsh provision compute --destroy --workspace staging
```

## Web Development

### Build and Deploy

```bash
#!/bin/bash
# scripts/build-deploy.sh

# @description: Build and deploy web application
# @arg target: Deployment target (staging/prod)
# @option build-only,b [flag]: Only build, don't deploy
# @option skip-tests,s [flag]: Skip running tests
# @option clean,c [flag]: Clean build artifacts first

set -e

TARGET="$TARGET"
NODE_ENV=""

case "$TARGET" in
    staging)
        NODE_ENV="staging"
        ;;
    prod)
        NODE_ENV="production"
        ;;
    *)
        echo "Error: Invalid target '$TARGET'"
        echo "Valid targets: staging, prod"
        exit 1
        ;;
esac

echo "=== Web Application Build & Deploy ==="
echo "Target: $TARGET"
echo "Environment: $NODE_ENV"

# Clean if requested
if [ "$CLEAN" = "1" ]; then
    echo "Cleaning build artifacts..."
    rm -rf dist/ build/ .next/
fi

# Install dependencies
echo "Installing dependencies..."
npm ci

# Run tests unless skipped
if [ "$SKIP_TESTS" != "1" ]; then
    echo "Running tests..."
    npm test
    echo "✓ Tests passed"
fi

# Build application
echo "Building application..."
NODE_ENV="$NODE_ENV" npm run build
echo "✓ Build completed"

# Deploy if not build-only
if [ "$BUILD_ONLY" != "1" ]; then
    echo "Deploying to $TARGET..."
    
    case "$TARGET" in
        staging)
            aws s3 sync dist/ s3://myapp-staging --delete
            aws cloudfront create-invalidation --distribution-id E123456789 --paths "/*"
            ;;
        prod)
            aws s3 sync dist/ s3://myapp-production --delete
            aws cloudfront create-invalidation --distribution-id E987654321 --paths "/*"
            ;;
    esac
    
    echo "✅ Deployment completed"
    echo "URL: https://$TARGET.myapp.com"
else
    echo "✅ Build completed (deployment skipped)"
fi
```

Usage:
```bash
runsh build-deploy staging
runsh build-deploy prod --skip-tests
runsh build-deploy staging --build-only --clean
```

### Development Server

```bash
#!/bin/bash
# scripts/dev-server.sh

# @description: Start development server with various options
# @option port,p [default=3000]: Port to run server on
# @option host,h [default=localhost]: Host to bind to
# @option https,s [flag]: Enable HTTPS
# @option mock-api,m [flag]: Start with mock API server
# @option watch,w [flag]: Enable hot reloading

PORT="$PORT"
HOST="$HOST"

echo "=== Development Server ==="

# Start mock API if requested
if [ "$MOCK_API" = "1" ]; then
    echo "Starting mock API server..."
    json-server --watch db.json --port 3001 &
    MOCK_PID=$!
    echo "Mock API running on http://localhost:3001"
fi

# Prepare server command
SERVER_CMD="npm run dev"

# Add environment variables
export PORT="$PORT"
export HOST="$HOST"

if [ "$HTTPS" = "1" ]; then
    export HTTPS=true
    echo "Starting HTTPS development server..."
    echo "Server will be available at https://$HOST:$PORT"
else
    echo "Starting development server..."
    echo "Server will be available at http://$HOST:$PORT"
fi

# Start development server
$SERVER_CMD

# Cleanup mock API if it was started
if [ -n "$MOCK_PID" ]; then
    kill $MOCK_PID 2>/dev/null || true
fi
```

Usage:
```bash
runsh dev-server                    # Default settings
runsh dev-server --port 8080        # Custom port
runsh dev-server --https --mock-api # HTTPS with mock API
```

## Database Management

### Database Backup

```bash
#!/bin/bash
# scripts/backup-db.sh

# @description: Backup database with compression and S3 upload
# @arg database: Database name to backup
# @option host,h [default=localhost]: Database host
# @option user,u [default=postgres]: Database user
# @option compress,c [flag]: Compress backup file
# @option s3-upload,s [flag]: Upload to S3 after backup
# @option retention,r [default=7]: Days to retain backups

set -e

DATABASE="$DATABASE"
HOST="$HOST"
USER="$USER"
RETENTION="$RETENTION"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${DATABASE}_${TIMESTAMP}.sql"

echo "=== Database Backup ==="
echo "Database: $DATABASE"
echo "Host: $HOST"
echo "User: $USER"

# Create backup
echo "Creating backup..."
pg_dump -h "$HOST" -U "$USER" -d "$DATABASE" > "$BACKUP_FILE"
echo "✓ Backup created: $BACKUP_FILE"

# Compress if requested
if [ "$COMPRESS" = "1" ]; then
    echo "Compressing backup..."
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    echo "✓ Compressed: $BACKUP_FILE"
fi

# Upload to S3 if requested
if [ "$S3_UPLOAD" = "1" ]; then
    echo "Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://mycompany-backups/database/"
    echo "✓ Uploaded to S3"
    
    # Clean up old backups
    echo "Cleaning up old backups (retention: $RETENTION days)..."
    find . -name "${DATABASE}_*.sql*" -mtime +$RETENTION -delete
fi

echo "✅ Backup completed: $BACKUP_FILE"
```

Usage:
```bash
runsh backup-db myapp --compress --s3-upload
runsh backup-db analytics --host db-prod.company.com --retention 30
```

### Database Migration

```bash
#!/bin/bash
# scripts/migrate-db.sh

# @description: Run database migrations
# @arg direction [default=up]: Migration direction (up/down)
# @option target,t: Target migration version
# @option dry-run,d [flag]: Show what migrations would run
# @option force,f [flag]: Force migration even with warnings

set -e

DIRECTION="$DIRECTION"

echo "=== Database Migration ==="
echo "Direction: $DIRECTION"

# Validate direction
case "$DIRECTION" in
    up|down)
        ;;
    *)
        echo "Error: Invalid direction '$DIRECTION'"
        echo "Valid directions: up, down"
        exit 1
        ;;
esac

# Build migration command
MIGRATE_CMD="npx knex migrate:$DIRECTION"

if [ -n "$TARGET" ]; then
    MIGRATE_CMD="$MIGRATE_CMD --to $TARGET"
    echo "Target: $TARGET"
fi

if [ "$DRY_RUN" = "1" ]; then
    echo "DRY RUN: Would execute:"
    echo "  $MIGRATE_CMD"
    
    # Show pending migrations
    echo "Pending migrations:"
    npx knex migrate:status
    exit 0
fi

# Check for pending migrations
PENDING=$(npx knex migrate:status | grep -c "Not run" || echo "0")

if [ "$PENDING" -eq 0 ] && [ "$DIRECTION" = "up" ]; then
    echo "No pending migrations"
    exit 0
fi

if [ "$PENDING" -gt 5 ] && [ "$FORCE" != "1" ]; then
    echo "Warning: $PENDING pending migrations found"
    read -p "Proceed? (y/N): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Migration cancelled"
        exit 0
    fi
fi

# Run migration
echo "Running migration..."
$MIGRATE_CMD

echo "✅ Migration completed"
npx knex migrate:status
```

Usage:
```bash
runsh migrate-db up                 # Run all pending migrations
runsh migrate-db down --target 001  # Rollback to specific version
runsh migrate-db up --dry-run       # Preview migrations
```

## Team Workflows

### GitHub Repository Configuration

```yaml
# .runsh/config.yaml
scripts_dir: "https://github.com/company/devops-scripts/tree/main/scripts"
```

### Shared Scripts Repository

```
devops-scripts/
├── scripts/
│   ├── deploy.sh              # Application deployment
│   ├── backup.sh              # Database backup
│   ├── provision.sh           # Infrastructure provisioning
│   ├── release.sh             # Release management
│   └── monitor.sh             # System monitoring
├── docs/
│   └── scripts.md             # Script documentation
└── README.md                  # Team setup instructions
```

### Team Setup Script

```bash
#!/bin/bash
# scripts/team-setup.sh

# @description: Setup development environment for new team members
# @arg developer_name: Developer's name
# @option skip-tools,s [flag]: Skip installing development tools
# @option setup-aws,a [flag]: Setup AWS credentials

DEVELOPER="$DEVELOPER_NAME"

echo "=== Team Development Setup ==="
echo "Setting up environment for: $DEVELOPER"

# Create development directory
mkdir -p ~/dev
cd ~/dev

# Clone required repositories
echo "Cloning team repositories..."
repos=(
    "company/frontend-app"
    "company/backend-api"
    "company/shared-libs"
    "company/devops-scripts"
)

for repo in "${repos[@]}"; do
    if [ ! -d "$(basename $repo)" ]; then
        git clone "git@github.com:$repo.git"
    fi
done

# Install development tools unless skipped
if [ "$SKIP_TOOLS" != "1" ]; then
    echo "Installing development tools..."
    
    # Install Node.js (via nvm)
    if ! command -v nvm &> /dev/null; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        source ~/.bashrc
    fi
    
    nvm install --lts
    nvm use --lts
    
    # Install global packages
    npm install -g @commitlint/cli @commitlint/config-conventional
    
    echo "✓ Development tools installed"
fi

# Setup AWS credentials if requested
if [ "$SETUP_AWS" = "1" ]; then
    echo "Setting up AWS credentials..."
    aws configure
    echo "✓ AWS credentials configured"
fi

# Setup RunSH configuration
echo "Setting up RunSH..."
runsh config init

cat > .runsh/config.yaml << EOF
scripts_dir: "https://github.com/company/devops-scripts/tree/main/scripts"
default_shell: "bash"
EOF

echo "✅ Team setup completed for $DEVELOPER"
echo "Available commands:"
runsh list
```

Usage:
```bash
runsh team-setup "John Doe" --setup-aws
runsh team-setup "Jane Smith" --skip-tools
```

## Personal Productivity

### Git Workflow

```bash
#!/bin/bash
# scripts/git-feature.sh

# @description: Create and manage feature branches
# @arg action: Action to perform (start/finish/list)
# @arg feature_name [optional]: Feature name for start/finish actions
# @option base,b [default=main]: Base branch for new features
# @option push,p [flag]: Push branch to remote after creation

set -e

ACTION="$ACTION"
FEATURE="$FEATURE_NAME"
BASE="$BASE"

case "$ACTION" in
    start)
        if [ -z "$FEATURE" ]; then
            echo "Error: Feature name required for start action"
            exit 1
        fi
        
        BRANCH="feature/$FEATURE"
        
        echo "Starting feature: $FEATURE"
        echo "Base branch: $BASE"
        
        # Create and checkout feature branch
        git checkout "$BASE"
        git pull origin "$BASE"
        git checkout -b "$BRANCH"
        
        if [ "$PUSH" = "1" ]; then
            git push -u origin "$BRANCH"
            echo "✓ Branch pushed to remote"
        fi
        
        echo "✅ Feature branch created: $BRANCH"
        ;;
        
    finish)
        if [ -z "$FEATURE" ]; then
            echo "Error: Feature name required for finish action"
            exit 1
        fi
        
        BRANCH="feature/$FEATURE"
        
        echo "Finishing feature: $FEATURE"
        
        # Switch to base branch and merge
        git checkout "$BASE"
        git pull origin "$BASE"
        git merge --no-ff "$BRANCH"
        
        # Delete feature branch
        git branch -d "$BRANCH"
        git push origin --delete "$BRANCH" 2>/dev/null || true
        
        echo "✅ Feature merged and branch deleted"
        ;;
        
    list)
        echo "Feature branches:"
        git branch | grep "feature/" | sed 's/^..//'
        ;;
        
    *)
        echo "Error: Invalid action '$ACTION'"
        echo "Valid actions: start, finish, list"
        exit 1
        ;;
esac
```

Usage:
```bash
runsh git-feature start user-auth --push
runsh git-feature finish user-auth
runsh git-feature list
```

### Project Initialization

```bash
#!/bin/bash
# scripts/init-project.sh

# @description: Initialize new project with standard structure
# @arg project_name: Name of the project
# @arg project_type: Type of project (web/api/lib/cli)
# @option git,g [flag]: Initialize git repository
# @option private,p [flag]: Create private repository
# @option template,t: Template to use

PROJECT="$PROJECT_NAME"
TYPE="$PROJECT_TYPE"

echo "=== Project Initialization ==="
echo "Project: $PROJECT"
echo "Type: $TYPE"

# Create project directory
mkdir -p "$PROJECT"
cd "$PROJECT"

# Create basic structure based on type
case "$TYPE" in
    web)
        mkdir -p src components public docs
        echo "# $PROJECT" > README.md
        echo "node_modules\ndist\n.env" > .gitignore
        ;;
    api)
        mkdir -p src routes middleware tests docs
        echo "# $PROJECT API" > README.md
        echo "node_modules\n.env\nlogs" > .gitignore
        ;;
    lib)
        mkdir -p src tests docs examples
        echo "# $PROJECT Library" > README.md
        echo "node_modules\ndist\ncoverage" > .gitignore
        ;;
    cli)
        mkdir -p src bin tests docs
        echo "# $PROJECT CLI" > README.md
        echo "node_modules\ndist" > .gitignore
        ;;
    *)
        echo "Error: Invalid project type '$TYPE'"
        echo "Valid types: web, api, lib, cli"
        exit 1
        ;;
esac

# Initialize git if requested
if [ "$GIT" = "1" ]; then
    git init
    git add .
    git commit -m "Initial commit"
    echo "✓ Git repository initialized"
fi

echo "✅ Project $PROJECT ($TYPE) initialized"
echo "Next steps:"
echo "  cd $PROJECT"
echo "  # Add your code and dependencies"
```

Usage:
```bash
runsh init-project myapp web --git
runsh init-project mylib lib --private
runsh init-project mytool cli --template typescript
```

## Configuration Examples

### Multi-Environment Setup

```yaml
# .runsh/config.yaml for development
scripts_dir: "./scripts"
default_shell: "bash"
```

```yaml
# .runsh/config.yaml for production
scripts_dir: "https://github.com/company/prod-scripts/tree/main/scripts"
default_shell: "bash"
```

### Team-Specific Scripts

```yaml
# Frontend team
scripts_dir: "https://github.com/company/frontend-tools/tree/main/scripts"

# DevOps team  
scripts_dir: "https://github.com/company/devops-automation/tree/main/scripts"

# QA team
scripts_dir: "https://github.com/company/testing-tools/tree/main/scripts"
```

## Next Steps

- **[Getting Started](getting-started.md)** - Set up your first script
- **[Script Syntax](script-syntax.md)** - Learn the metadata format
- **[GitHub Integration](github-integration.md)** - Share scripts with your team
- **[Configuration](configuration.md)** - Customize RunSH for your workflow