#!/bin/bash

# PostgreSQL Test Data Generator Script
# This script creates comprehensive test data for MCP PostgreSQL Operations Server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Check if .env file exists and load it
if [ -f ".env" ]; then
    print_info "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    print_warning ".env file not found. Using default values."
fi

# Set default values if not provided
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-postgres}
# Always use postgres database for test data creation (required for CREATE DATABASE)
POSTGRES_DB=postgres

print_info "PostgreSQL connection details:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  User: $POSTGRES_USER"
echo "  Database: $POSTGRES_DB"
echo ""

# Check if PostgreSQL is accessible
print_info "Testing PostgreSQL connection..."
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" > /dev/null 2>&1; then
    print_error "Cannot connect to PostgreSQL server!"
    print_error "Please check your connection parameters and ensure PostgreSQL is running."
    exit 1
fi

print_success "PostgreSQL connection successful!"
echo ""

# Warning about destructive operations
print_warning "⚠️  WARNING: This script will create test databases and users!"
print_warning "⚠️  It may overwrite existing data if database names conflict."
print_warning ""
print_warning "The following databases will be created/replaced:"
print_warning "  - ecommerce"
print_warning "  - analytics"  
print_warning "  - inventory"
print_warning "  - hr_system"
print_warning ""
print_warning "The following users will be created:"
print_warning "  - app_readonly"
print_warning "  - app_readwrite"
print_warning "  - analytics_user"
print_warning "  - backup_user"
print_warning ""

# Ask for confirmation
read -p "Do you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Operation cancelled by user."
    exit 0
fi

# Run the SQL script
print_info "Executing test data generation script..."
print_info "This may take a few minutes depending on your system performance..."
echo ""

if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "scripts/create-test-data.sql"; then
    echo ""
    print_success "Test data generation completed successfully!"
    echo ""
    print_info "🎉 Your PostgreSQL server now has comprehensive test data!"
    echo ""
    print_info "Next steps:"
    echo "  1. Start your MCP server: ./scripts/run-mcp-inspector-local.sh"
    echo "  2. Test multi-database operations:"
    echo "     - get_database_list()"
    echo "     - get_table_list(database_name='ecommerce')"
    echo "     - get_pg_stat_statements_top_queries(limit=10)"
    echo "  3. Analyze performance and capacity:"
    echo "     - get_database_size_info()"
    echo "     - get_index_usage_stats(database_name='inventory')"
    echo "     - get_vacuum_analyze_stats(database_name='hr_system')"
    echo ""
    print_info "Test user credentials:"
    echo "  - app_readonly / readonly123"
    echo "  - app_readwrite / readwrite123" 
    echo "  - analytics_user / analytics123"
    echo "  - backup_user / backup123"
    echo ""
else
    echo ""
    print_error "Failed to execute test data generation script!"
    print_error "Please check the error messages above and try again."
    exit 1
fi
