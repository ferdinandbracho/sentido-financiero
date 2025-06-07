#!/bin/bash

# Deployment Verification Script
# This script tests that all services are running correctly

set -e

echo "🔍 StatementSense Deployment Verification"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if service is responding
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Function to check Docker service
check_docker_service() {
    local service_name=$1
    echo -n "Checking Docker service $service_name... "
    
    if docker-compose ps | grep -q "$service_name.*Up"; then
        echo -e "${GREEN}✅ Running${NC}"
        return 0
    else
        echo -e "${RED}❌ Not running${NC}"
        return 1
    fi
}

echo ""
echo "1. Checking Docker Services"
echo "------------------------"

SERVICES=("postgres" "ollama" "backend" "frontend")
for service in "${SERVICES[@]}"; do
    check_docker_service "$service"
done

echo ""
echo "2. Checking Service Health"
echo "------------------------"

# Wait a moment for services to be ready
sleep 5

# Check backend health
check_service "Backend API" "http://localhost:8000/" 200

# Check backend docs
check_service "API Documentation" "http://localhost:8000/docs" 200

# Check frontend
check_service "Frontend" "http://localhost:3000/" 200

# Check database connection
echo -n "Checking database connection... "
if docker-compose exec -T postgres pg_isready -U statement_user -d statement_sense > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# Check Ollama
echo -n "Checking Ollama service... "
if curl -s "http://localhost:11434/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Responding${NC}"
else
    echo -e "${RED}❌ Not responding${NC}"
fi

echo ""
echo "3. Checking AI Model"
echo "------------------"

echo -n "Checking if Llama model is downloaded... "
if docker-compose exec -T ollama ollama list | grep -q "llama3.2:1b"; then
    echo -e "${GREEN}✅ Model available${NC}"
else
    echo -e "${YELLOW}⚠️  Model not found${NC}"
    echo ""
    echo -e "${YELLOW}To download the model, run:${NC}"
    echo "docker-compose exec ollama ollama pull llama3.2:1b"
fi

echo ""
echo "4. Environment Check"
echo "------------------"

echo -n "Checking environment file... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${YELLOW}⚠️  Not found${NC}"
    echo "Consider copying .env.local or .env.docker to .env"
fi

echo -n "Checking uploads directory... "
if [ -d "uploads" ]; then
    echo -e "${GREEN}✅ Exists${NC}"
else
    echo -e "${YELLOW}⚠️  Creating...${NC}"
    mkdir -p uploads
    echo -e "${GREEN}✅ Created${NC}"
fi

echo ""
echo "5. Quick Functionality Test"
echo "-------------------------"

echo -n "Testing API root endpoint... "
if response=$(curl -s "http://localhost:8000/" 2>/dev/null); then
    if echo "$response" | grep -q "StatementSense"; then
        echo -e "${GREEN}✅ API responding correctly${NC}"
    else
        echo -e "${YELLOW}⚠️  API responding but unexpected content${NC}"
    fi
else
    echo -e "${RED}❌ API not responding${NC}"
fi

echo ""
echo "📋 Summary"
echo "========="

echo ""
echo "🌐 Service URLs:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   pgAdmin:      http://localhost:5050 (if enabled)"

echo ""
echo "🐳 Docker Commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Restart:      docker-compose restart"
echo "   Stop:         docker-compose down"
echo "   Rebuild:      docker-compose up --build"

echo ""
echo "🔧 Makefile Commands:"
echo "   Development:  make docker-dev"
echo "   Production:   make docker-prod"
echo "   Stop:         make docker-down"
echo "   Logs:         make docker-logs"

echo ""
echo "✅ Verification complete!"
echo ""
