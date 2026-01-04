#!/bin/bash
# Emergency Database Schema Fix Script
# Restores backtester schema if it's missing after deployment
# Usage: ./fix-database-schema.sh [environment]
# Environment: local (default) or prod

set -e

ENV=${1:-local}

if [ "$ENV" = "local" ]; then
    CONTAINER_NAME="backtester_postgres"
    DB_USER="backtester"
    DB_NAME="backtester"
elif [ "$ENV" = "prod" ]; then
    CONTAINER_NAME="backtester_postgres_prod"
    DB_USER="${DB_USER:-amrahov}"
    DB_NAME="backtester"
else
    echo "❌ Invalid environment: $ENV"
    echo "Usage: $0 [local|prod]"
    exit 1
fi

echo "🔧 Emergency Database Schema Fix"
echo "   Environment: $ENV"
echo "   Container: $CONTAINER_NAME"
echo "   Database: $DB_NAME"
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container $CONTAINER_NAME is not running!"
    exit 1
fi

# Check if schema exists
echo "🔍 Checking if schema 'backtester' exists..."
SCHEMA_EXISTS=$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'backtester');" 2>/dev/null || echo "f")

if [ "$SCHEMA_EXISTS" = "t" ]; then
    echo "✅ Schema 'backtester' already exists"

    # Check tables count
    TABLE_COUNT=$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'backtester';" 2>/dev/null || echo "0")
    echo "📊 Found $TABLE_COUNT tables in schema 'backtester'"

    if [ "$TABLE_COUNT" -eq 0 ]; then
        echo "⚠️  Schema exists but no tables found. Applying init-db.sql..."
        docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < init-db.sql

        if [ $? -eq 0 ]; then
            echo "✅ Tables created successfully"
        else
            echo "❌ Failed to create tables"
            exit 1
        fi
    fi

    echo ""
    echo "✅ Database schema is OK!"
    exit 0
fi

echo "❌ Schema 'backtester' does NOT exist!"
echo "🔧 Attempting to fix..."
echo ""

# Try to restore from backup first
BACKUP_DIR="./backups"
if [ -d "$BACKUP_DIR" ]; then
    # Find last backup larger than 5KB (likely contains data)
    LAST_GOOD_BACKUP=$(find "$BACKUP_DIR" -name "*.sql.gz" -type f -size +5k -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

    if [ -n "$LAST_GOOD_BACKUP" ]; then
        BACKUP_SIZE=$(du -h "$LAST_GOOD_BACKUP" | cut -f1)
        echo "📦 Found backup: $(basename $LAST_GOOD_BACKUP) ($BACKUP_SIZE)"
        read -p "Restore from this backup? (yes/no): " CONFIRM

        if [ "$CONFIRM" = "yes" ]; then
            echo "⏳ Restoring from backup..."
            gunzip -c "$LAST_GOOD_BACKUP" | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME

            if [ $? -eq 0 ]; then
                echo "✅ Restore completed!"

                # Verify schema was created
                SCHEMA_EXISTS=$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'backtester');" 2>/dev/null || echo "f")

                if [ "$SCHEMA_EXISTS" = "t" ]; then
                    TABLE_COUNT=$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'backtester';" 2>/dev/null)
                    echo "✅ Schema restored with $TABLE_COUNT tables"
                    exit 0
                fi
            else
                echo "⚠️  Restore failed, trying manual schema creation..."
            fi
        fi
    fi
fi

# Manual schema creation as fallback
echo "🔧 Creating schema manually..."
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "CREATE SCHEMA IF NOT EXISTS backtester AUTHORIZATION $DB_USER;"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create schema"
    exit 1
fi

echo "✅ Schema created"
echo "📝 Applying init-db.sql..."

# Check if init-db.sql exists
if [ ! -f "init-db.sql" ]; then
    echo "❌ init-db.sql not found in current directory"
    exit 1
fi

# Apply init-db.sql
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < init-db.sql

if [ $? -ne 0 ]; then
    echo "❌ Failed to apply init-db.sql"
    exit 1
fi

# Verify
echo ""
echo "🔍 Verifying database..."
TABLE_COUNT=$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'backtester';" 2>/dev/null)
echo "📊 Created $TABLE_COUNT tables"

# Show tables
echo ""
echo "📋 Tables in schema 'backtester':"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\dt backtester.*"

echo ""
echo "✅ Database schema fixed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Check that all tables were created: \dt backtester.*"
echo "   2. If you had backtest results, they may need to be restored from backup"
echo "   3. Deploy with fixed GitHub Actions workflow to prevent this issue"
