#!/bin/bash

# Database Migration Script for Docker
# This script runs database migrations in the Docker environment

set -e

echo "🔄 Running database migrations..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
python -c "
import time
import psycopg2
from psycopg2 import OperationalError
import os

def wait_for_db():
    db_config = {
        'host': os.getenv('DB_HOST', 'postgres'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'statement_user'),
        'password': os.getenv('DB_PASS', 'statement_password'),
        'database': os.getenv('DB_NAME', 'statement_sense')
    }
    
    for i in range(30):
        try:
            conn = psycopg2.connect(**db_config)
            conn.close()
            print('✅ Database is ready!')
            return True
        except OperationalError:
            print(f'⏳ Waiting for database... ({i+1}/30)')
            time.sleep(2)
    
    raise Exception('❌ Database connection timeout')

wait_for_db()
"

# Run migrations
echo "🚀 Running Alembic migrations..."
alembic upgrade head

echo "✅ Database migrations completed successfully!"
