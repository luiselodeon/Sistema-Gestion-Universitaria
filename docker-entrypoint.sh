#!/bin/bash
set -e

echo "Waiting for MySQL to be ready..."

# Wait for MySQL using Python connection attempt
until python3 << END
import sys
import os
import mysql.connector
try:
    host = os.getenv("DB_HOST", "proyecto_bases_mysql_db")
    user = os.getenv("DB_USER") or os.getenv("MYSQL_USER", "myuser")
    password = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD", "mypassword")
    database = os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE", "controlescolar_db")

    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
END
do
    echo "Waiting for database connection..."
    sleep 2
done

echo "MySQL is ready!"

# Check if database should be seeded (only on first run or if flag is set)
if [ "${SEED_DATABASE:-true}" = "true" ]; then
    echo "Seeding database with test data..."
    python3 /app/seed_data.py
    
    if [ $? -eq 0 ]; then
        echo "Database seeded successfully!"
    else
        echo "Warning: Database seeding failed, but continuing..."
    fi
else
    echo "Skipping database seeding (SEED_DATABASE=false)"
fi

echo "Starting Flask application..."
# Execute the main command
exec "$@"
