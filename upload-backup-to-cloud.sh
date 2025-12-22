#!/bin/bash
# Upload Database Backup to Cloud Storage
# Supports: AWS S3, Google Cloud Storage
# Usage: ./upload-backup-to-cloud.sh <backup_file> [provider]
# Provider: s3 (default) or gcs

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Backup file not specified"
    echo "Usage: $0 <backup_file> [s3|gcs]"
    echo ""
    echo "Examples:"
    echo "  $0 backups/backup_prod_20241221_120000.sql.gz s3"
    echo "  $0 backups/backup_prod_20241221_120000.sql.gz gcs"
    exit 1
fi

BACKUP_FILE="$1"
PROVIDER="${2:-s3}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

BACKUP_NAME=$(basename "$BACKUP_FILE")
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "☁️  Uploading backup to cloud storage..."
echo "   File: $BACKUP_NAME"
echo "   Size: $FILE_SIZE"
echo "   Provider: $PROVIDER"

# =============================================================================
# AWS S3 Upload
# =============================================================================
upload_to_s3() {
    # Configuration from environment variables
    S3_BUCKET="${BACKUP_S3_BUCKET:-backtester-backups}"
    S3_REGION="${AWS_REGION:-us-east-1}"
    S3_STORAGE_CLASS="${S3_STORAGE_CLASS:-STANDARD_IA}"  # Cheaper for backups
    S3_PREFIX="${S3_PREFIX:-database-backups}"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo "❌ AWS CLI not installed"
        echo "   Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi

    # Check credentials
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "❌ AWS credentials not configured"
        echo "   Set: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        exit 1
    fi

    S3_PATH="s3://$S3_BUCKET/$S3_PREFIX/$BACKUP_NAME"

    echo "📤 Uploading to S3: $S3_PATH"

    aws s3 cp "$BACKUP_FILE" "$S3_PATH" \
        --region "$S3_REGION" \
        --storage-class "$S3_STORAGE_CLASS" \
        --metadata "uploaded=$(date -u +%Y-%m-%dT%H:%M:%SZ),source=automated-backup"

    if [ $? -eq 0 ]; then
        echo "✅ Upload to S3 successful!"
        echo "   URL: $S3_PATH"

        # Set lifecycle policy if not exists (keep 90 days)
        echo "🗄️  Configuring lifecycle policy (90 days retention)..."
        LIFECYCLE_POLICY=$(cat <<EOF
{
    "Rules": [
        {
            "Id": "DeleteOldBackups",
            "Status": "Enabled",
            "Prefix": "$S3_PREFIX/",
            "Expiration": {
                "Days": 90
            }
        }
    ]
}
EOF
)
        echo "$LIFECYCLE_POLICY" | aws s3api put-bucket-lifecycle-configuration \
            --bucket "$S3_BUCKET" \
            --lifecycle-configuration file:///dev/stdin 2>/dev/null || true

        # Enable versioning for safety
        aws s3api put-bucket-versioning \
            --bucket "$S3_BUCKET" \
            --versioning-configuration Status=Enabled 2>/dev/null || true

        return 0
    else
        echo "❌ Upload to S3 failed!"
        return 1
    fi
}

# =============================================================================
# Google Cloud Storage Upload
# =============================================================================
upload_to_gcs() {
    # Configuration from environment variables
    GCS_BUCKET="${BACKUP_GCS_BUCKET:-backtester-backups}"
    GCS_STORAGE_CLASS="${GCS_STORAGE_CLASS:-NEARLINE}"  # Cheaper for backups
    GCS_PREFIX="${GCS_PREFIX:-database-backups}"

    # Check gcloud CLI
    if ! command -v gsutil &> /dev/null; then
        echo "❌ Google Cloud SDK not installed"
        echo "   Install: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        echo "❌ Google Cloud not authenticated"
        echo "   Run: gcloud auth login"
        exit 1
    fi

    GCS_PATH="gs://$GCS_BUCKET/$GCS_PREFIX/$BACKUP_NAME"

    echo "📤 Uploading to GCS: $GCS_PATH"

    gsutil -h "Content-Type:application/gzip" \
           -h "x-goog-meta-uploaded:$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
           -h "x-goog-meta-source:automated-backup" \
           cp "$BACKUP_FILE" "$GCS_PATH"

    if [ $? -eq 0 ]; then
        # Set storage class
        gsutil rewrite -s "$GCS_STORAGE_CLASS" "$GCS_PATH" 2>/dev/null || true

        echo "✅ Upload to GCS successful!"
        echo "   URL: $GCS_PATH"

        # Set lifecycle policy (keep 90 days)
        echo "🗄️  Configuring lifecycle policy (90 days retention)..."
        LIFECYCLE_JSON=$(cat <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["$GCS_PREFIX/"]
        }
      }
    ]
  }
}
EOF
)
        echo "$LIFECYCLE_JSON" | gsutil lifecycle set /dev/stdin "gs://$GCS_BUCKET" 2>/dev/null || true

        return 0
    else
        echo "❌ Upload to GCS failed!"
        return 1
    fi
}

# =============================================================================
# Main Upload Logic
# =============================================================================

case "$PROVIDER" in
    s3)
        upload_to_s3
        ;;
    gcs)
        upload_to_gcs
        ;;
    *)
        echo "❌ Unknown provider: $PROVIDER"
        echo "   Supported: s3, gcs"
        exit 1
        ;;
esac

echo ""
echo "✅ Cloud upload complete!"
echo ""
echo "📋 Verification:"
case "$PROVIDER" in
    s3)
        echo "   List backups: aws s3 ls s3://$S3_BUCKET/$S3_PREFIX/"
        echo "   Download: aws s3 cp s3://$S3_BUCKET/$S3_PREFIX/$BACKUP_NAME ./"
        ;;
    gcs)
        echo "   List backups: gsutil ls gs://$GCS_BUCKET/$GCS_PREFIX/"
        echo "   Download: gsutil cp gs://$GCS_BUCKET/$GCS_PREFIX/$BACKUP_NAME ./"
        ;;
esac
