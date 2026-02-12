-- Create read-only user for pgweb and external tools
-- This script runs automatically on first container start

-- Create the reader user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'portfolio_reader') THEN
        CREATE USER portfolio_reader WITH PASSWORD 'reader_password_change_me';
    END IF;
END
$$;

-- Grant connection to the database
GRANT CONNECT ON DATABASE portfolio TO portfolio_reader;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA public TO portfolio_reader;
GRANT USAGE ON SCHEMA raw_toronto TO portfolio_reader;
GRANT USAGE ON SCHEMA stg_toronto TO portfolio_reader;
GRANT USAGE ON SCHEMA int_toronto TO portfolio_reader;
GRANT USAGE ON SCHEMA mart_toronto TO portfolio_reader;

-- Grant SELECT on all existing tables in schemas
GRANT SELECT ON ALL TABLES IN SCHEMA public TO portfolio_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA raw_toronto TO portfolio_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA stg_toronto TO portfolio_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA int_toronto TO portfolio_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA mart_toronto TO portfolio_reader;

-- Grant SELECT on future tables (default privileges)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO portfolio_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw_toronto GRANT SELECT ON TABLES TO portfolio_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA stg_toronto GRANT SELECT ON TABLES TO portfolio_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA int_toronto GRANT SELECT ON TABLES TO portfolio_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart_toronto GRANT SELECT ON TABLES TO portfolio_reader;

-- Verify user was created
SELECT rolname FROM pg_catalog.pg_roles WHERE rolname = 'portfolio_reader';
