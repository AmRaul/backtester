#!/bin/bash
# Setup Automated Database Backups with Cron
# This script configures daily automated backups on the production server
# Usage: sudo ./setup-backup-cron.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup-db.sh"
LOG_DIR="/var/log/backtester"
LOG_FILE="$LOG_DIR/backup.log"

echo "🔧 Setting up automated database backups..."

# Check if running on server
if [ ! -f /opt/backtester/.env ]; then
    echo "⚠️  Warning: This script should be run on the production server at /opt/backtester/"
    read -p "Continue anyway? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ Error: backup-db.sh not found at $BACKUP_SCRIPT"
    exit 1
fi

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"
echo "✅ Made backup-db.sh executable"

# Create log directory
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"
echo "✅ Created log directory: $LOG_DIR"

# Create cron job
CRON_SCHEDULE="0 3 * * *"  # Every day at 3:00 AM
CRON_COMMAND="cd $SCRIPT_DIR && ./backup-db.sh prod >> $LOG_FILE 2>&1"
CRON_JOB="$CRON_SCHEDULE $CRON_COMMAND"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup-db.sh prod"; then
    echo "⚠️  Cron job already exists. Removing old version..."
    crontab -l 2>/dev/null | grep -v "backup-db.sh prod" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added:"
echo "   Schedule: Daily at 3:00 AM"
echo "   Command: $CRON_COMMAND"
echo "   Logs: $LOG_FILE"

# Create logrotate configuration
LOGROTATE_CONF="/etc/logrotate.d/backtester-backup"

if [ -w "/etc/logrotate.d" ]; then
    cat > "$LOGROTATE_CONF" <<EOF
$LOG_FILE {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
    echo "✅ Logrotate configured: $LOGROTATE_CONF"
else
    echo "⚠️  Cannot create logrotate config (need sudo)"
    echo "   Run manually: sudo bash -c 'cat > $LOGROTATE_CONF <<EOF
$LOG_FILE {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
EOF'"
fi

# Test backup script
echo ""
echo "🧪 Testing backup script..."
if $BACKUP_SCRIPT prod; then
    echo "✅ Test backup successful!"
else
    echo "❌ Test backup failed!"
    exit 1
fi

# Show current cron jobs
echo ""
echo "📋 Current cron jobs:"
crontab -l

# Show backup directory
echo ""
echo "📁 Backup directory:"
ls -lh "$SCRIPT_DIR/backups/" 2>/dev/null || echo "  No backups yet"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Next steps:"
echo "   1. Backups will run daily at 3:00 AM"
echo "   2. Logs available at: $LOG_FILE"
echo "   3. Backups stored in: $SCRIPT_DIR/backups/"
echo "   4. Last 10 backups are kept automatically"
echo ""
echo "🔍 Monitor backups:"
echo "   tail -f $LOG_FILE"
echo "   ls -lh $SCRIPT_DIR/backups/"
