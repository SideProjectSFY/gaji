#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
CONTAINER_NAME="gaji-postgres"
DB_NAME="${DB_NAME:-gaji_db}"
DB_USER="${DB_USER:-gaji_user}"

# Load environment variables from .env.prod if it exists
ENV_FILE=".env.prod"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -f, --file <SQL_FILE>     Execute SQL from file"
    echo "  -c, --command <SQL>       Execute SQL command directly"
    echo "  -d, --run-dml             Execute all DML migration files in order"
    echo "  -i, --interactive         Open interactive psql session"
    echo "  -h, --help                Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -f migration.sql                    # Execute SQL from file"
    echo "  $0 -c \"SELECT * FROM users LIMIT 10;\"  # Execute SQL command"
    echo "  $0 -d                                  # Execute all DML migrations in order"
    echo "  $0 -i                                  # Interactive mode"
    exit 1
}

# Function to check if container is running
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}❌ Error: Container '${CONTAINER_NAME}' is not running${NC}"
        echo -e "${YELLOW}💡 Tip: Start the container with 'make prod' or 'docker compose up -d postgres'${NC}"
        exit 1
    fi
}

# Function to execute SQL file
exec_sql_file() {
    local sql_file=$1
    
    if [ ! -f "$sql_file" ]; then
        echo -e "${RED}❌ Error: File '$sql_file' not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}📄 Executing SQL from file: $sql_file${NC}"
    docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$sql_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SQL execution completed successfully${NC}"
    else
        echo -e "${RED}❌ SQL execution failed${NC}"
        exit 1
    fi
}

# Function to execute SQL command
exec_sql_command() {
    local sql_command=$1
    
    echo -e "${GREEN}🔍 Executing SQL command...${NC}"
    docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "$sql_command"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SQL execution completed successfully${NC}"
    else
        echo -e "${RED}❌ SQL execution failed${NC}"
        exit 1
    fi
}

# Function to execute all DML migrations in order
run_dml_migrations() {
    local dml_dir="gajiBE/src/main/resources/db/migration/dml"
    
    # Check if directory exists
    if [ ! -d "$dml_dir" ]; then
        echo -e "${RED}❌ Error: DML directory not found: $dml_dir${NC}"
        echo -e "${YELLOW}💡 Tip: Run this script from the project root directory${NC}"
        exit 1
    fi
    
    # Find all SQL files and sort them by version number
    local sql_files=$(find "$dml_dir" -name "V*.sql" -type f | sort -V)
    
    if [ -z "$sql_files" ]; then
        echo -e "${YELLOW}⚠️  No DML migration files found in $dml_dir${NC}"
        exit 0
    fi
    
    local total_files=$(echo "$sql_files" | wc -l | tr -d ' ')
    local current=0
    local success=0
    local failed=0
    
    echo -e "${GREEN}📦 Found $total_files DML migration file(s)${NC}"
    echo -e "${GREEN}🚀 Starting batch execution...${NC}"
    echo ""
    
    # Execute each file in order
    while IFS= read -r sql_file; do
        current=$((current + 1))
        local filename=$(basename "$sql_file")
        
        echo -e "${YELLOW}[$current/$total_files] Executing: $filename${NC}"
        
        if docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$sql_file" 2>&1; then
            echo -e "${GREEN}  ✅ Success${NC}"
            success=$((success + 1))
        else
            echo -e "${RED}  ❌ Failed${NC}"
            failed=$((failed + 1))
            
            # Ask user whether to continue or stop
            read -p "Continue with remaining files? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}⏸️  Execution stopped by user${NC}"
                break
            fi
        fi
        echo ""
    done <<< "$sql_files"
    
    # Summary
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📊 Execution Summary${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  Total files:    $total_files"
    echo -e "  ${GREEN}Success:        $success${NC}"
    if [ $failed -gt 0 ]; then
        echo -e "  ${RED}Failed:         $failed${NC}"
    else
        echo -e "  Failed:         $failed"
    fi
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ $failed -gt 0 ]; then
        exit 1
    fi
}

# Function to open interactive session
open_interactive() {
    echo -e "${GREEN}🔓 Opening interactive psql session...${NC}"
    echo -e "${YELLOW}📝 Tips:${NC}"
    echo -e "  - Type 'exit' or press Ctrl+D to exit"
    echo -e "  - Use \\dt to list tables"
    echo -e "  - Use \\d <table_name> to describe a table"
    echo -e "  - Use \\q to quit"
    echo ""
    docker exec -it "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"
}

# Main script
main() {
    # Check if container is running
    check_container
    
    # Parse arguments
    if [ $# -eq 0 ]; then
        usage
    fi
    
    case "$1" in
        -f|--file)
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Error: SQL file not specified${NC}"
                usage
            fi
            exec_sql_file "$2"
            ;;
        -c|--command)
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Error: SQL command not specified${NC}"
                usage
            fi
            exec_sql_command "$2"
            ;;
        -d|--run-dml)
            run_dml_migrations
            ;;
        -i|--interactive)
            open_interactive
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}❌ Error: Unknown option '$1'${NC}"
            usage
            ;;
    esac
}

main "$@"
