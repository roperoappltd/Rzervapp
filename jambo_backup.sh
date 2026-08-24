#!/bin/bash
# Dumps ONLY jambo_db (not the whole shared MariaDB server -- NextCloud
# presumably has its own separate backup strategy already, no need to
# duplicate that here). Compresses the dump, keeps the last 7 daily
# backups, deletes anything older automatically.
#
# Credentials are read from ~/.my.cnf rather than embedded in this
# script -- see the setup note below. Anyone who can read this file
# shouldn't be able to see the database password just by opening it.

set -e

BACKUP_DIR="/srv/dockerdata/Jambo_database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="jambo_db_${TIMESTAMP}.sql"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

# Connects to the shared MariaDB container via its published host port
# (3308, from the earlier docker ps output). --defaults-extra-file
# reads credentials from a separate, permission-locked file instead of
# passing -p on the command line, which would otherwise be visible to
# anyone running `ps` while this script is executing.
mysqldump --defaults-extra-file=/root/.jambo_db_credentials.cnf \
    -h 127.0.0.1 -P 3308 \
    jambo_db > "${BACKUP_DIR}/${FILENAME}"

gzip "${BACKUP_DIR}/${FILENAME}"

# Delete anything older than the retention window
find "$BACKUP_DIR" -name "jambo_db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "$(date): Backup completed -- ${FILENAME}.gz" >> "${BACKUP_DIR}/backup.log"
