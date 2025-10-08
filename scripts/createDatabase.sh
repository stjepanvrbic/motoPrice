#!/bin/bash
# Create PostgreSQL database for motoPrice

set -e

DB_NAME="motoprice"
DB_USER="${DB_USER:-$USER}"

echo "Creating database: $DB_NAME"

if psql postgres -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Database '$DB_NAME' already exists"
else
    createdb $DB_NAME
    echo "Database '$DB_NAME' created successfully"
fi
