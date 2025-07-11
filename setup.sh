#!/bin/bash

# Bylaw DB Development Setup Script
# This script sets up the development environment for the Bylaw DB project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="bylaw-db"
PYTHON_VERSION="3.11"
NODE_VERSION="18"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        local version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        
        if [[ $major -eq 3 && $minor -ge 11 ]]; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# Function to check Node.js version
check_node_version() {
    if command_exists node; then
        local version=$(node --version | cut -d'v' -f2 | cut -d. -f1)
        if [[ $version -ge 18 ]]; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# Function to install system dependencies on different platforms
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y \
                python3-pip python3-venv python3-dev \
                postgresql-client libpq-dev \
                curl wget git \
                build-essential
            
            # Install Node.js via NodeSource
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
            
        # CentOS/RHEL/Fedora
        elif command_exists yum; then
            sudo yum update -y
            sudo yum install -y \
                python3-pip python3-devel \
                postgresql-devel \
                curl wget git \
                gcc gcc-c++ make
            
            # Install Node.js
            curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
            sudo yum install -y nodejs
            
        elif command_exists dnf; then
            sudo dnf update -y
            sudo dnf install -y \
                python3-pip python3-devel \
                postgresql-devel \
                curl wget git \
                gcc gcc-c++ make
            
            # Install Node.js
            curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
            sudo dnf install -y nodejs
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            print_status "Installing dependencies via Homebrew..."
            brew update
            brew install python@3.11 postgresql node@18 git
            
            # Link Node.js if needed
            brew link node@18
        else
            print_error "Homebrew not found. Please install Homebrew first:"
            print_error "https://brew.sh/"
            exit 1
        fi
    else
        print_warning "Unsupported operating system. Please install dependencies manually."
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Python
    if ! check_python_version; then
        missing_deps+=("python3.11+")
    fi
    
    # Check Node.js
    if ! check_node_version; then
        missing_deps+=("node18+")
    fi
    
    # Check Docker
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    # Check Git
    if ! command_exists git; then
        missing_deps+=("git")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Attempting to install missing dependencies..."
        install_system_dependencies
        
        # Recheck after installation
        if ! check_python_version; then
            print_error "Python 3.11+ is still not available"
            exit 1
        fi
        
        if ! check_node_version; then
            print_error "Node.js 18+ is still not available"
            exit 1
        fi
        
        if ! command_exists docker; then
            print_error "Docker is still not available. Please install Docker manually:"
            print_error "https://docs.docker.com/get-docker/"
            exit 1
        fi
        
        if ! command_exists docker-compose; then
            print_error "Docker Compose is still not available. Please install Docker Compose manually:"
            print_error "https://docs.docker.com/compose/install/"
            exit 1
        fi
    fi
    
    print_success "All prerequisites are satisfied"
}

# Function to setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Created Python virtual environment"
    else
        print_warning "Python virtual environment already exists"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Python environment setup complete"
    cd ..
}

# Function to setup Node.js environment
setup_node_env() {
    print_status "Setting up Node.js environment..."
    
    cd frontend
    
    # Install dependencies
    npm install
    
    print_success "Node.js environment setup complete"
    cd ..
}

# Function to setup Docker environment
setup_docker_env() {
    print_status "Setting up Docker environment..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Build Docker images
    print_status "Building Docker images..."
    docker-compose build
    
    print_success "Docker environment setup complete"
}

# Function to setup environment files
setup_environment_files() {
    print_status "Setting up environment files..."
    
    # Copy environment templates
    if [ ! -f ".env" ]; then
        cp .env.template .env
        print_success "Created .env file"
        print_warning "Please configure your .env file with appropriate values"
    else
        print_warning ".env file already exists"
    fi
    
    if [ ! -f ".env.production" ]; then
        cp .env.production.template .env.production
        print_success "Created .env.production file"
        print_warning "Please configure your .env.production file for production deployment"
    else
        print_warning ".env.production file already exists"
    fi
}

# Function to setup Git hooks
setup_git_hooks() {
    print_status "Setting up Git hooks..."
    
    # Install pre-commit hooks
    cd backend
    source venv/bin/activate
    pip install pre-commit
    cd ..
    
    # Install hooks
    pre-commit install
    
    print_success "Git hooks setup complete"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Start database service
    docker-compose up -d database redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    cd backend
    source venv/bin/activate
    python ../database/migrate.py up
    
    # Seed with minimal data
    python ../database/seed.py --minimal
    
    print_success "Database setup complete"
    cd ..
}

# Function to run tests
run_tests() {
    print_status "Running tests to verify setup..."
    
    # Backend tests
    cd backend
    source venv/bin/activate
    python -m pytest tests/ -v --tb=short
    cd ..
    
    # Frontend tests
    cd frontend
    npm test -- --coverage --watchAll=false
    cd ..
    
    print_success "All tests passed"
}

# Function to show final instructions
show_final_instructions() {
    echo ""
    echo "================================================================="
    echo -e "${GREEN}Bylaw DB Development Environment Setup Complete!${NC}"
    echo "================================================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Configure your environment:"
    echo "   - Edit .env file with your database and API credentials"
    echo "   - Edit .env.production for production deployment"
    echo ""
    echo "2. Start the development environment:"
    echo "   make dev"
    echo ""
    echo "3. Access the application:"
    echo "   - Backend API: http://localhost:8000"
    echo "   - Frontend: http://localhost:3000"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo ""
    echo "4. Useful commands:"
    echo "   - make help           # Show all available commands"
    echo "   - make test           # Run all tests"
    echo "   - make lint           # Run code linting"
    echo "   - make db-seed        # Seed database with test data"
    echo "   - make logs           # View application logs"
    echo ""
    echo "5. Development workflow:"
    echo "   - Make changes to code"
    echo "   - Run 'make test' to verify changes"
    echo "   - Commit changes (pre-commit hooks will run automatically)"
    echo ""
    echo "For more information, see the README.md file."
    echo ""
}

# Function to handle cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Setup failed. Cleaning up..."
        docker-compose down >/dev/null 2>&1 || true
    fi
}

# Main setup function
main() {
    echo "================================================================="
    echo -e "${BLUE}Bylaw DB Development Environment Setup${NC}"
    echo "================================================================="
    echo ""
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Check if we're in the right directory
    if [ ! -f "Makefile" ] || [ ! -f "docker-compose.yml" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Parse command line arguments
    SKIP_TESTS=false
    SKIP_DOCKER=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-tests    Skip running tests after setup"
                echo "  --skip-docker   Skip Docker setup (use for local development only)"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run setup steps
    check_prerequisites
    setup_environment_files
    setup_python_env
    setup_node_env
    setup_git_hooks
    
    if [ "$SKIP_DOCKER" = false ]; then
        setup_docker_env
        setup_database
    fi
    
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi
    
    show_final_instructions
}

# Run main function
main "$@"