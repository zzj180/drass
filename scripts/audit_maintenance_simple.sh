#!/bin/bash

# Simple Audit Log Maintenance Script
# Provides easy-to-use commands for audit log maintenance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MAINTENANCE_SCRIPT="$SCRIPT_DIR/audit_maintenance.py"
LOG_FILE="$PROJECT_ROOT/logs/audit_maintenance.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

# Function to run maintenance command
run_maintenance() {
    local operation="$1"
    local dry_run="$2"
    local output_file="$3"
    
    print_status "Running audit maintenance: $operation"
    
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    # Build command
    local cmd="python3 $MAINTENANCE_SCRIPT --operation $operation"
    
    if [ "$dry_run" = "true" ]; then
        cmd="$cmd --dry-run"
    fi
    
    if [ -n "$output_file" ]; then
        cmd="$cmd --output $output_file"
    fi
    
    # Run command and capture output
    if eval "$cmd" 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Maintenance operation '$operation' completed successfully"
        return 0
    else
        print_error "Maintenance operation '$operation' failed"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Audit Log Maintenance Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  health              Run health check"
    echo "  backup [name]       Create backup (optional name)"
    echo "  restore <name>      Restore from backup"
    echo "  cleanup [--dry-run] Clean up old logs"
    echo "  optimize            Optimize database"
    echo "  full [--dry-run]    Run full maintenance cycle"
    echo "  list-backups        List all backups"
    echo "  stats               Show system statistics"
    echo "  monitor             Show monitoring dashboard"
    echo ""
    echo "Options:"
    echo "  --dry-run          Run in dry-run mode (no actual changes)"
    echo "  --output <file>    Save results to file"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 health"
    echo "  $0 backup my_backup"
    echo "  $0 cleanup --dry-run"
    echo "  $0 full --dry-run"
    echo "  $0 list-backups"
}

# Function to check if maintenance script exists
check_maintenance_script() {
    if [ ! -f "$MAINTENANCE_SCRIPT" ]; then
        print_error "Maintenance script not found: $MAINTENANCE_SCRIPT"
        exit 1
    fi
    
    if [ ! -x "$MAINTENANCE_SCRIPT" ]; then
        print_warning "Making maintenance script executable..."
        chmod +x "$MAINTENANCE_SCRIPT"
    fi
}

# Function to check Python dependencies
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    if ! python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT/services/main-app'); from app.services.audit_backup_service import audit_backup_service" 2>/dev/null; then
        print_error "Python dependencies not available. Please ensure the services are properly installed."
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Main script logic
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    # Parse arguments
    local command=""
    local dry_run="false"
    local output_file=""
    local backup_name=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --output)
                output_file="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            health|backup|restore|cleanup|optimize|full|list-backups|stats|monitor)
                command="$1"
                shift
                ;;
            *)
                # Assume it's a backup name or other parameter
                if [ -z "$backup_name" ] && [ "$command" = "backup" ]; then
                    backup_name="$1"
                elif [ -z "$backup_name" ] && [ "$command" = "restore" ]; then
                    backup_name="$1"
                else
                    print_error "Unknown argument: $1"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Validate command
    if [ -z "$command" ]; then
        print_error "No command specified"
        show_usage
        exit 1
    fi
    
    # Check prerequisites
    check_maintenance_script
    check_dependencies
    
    # Execute command
    case $command in
        health)
            run_maintenance "health" "$dry_run" "$output_file"
            ;;
        backup)
            if [ -n "$backup_name" ]; then
                print_status "Creating backup: $backup_name"
                cd "$PROJECT_ROOT"
                python3 "$MAINTENANCE_SCRIPT" --operation backup --backup-name "$backup_name" ${output_file:+--output "$output_file"} 2>&1 | tee -a "$LOG_FILE"
            else
                run_maintenance "backup" "$dry_run" "$output_file"
            fi
            ;;
        restore)
            if [ -z "$backup_name" ]; then
                print_error "Backup name required for restore operation"
                exit 1
            fi
            print_status "Restoring backup: $backup_name"
            cd "$PROJECT_ROOT"
            python3 "$MAINTENANCE_SCRIPT" --operation restore --backup-name "$backup_name" ${output_file:+--output "$output_file"} 2>&1 | tee -a "$LOG_FILE"
            ;;
        cleanup)
            run_maintenance "cleanup" "$dry_run" "$output_file"
            ;;
        optimize)
            run_maintenance "optimize" "$dry_run" "$output_file"
            ;;
        full)
            run_maintenance "full" "$dry_run" "$output_file"
            ;;
        list-backups)
            run_maintenance "list-backups" "$dry_run" "$output_file"
            ;;
        stats)
            run_maintenance "stats" "$dry_run" "$output_file"
            ;;
        monitor)
            print_status "Opening monitoring dashboard..."
            echo "Please access the monitoring dashboard at: http://localhost:5173/audit-logs"
            echo "Or use the API endpoint: http://localhost:8888/api/v1/audit-maintenance/monitoring/dashboard"
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
