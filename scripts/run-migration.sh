#!/bin/bash
set -e

MIGRATION_FILE=$1

if [ -z "$MIGRATION_FILE" ]; then
    echo "Usage: ./run-migration.sh "
    echo "Example: ./run-migration.sh migrations/001_expand_address.sql"
    exit 1
fi

if [ ! -f "$MIGRATION_FILE" ]; then
    echo "Migration file not found: $MIGRATION_FILE"
    exit 1
fi

# Get database endpoint from Terraform output
DB_ENDPOINT=$(cd terraform && terraform output -raw db_endpoint 2>/dev/null || echo "localhost")
DB_NAME=${DB_NAME:-ecommerce}
DB_USER=${DB_USER:-postgres}

echo "Running migration: $MIGRATION_FILE"
echo "Target database: $DB_ENDPOINT/$DB_NAME"
read -p "Continue? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    PGPASSWORD=$DB_PASSWORD psql -h $DB_ENDPOINT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE
    echo "Migration completed successfully!"
else
    echo "Migration cancelled."
fi
