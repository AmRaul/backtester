#!/bin/bash
# Backup Monitoring Script
# Checks if recent backups exist and sends alerts if needed
# Usage: ./check-backups.sh [environment]
# Environment: local (default) or prod

set -e

ENV=${1:-prod}
BACKUP_DIR="./backups"
ALERT_THRESHOLD_HOURS=24  # Alert if no backup in last 24 hours
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID}"

echo "🔍 Checking backup status..."
echo "   Environment: $ENV"
echo "   Directory: $BACKUP_DIR"
echo "   Alert threshold: ${ALERT_THRESHOLD_HOURS}h"

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# Find latest backup for environment
LATEST_BACKUP=$(find "$BACKUP_DIR" -name "backup_${ENV}_*.sql.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

if [ -z "$LATEST_BACKUP" ]; then
    MESSAGE="❌ ERROR: No backups found for environment '$ENV'"
    STATUS="CRITICAL"
else
    # Get backup age
    BACKUP_TIMESTAMP=$(stat -c %Y "$LATEST_BACKUP" 2>/dev/null || stat -f %m "$LATEST_BACKUP")
    CURRENT_TIMESTAMP=$(date +%s)
    AGE_SECONDS=$((CURRENT_TIMESTAMP - BACKUP_TIMESTAMP))
    AGE_HOURS=$((AGE_SECONDS / 3600))
    AGE_MINUTES=$(((AGE_SECONDS % 3600) / 60))

    BACKUP_NAME=$(basename "$LATEST_BACKUP")
    BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
    BACKUP_DATE=$(date -r "$LATEST_BACKUP" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -d "@$BACKUP_TIMESTAMP" "+%Y-%m-%d %H:%M:%S")

    echo ""
    echo "📊 Latest Backup:"
    echo "   File: $BACKUP_NAME"
    echo "   Size: $BACKUP_SIZE"
    echo "   Date: $BACKUP_DATE"
    echo "   Age: ${AGE_HOURS}h ${AGE_MINUTES}m"

    # Check if backup is too old
    if [ $AGE_HOURS -gt $ALERT_THRESHOLD_HOURS ]; then
        MESSAGE="⚠️ WARNING: Latest backup for '$ENV' is ${AGE_HOURS}h old (threshold: ${ALERT_THRESHOLD_HOURS}h)
File: $BACKUP_NAME
Size: $BACKUP_SIZE
Date: $BACKUP_DATE"
        STATUS="WARNING"
    else
        MESSAGE="✅ Backup status OK for '$ENV'
Latest: $BACKUP_NAME ($BACKUP_SIZE)
Age: ${AGE_HOURS}h ${AGE_MINUTES}m
Date: $BACKUP_DATE"
        STATUS="OK"
    fi
fi

# Count total backups
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "backup_${ENV}_*.sql.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

echo ""
echo "📈 Statistics:"
echo "   Total backups ($ENV): $TOTAL_BACKUPS"
echo "   Total size: $TOTAL_SIZE"

MESSAGE="$MESSAGE

Total backups: $TOTAL_BACKUPS
Directory size: $TOTAL_SIZE"

# Check cloud backups if configured
if command -v aws &> /dev/null && [ -n "$BACKUP_S3_BUCKET" ]; then
    echo ""
    echo "☁️  Checking S3 backups..."
    S3_BUCKET="${BACKUP_S3_BUCKET}"
    S3_PREFIX="${S3_PREFIX:-database-backups}"

    S3_COUNT=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" 2>/dev/null | wc -l || echo "0")
    if [ "$S3_COUNT" -gt 0 ]; then
        echo "   S3 backups: $S3_COUNT files"
        MESSAGE="$MESSAGE
S3 backups: $S3_COUNT files"
    else
        echo "   ⚠️  No S3 backups found"
        MESSAGE="$MESSAGE
⚠️ No S3 backups found"
    fi
fi

# Send Telegram notification if configured
send_telegram_alert() {
    local message="$1"
    local status="$2"

    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
        echo "⚠️  Telegram not configured (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required)"
        return 0
    fi

    # Add emoji based on status
    case "$status" in
        OK)
            EMOJI="✅"
            ;;
        WARNING)
            EMOJI="⚠️"
            ;;
        CRITICAL)
            EMOJI="❌"
            ;;
        *)
            EMOJI="ℹ️"
            ;;
    esac

    FULL_MESSAGE="$EMOJI Backtester Backup Monitor

$message

Server: $(hostname)
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        -d text="$FULL_MESSAGE" \
        -d parse_mode="HTML" > /dev/null

    if [ $? -eq 0 ]; then
        echo "✅ Telegram notification sent"
    else
        echo "❌ Failed to send Telegram notification"
    fi
}

# Send alert only for WARNING or CRITICAL
if [ "$STATUS" != "OK" ]; then
    echo ""
    echo "📨 Sending alert..."
    send_telegram_alert "$MESSAGE" "$STATUS"
fi

# Print final status
echo ""
case "$STATUS" in
    OK)
        echo "✅ Status: $STATUS"
        exit 0
        ;;
    WARNING)
        echo "⚠️  Status: $STATUS"
        exit 1
        ;;
    CRITICAL)
        echo "❌ Status: $STATUS"
        exit 2
        ;;
esac
