#!/usr/bin/env bash
# ==============================================================================
# MobiPrice Automated SQLite3 & Media Backup Script
# Safe hot backup using SQLite .backup (zero downtime, no table locking)
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/mobiprice}"
PROJECT_DIR="${PROJECT_DIR:-/var/www/mobiprice}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=14

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting MobiPrice Backup..."

# 1. Hot Backup of SQLite3 Database (WAL-safe)
DB_BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sqlite3"
sqlite3 "${PROJECT_DIR}/db.sqlite3" ".backup '${DB_BACKUP_FILE}'"

# Compress SQLite backup
gzip -9 "${DB_BACKUP_FILE}"
echo "[$(date)] Database backed up: ${DB_BACKUP_FILE}.gz"

# 2. Backup Media Directory (Device photos, spare part images)
if [ -d "${PROJECT_DIR}/media" ]; then
    MEDIA_BACKUP_FILE="${BACKUP_DIR}/media_backup_${TIMESTAMP}.tar.gz"
    tar -czf "${MEDIA_BACKUP_FILE}" -C "${PROJECT_DIR}" media
    echo "[$(date)] Media backed up: ${MEDIA_BACKUP_FILE}"
fi

# 3. Clean up backups older than retention policy
find "${BACKUP_DIR}" -type f -name "*.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Cleaned up backups older than ${RETENTION_DAYS} days."

echo "[$(date)] Backup completed successfully!"
