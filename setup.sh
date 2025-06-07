#!/bin/bash

# StatementSense Complete Setup Script
set -e

echo "🚀 StatementSense - Complete Setup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    print_success "All requirements are met"
}

# Setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -e .
    
    print_success "Backend setup completed"
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    # Install Node.js dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    cd ..
    print_success "Frontend setup completed"
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Initialize database
    source .venv/bin/activate
    python init_db.py
    
    print_success "Database setup completed"
}

# Start services with Docker Compose
start_services() {
    print_status "Starting services with Docker Compose..."
    
    # Build and start services
    docker-compose up --build -d
    
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check service health
    if docker-compose ps | grep -q "Up"; then
        print_success "All services are running"
    else
        print_error "Some services failed to start"
        docker-compose logs
        exit 1
    fi
}

# Setup Ollama and download model
setup_ollama() {
    print_status "Setting up Ollama LLM..."
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama service..."
    timeout 60 bash -c 'until docker-compose exec ollama ollama list; do sleep 2; done'
    
    # Download the model
    print_status "Downloading Llama 3.2 1B model (this may take a few minutes)..."
    docker-compose exec ollama ollama pull llama3.2:1b
    
    print_success "Ollama setup completed"
}

# Display final information
show_final_info() {
    print_success "🎉 StatementSense setup completed successfully!"
    echo ""
    echo "📋 Service URLs:"
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8000"
    echo "   API Docs:  http://localhost:8000/docs"
    echo "   Database:  localhost:5432"
    echo "   Ollama:    http://localhost:11434"
    echo ""
    echo "🔧 Useful commands:"
    echo "   Stop services:     docker-compose down"
    echo "   View logs:         docker-compose logs -f"
    echo "   Restart services:  docker-compose restart"
    echo "   Backend shell:     docker-compose exec backend bash"
    echo "   Frontend shell:    docker-compose exec frontend sh"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Open http://localhost:3000 in your browser"
    echo "   2. Upload a PDF bank statement"
    echo "   3. Process it to see the AI categorization in action"
    echo ""
    print_warning "Note: The first AI categorization may take longer as the model loads"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    docker-compose down
}

# Main setup function
main() {
    echo "Starting StatementSense setup..."
    echo ""
    
    # Ask user for setup type
    echo "Choose setup type:"
    echo "1) Full setup with Docker (recommended)"
    echo "2) Development setup (local Python + Node.js)"
    echo "3) Docker only (assumes dependencies are installed)"
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            print_status "Running full Docker setup..."
            check_docker
            start_services
            sleep 5
            setup_ollama
            show_final_info
            ;;
        2)
            print_status "Running development setup..."
            check_requirements
            setup_backend
            setup_frontend
            setup_database
            print_success "Development setup completed!"
            echo ""
            echo "To start the services:"
            echo "1. Backend: source .venv/bin/activate && uvicorn app.main:app --reload"
            echo "2. Frontend: cd frontend && npm run dev"
            echo "3. Start PostgreSQL and Ollama manually"
            ;;
        3)
            print_status "Running Docker-only setup..."
            check_docker
            start_services
            sleep 5
            setup_ollama
            show_final_info
            ;;
        *)
            print_error "Invalid choice. Please run the script again."
            exit 1
            ;;
    esac
}

# Set trap for cleanup on script exit
trap cleanup EXIT

# Run main function
main

print_success "Setup script completed! 🎉"