# Requirements Generator - Multi-Tenant SaaS Platform

AI-powered requirements gathering platform that uses FastAPI + Pydantic to guide teams through creating comprehensive product requirements using domain-driven design principles.

## Technology Stack

- **Backend**: Python 3.11+ with FastAPI 0.104+
- **Data Validation**: Pydantic v2
- **Database**: PostgreSQL 15+ with pgvector extension
- **Session/Cache**: Redis with async client
- **Frontend**: Jinja2 templates + HTMX
- **Real-time**: Server-Sent Events (SSE)
- **AI Integration**: OpenAI API
- **Authentication**: JWT with Azure AD integration

## Development Stages

This project is being developed in stages using Claude Code:

### Stage 1: Core Foundation
- Project setup and configuration
- Database models with Pydantic
- Basic FastAPI structure
- Docker development environment

### Stage 2: Multi-Tenant Foundation
- Tenant management system
- Authentication and authorization
- Database tenant isolation
- Basic web interface

### Stage 3: AI Integration Core
- OpenAI API integration
- Conversation session management
- Real-time SSE implementation
- Background task processing

### Stage 4: Requirements Management
- CRUD operations for requirements
- Domain-driven design support
- Markdown documentation generation
- Version control basics

### Stage 5: Advanced Features
- RAG with pgvector
- Advanced collaboration features
- Enterprise integrations
- Performance optimization

## Getting Started

```bash
# Clone the repository
git clone git@github.com:FreeSideNomad/requirements-generator.git
cd requirements-generator

# Install uv (ultra-fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

# Install dependencies
./scripts/dev.sh install

# Set up development environment
docker-compose up -d

# Run database migrations
./scripts/dev.sh migrate

# Start development server
./scripts/dev.sh dev
```

## Development Commands

```bash
# Install dependencies
./scripts/dev.sh install

# Start development server
./scripts/dev.sh dev

# Run tests
./scripts/dev.sh test

# Run code quality checks
./scripts/dev.sh lint

# Format code
./scripts/dev.sh format

# Start background worker
./scripts/dev.sh worker

# Clean cache files
./scripts/dev.sh clean
```

## Project Structure

```
src/
├── tenants/      # Tenant management domain
├── ai/          # AI conversation domain
├── requirements/ # Requirements domain
├── auth/        # Authentication domain
├── shared/      # Shared utilities
└── main.py      # FastAPI application entry point
```

## Contributing

This project is being developed incrementally with Claude Code assistance. Each feature branch corresponds to a development stage with comprehensive tests and documentation.