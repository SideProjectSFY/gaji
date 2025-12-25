#!/bin/bash
# daily_pg_report.sh

DATE=$(date +%Y-%m-%d)
LOG_DIR="./logs/monitoring"
mkdir -p $LOG_DIR
REPORT_FILE="$LOG_DIR/daily_report_${DATE}.txt"

# Use docker exec to run psql inside the container
# Assumes container name is gaji-postgres and user is gaji_user and db is gaji_db
CONTAINER_NAME="gaji-postgres"
DB_USER="gaji_user"
DB_NAME="gaji_db"

echo "Generating PostgreSQL report from container $CONTAINER_NAME..."

docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME << EOF > $REPORT_FILE
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'PostgreSQL Daily Performance Report'
\echo 'Generated at: $(date)'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo ''

\echo '1. Slow Queries TOP 5'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
SELECT 
    calls,
    mean_exec_time::numeric(10,2) as avg_time_ms,
    LEFT(query, 100) as query_preview
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 5;

\echo ''
\echo '2. Cache Hit Ratio'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
SELECT 
    ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_ratio
FROM pg_stat_database
WHERE datname = current_database();

\echo ''
\echo '3. Database Size'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
SELECT pg_size_pretty(pg_database_size(current_database()));

\echo ''
\echo '4. Connections'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
SELECT COUNT(*) as total_connections,
       COUNT(CASE WHEN state = 'active' THEN 1 END) as active,
       COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle
FROM pg_stat_activity;

\echo ''
\echo '5. Tables with many Dead Tuples (Need VACUUM)'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
SELECT 
    schemaname || '.' || tablename as table_name,
    n_dead_tup as dead_tuples,
    last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 5;

EOF

if [ -f "$REPORT_FILE" ]; then
    echo "Report generated: $REPORT_FILE"
    # Delete reports older than 7 days
    find $LOG_DIR -name "daily_report_*.txt" -mtime +7 -delete
fi
