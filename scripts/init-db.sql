-- Initialize PostgreSQL database with pgvector extension and development data

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create development database if not exists
\c requirements_db;

-- Enable extensions in the requirements database
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create schemas for multi-tenant architecture
CREATE SCHEMA IF NOT EXISTS shared;
CREATE SCHEMA IF NOT EXISTS tenants;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS requirements;
CREATE SCHEMA IF NOT EXISTS domain;

-- Grant permissions to postgres user
GRANT ALL ON SCHEMA shared TO postgres;
GRANT ALL ON SCHEMA tenants TO postgres;
GRANT ALL ON SCHEMA auth TO postgres;
GRANT ALL ON SCHEMA ai TO postgres;
GRANT ALL ON SCHEMA requirements TO postgres;
GRANT ALL ON SCHEMA domain TO postgres;

-- Create test database for development
CREATE DATABASE requirements_test;
\c requirements_test;

-- Enable extensions in test database
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create same schemas in test database
CREATE SCHEMA IF NOT EXISTS shared;
CREATE SCHEMA IF NOT EXISTS tenants;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS requirements;
CREATE SCHEMA IF NOT EXISTS domain;

-- Grant permissions
GRANT ALL ON SCHEMA shared TO postgres;
GRANT ALL ON SCHEMA tenants TO postgres;
GRANT ALL ON SCHEMA auth TO postgres;
GRANT ALL ON SCHEMA ai TO postgres;
GRANT ALL ON SCHEMA requirements TO postgres;
GRANT ALL ON SCHEMA domain TO postgres;