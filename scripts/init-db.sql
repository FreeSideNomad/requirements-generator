-- PostgreSQL initialization script for Requirements Generator
-- This script sets up the database with required extensions

-- Enable pgvector extension for vector storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for full-text search capabilities
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable btree_gin for advanced indexing
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Create a function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Set up database configuration for better performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA audit TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Requirements Generator database initialized successfully';
    RAISE NOTICE 'Extensions enabled: vector, uuid-ossp, pg_trgm, btree_gin';
    RAISE NOTICE 'Schemas created: audit, analytics';
END $$;