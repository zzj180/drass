#!/bin/bash

# ======================================================
# macOS Compatibility Functions
# ======================================================
# Provides cross-platform functions for macOS and Linux
# ======================================================

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Get available memory in GB
get_memory_gb() {
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        # macOS: Use vm_stat to get memory info
        local pages_free=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        local pages_inactive=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
        local pages_purgeable=$(vm_stat | grep "Pages purgeable" | awk '{print $3}' | sed 's/\.//')

        # Calculate available memory (pages * 4096 bytes per page)
        local total_pages=$((pages_free + pages_inactive + pages_purgeable))
        local available_gb=$(echo "scale=1; $total_pages * 4096 / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "N/A")
        echo "$available_gb"
    elif [[ "$os" == "linux" ]]; then
        # Linux: Use free command
        free -g | awk 'NR==2{printf "%.1f", $7/1024}'
    else
        echo "N/A"
    fi
}

# Kill process on port (cross-platform)
kill_port() {
    local port=$1
    local service_name=${2:-"service"}
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        # macOS: Use lsof to find and kill processes
        local pids=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pids" ]; then
            echo "Killing $service_name on port $port (PIDs: $pids)"
            echo "$pids" | xargs kill -9 2>/dev/null
            return 0
        fi
    elif [[ "$os" == "linux" ]]; then
        # Linux: Use fuser
        if fuser -k $port/tcp 2>/dev/null; then
            echo "Killed $service_name on port $port"
            return 0
        fi
    fi

    return 1
}

# Check if process is running (cross-platform)
check_process() {
    local process_name=$1
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        # macOS: Use pgrep
        pgrep -f "$process_name" > /dev/null 2>&1
    elif [[ "$os" == "linux" ]]; then
        # Linux: Use pidof or pgrep
        pidof "$process_name" > /dev/null 2>&1 || pgrep -f "$process_name" > /dev/null 2>&1
    else
        return 1
    fi
}

# Get process PID (cross-platform)
get_process_pid() {
    local process_name=$1
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        pgrep -f "$process_name" 2>/dev/null | head -1
    elif [[ "$os" == "linux" ]]; then
        pidof "$process_name" 2>/dev/null || pgrep -f "$process_name" 2>/dev/null | head -1
    else
        echo ""
    fi
}

# Check if port is in use (cross-platform)
check_port() {
    local port=$1
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
    elif [[ "$os" == "linux" ]]; then
        netstat -tuln 2>/dev/null | grep -q ":$port "
    else
        return 1
    fi
}

# Get disk space available (cross-platform)
get_disk_space_gb() {
    local path=${1:-.}
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        df -g "$path" | awk 'NR==2{print $4}'
    elif [[ "$os" == "linux" ]]; then
        df -BG "$path" | awk 'NR==2{print $4}' | sed 's/G//'
    else
        echo "N/A"
    fi
}

# Get CPU count (cross-platform)
get_cpu_count() {
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        sysctl -n hw.ncpu
    elif [[ "$os" == "linux" ]]; then
        nproc
    else
        echo "1"
    fi
}

# Get system uptime (cross-platform)
get_uptime() {
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        uptime | awk '{print $3" "$4}' | sed 's/,//'
    elif [[ "$os" == "linux" ]]; then
        uptime -p 2>/dev/null || uptime | awk '{print $3" "$4}' | sed 's/,//'
    else
        echo "unknown"
    fi
}

# Export functions for use in other scripts
export -f detect_os
export -f get_memory_gb
export -f kill_port
export -f check_process
export -f get_process_pid
export -f check_port
export -f get_disk_space_gb
export -f get_cpu_count
export -f get_uptime

# Test mode (if script is run directly)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "macOS Compatibility Utility Functions Test"
    echo "=========================================="
    echo "OS: $(detect_os)"
    echo "Available Memory: $(get_memory_gb) GB"
    echo "Available Disk: $(get_disk_space_gb) GB"
    echo "CPU Count: $(get_cpu_count)"
    echo "System Uptime: $(get_uptime)"
    echo ""
    echo "Port 8080 in use: $(check_port 8080 && echo 'Yes' || echo 'No')"
    echo ""
    echo "Functions exported successfully!"
fi