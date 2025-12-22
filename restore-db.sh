#!/bin/bash
# Database Restore Script for Backtester PostgreSQL
# Usage: ./restore-db.sh <backup_file> [environment]
# Environment: local (default) or prod

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Backup file not specified"
    echo "Usage: $0 <backup_file.sql.gz> [local|prod]"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.sql.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"
ENV=${2:-local}

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [ "$ENV" = "local" ]; then
    CONTAINER_NAME="backtester_postgres"
    DB_USER="backtester"
    DB_NAME="backtester"
elif [ "$ENV" = "prod" ]; then
    CONTAINER_NAME="backtester_postgres_prod"
    DB_USER="${DB_USER:-backtester}"
    DB_NAME="backtester"
else
    echo "❌ Invalid environment: $ENV"
    echo "Usage: $0 <backup_file> [local|prod]"
    exit 1
fi

echo "⚠️  WARNING: This will OVERWRITE the current database!"
echo "   Environment: $ENV"
echo "   Container: $CONTAINER_NAME"
echo "   Database: $DB_NAME"
echo "   Backup: $BACKUP_FILE"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME is not running!"
    exit 1
fi

# Create safety backup before restore
SAFETY_BACKUP="backups/before_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
echo "🔒 Creating safety backup first..."
mkdir -p backups
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip > "$SAFETY_BACKUP"
echo "   ✅ Safety backup: $SAFETY_BACKUP"

# Decompress if needed
TEMP_FILE=""
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📦 Decompressing backup..."
    TEMP_FILE="/tmp/restore_$(date +%s).sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Perform restore
echo "⏳ Restoring database..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$RESTORE_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully!"

    # Cleanup temp file
    if [ -n "$TEMP_FILE" ]; then
        rm -f "$TEMP_FILE"
    fi

    echo ""
    echo "📊 Verifying restore..."
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "\dt backtester.*"
else
    echo "❌ Restore failed!"
    echo ""
    echo "⚠️  Your data is safe. Original state saved at: $SAFETY_BACKUP"
    echo "   You can restore it using: $0 $SAFETY_BACKUP $ENV"

    # Cleanup temp file
    if [ -n "$TEMP_FILE" ]; then
        rm -f "$TEMP_FILE"
    fi

    exit 1
fi
