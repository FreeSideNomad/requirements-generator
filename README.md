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

# Set up development environment
docker-compose up -d
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload
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