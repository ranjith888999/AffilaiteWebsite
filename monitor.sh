#!/bin/bash

# Monitoring Script for Affiliate Website
# Checks application health and system resources

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Main monitoring function
monitor_system() {
    clear
    echo -e "${BLUE}🔍 Affiliate Website Monitoring Dashboard${NC}"
    echo "Last updated: $(date)"
    echo ""

    # Container status
    print_header "Container Status"
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(affiliate_app|affiliate_db|affiliate_nginx)"; then
        print_status "Containers are running"
    else
        print_error "Some containers are not running!"
    fi
    echo ""

    # Application health check
    print_header "Application Health"
    if curl -f -s http://localhost:80 > /dev/null 2>&1; then
        print_status "Application is responding"
        RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:80)
        echo "  Response time: ${RESPONSE_TIME}s"
    else
        print_error "Application is not responding!"
    fi
    echo ""

    # Database connectivity
    print_header "Database Status"
    if docker exec affiliate_db pg_isready -U affiliate_user > /dev/null 2>&1; then
        print_status "Database is ready"
        # Get database stats
        DB_CONNECTIONS=$(docker exec affiliate_db psql -U affiliate_user -d affiliate_website -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='affiliate_website';" 2>/dev/null | xargs || echo "N/A")
        echo "  Active connections: $DB_CONNECTIONS"
    else
        print_error "Database is not ready!"
    fi
    echo ""

    # System resources
    print_header "System Resources"
    
    # Memory usage
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
    if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
        print_error "Memory usage: ${MEM_USAGE}% (High!)"
    elif (( $(echo "$MEM_USAGE > 70" | bc -l) )); then
        print_warning "Memory usage: ${MEM_USAGE}% (Moderate)"
    else
        print_status "Memory usage: ${MEM_USAGE}%"
    fi

    # Disk usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        print_error "Disk usage: ${DISK_USAGE}% (High!)"
    elif [ "$DISK_USAGE" -gt 70 ]; then
        print_warning "Disk usage: ${DISK_USAGE}% (Moderate)"
    else
        print_status "Disk usage: ${DISK_USAGE}%"
    fi

    # Load average
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo "  Load average: $LOAD_AVG"
    echo ""

    # Docker stats
    print_header "Container Resources"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep -E "(affiliate_app|affiliate_db|affiliate_nginx|NAME)"
    echo ""

    # Recent logs
    print_header "Recent Application Logs (Last 5 lines)"
    docker logs affiliate_app --tail 5 2>/dev/null || echo "No recent logs available"
    echo ""

    # Log file sizes
    print_header "Log File Sizes"
    if [ -d "/var/log/affiliate-website" ]; then
        du -sh /var/log/affiliate-website/* 2>/dev/null || echo "No log files found"
    else
        echo "Log directory not found"
    fi
    echo ""

    # Network connectivity test
    print_header "External Connectivity"
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        print_status "Internet connectivity OK"
    else
        print_error "No internet connectivity!"
    fi

    if ping -c 1 api.cuelinks.com > /dev/null 2>&1; then
        print_status "Cuelinks API reachable"
    else
        print_warning "Cuelinks API unreachable"
    fi
    echo ""

    # Backup status
    print_header "Backup Status"
    if [ -d "/var/backups/affiliate-website" ]; then
        LAST_BACKUP=$(ls -t /var/backups/affiliate-website/*.sql.gz 2>/dev/null | head -1)
        if [ -n "$LAST_BACKUP" ]; then
            BACKUP_DATE=$(stat -c %y "$LAST_BACKUP" | cut -d' ' -f1)
            print_status "Last backup: $BACKUP_DATE"
        else
            print_warning "No database backups found"
        fi
    else
        print_warning "Backup directory not found"
    fi
}

# SSL certificate check
check_ssl() {
    print_header "SSL Certificate Status"
    if [ -f "./ssl/fullchain.pem" ]; then
        EXPIRY=$(openssl x509 -enddate -noout -in ./ssl/fullchain.pem | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
        
        if [ $DAYS_LEFT -lt 7 ]; then
            print_error "SSL certificate expires in $DAYS_LEFT days!"
        elif [ $DAYS_LEFT -lt 30 ]; then
            print_warning "SSL certificate expires in $DAYS_LEFT days"
        else
            print_status "SSL certificate valid for $DAYS_LEFT days"
        fi
    else
        print_warning "No SSL certificate found"
    fi
    echo ""
}

# Performance test
performance_test() {
    print_header "Performance Test"
    echo "Testing application response times..."
    
    for i in {1..5}; do
        RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:80 2>/dev/null || echo "0")
        echo "  Test $i: ${RESPONSE_TIME}s"
    done
    echo ""
}

# Main execution
case "$1" in
    "ssl")
        check_ssl
        ;;
    "perf")
        performance_test
        ;;
    "watch")
        while true; do
            monitor_system
            echo "Press Ctrl+C to stop monitoring..."
            sleep 30
        done
        ;;
    *)
        monitor_system
        echo ""
        echo "Available options:"
        echo "  ./monitor.sh        - Run monitoring once"
        echo "  ./monitor.sh watch  - Continuous monitoring"
        echo "  ./monitor.sh ssl    - Check SSL certificate"
        echo "  ./monitor.sh perf   - Performance test"
        ;;
esac
