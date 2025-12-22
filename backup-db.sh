#!/bin/bash
# Database Backup Script for Backtester PostgreSQL
# Usage: ./backup-db.sh [environment]
# Environment: local (default) or prod

set -e

ENV=${1:-local}
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

if [ "$ENV" = "local" ]; then
    CONTAINER_NAME="backtester_postgres"
    DB_USER="backtester"
    DB_NAME="backtester"
    BACKUP_FILE="$BACKUP_DIR/backup_local_${TIMESTAMP}.sql"
elif [ "$ENV" = "prod" ]; then
    CONTAINER_NAME="backtester_postgres_prod"
    DB_USER="${DB_USER:-backtester}"
    DB_NAME="backtester"
    BACKUP_FILE="$BACKUP_DIR/backup_prod_${TIMESTAMP}.sql"
else
    echo "❌ Invalid environment: $ENV"
    echo "Usage: $0 [local|prod]"
    exit 1
fi

echo "🗄️  Starting database backup..."
echo "   Environment: $ENV"
echo "   Container: $CONTAINER_NAME"
echo "   Database: $DB_NAME"
echo "   Output: $BACKUP_FILE"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME is not running!"
    exit 1
fi

# Perform backup
echo "⏳ Creating backup..."
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup completed successfully!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $FILE_SIZE"

    # Compress backup
    echo "📦 Compressing backup..."
    gzip "$BACKUP_FILE"
    COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "✅ Compressed to ${BACKUP_FILE}.gz ($COMPRESSED_SIZE)"

    # Keep only last 10 backups
    echo "🧹 Cleaning old backups (keeping last 10)..."
    ls -t "$BACKUP_DIR"/backup_${ENV}_*.sql.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/backup_${ENV}_*.sql.gz 2>/dev/null | wc -l)
    echo "📊 Total backups for $ENV: $BACKUP_COUNT"
else
    echo "❌ Backup failed!"
    rm -f "$BACKUP_FILE" 2>/dev/null
    exit 1
fi
