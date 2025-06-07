-- Database initialization script for StatementSense
-- This script will be executed when the PostgreSQL container starts

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE statement_sense'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'statement_sense');

-- Connect to the database
\c statement_sense

-- Create the user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'statement_user') THEN
        CREATE USER statement_user WITH PASSWORD 'statement_password';
    END IF;
END
$$;

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE statement_sense TO statement_user;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Make sure the user has all privileges on the public schema
GRANT ALL PRIVILEGES ON SCHEMA public TO statement_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO statement_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO statement_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO statement_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO statement_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO statement_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO statement_user;

-- Initial setup complete
SELECT 'StatementSense database initialized successfully' as message;
