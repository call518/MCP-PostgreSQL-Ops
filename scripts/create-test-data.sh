#!/bin/bash

# PostgreSQL Test Data Creation Script
# This script creates test data - assumes it's called only on first run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if PostgreSQL is ready
wait_for_postgres() {
    log_info "Waiting for PostgreSQL to be ready..."
    for i in $(seq 1 120); do
        if psql -h postgres -p ${POSTGRES_PORT} -U "${POSTGRES_USER}" -d postgres -c '\q' >/dev/null 2>&1; then
            log_success "PostgreSQL is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    log_error "PostgreSQL failed to start within 120 seconds"
    exit 1
}

# Check if sample databases already exist
check_existing_databases() {
    log_info "Checking if sample databases already exist..."
    
    # Check if ALL test databases exist (we need all 4)
    EXISTING_DBS=$(psql -h postgres -p ${POSTGRES_PORT} -U "${POSTGRES_USER}" -d postgres -t -c "
        SELECT COUNT(*) FROM pg_database 
        WHERE datname IN ('ecommerce', 'analytics', 'inventory', 'hr_system');
    " 2>/dev/null | xargs || echo "0")
    
    if [ "$EXISTING_DBS" -eq 4 ]; then
        log_warning "All sample databases already exist (found $EXISTING_DBS/4 databases)"
        log_info "Skipping test data creation - data already fully initialized"
        exit 0
    elif [ "$EXISTING_DBS" -gt 0 ]; then
        log_warning "Some sample databases exist (found $EXISTING_DBS/4 databases)"
        log_info "Proceeding with initialization to create missing databases"
    else
        log_info "No sample databases found - proceeding with full initialization"
    fi
    
    log_info "No sample databases found - proceeding with initialization"
}

# Install extensions
install_extensions() {
    log_info "Installing PostgreSQL extensions..."
    
    # Install extensions in postgres database
    psql -h postgres -p ${POSTGRES_PORT} -U "${POSTGRES_USER}" -d postgres -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" >/dev/null
    psql -h postgres -p ${POSTGRES_PORT} -U "${POSTGRES_USER}" -d postgres -c "CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;" >/dev/null
    
    # Install extensions in custom database if different from postgres
    if [[ "${POSTGRES_DB}" != "postgres" ]]; then
        psql -h postgres -p ${POSTGRES_PORT} -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;" >/dev/null 2>&1 || true
        psql -h postgres -p ${POSTGRES_PORT} -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;" >/dev/null 2>&1 || true
    fi
    
    log_success "Extensions installed successfully"
}

# Create test data
create_test_data() {
    log_info "Creating comprehensive test data..."
    
    if psql -h postgres -p ${POSTGRES_PORT} -U "${POSTGRES_USER}" -d postgres -f /scripts/create-test-data.sql; then
        log_success "Test data creation completed successfully!"
    else
        log_error "Failed to create test data!"
        exit 1
    fi
}

# Main execution
main() {
    log_info "Starting PostgreSQL test data initialization..."
    
    # Wait for PostgreSQL to be ready
    wait_for_postgres
    
    # Check if sample databases already exist (exit if they do)
    check_existing_databases
    
    # Install extensions and create test data
    install_extensions
    create_test_data
    
    log_success "Test data initialization completed successfully!"
}

# Execute main function
main "$@"
