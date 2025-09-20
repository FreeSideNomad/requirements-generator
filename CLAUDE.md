# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered requirements gathering application that guides teams through creating comprehensive product requirements using domain-driven design principles. The tool leverages OpenAI's ChatGPT interface to interactively help users develop product visions, identify bounded contexts, and create structured requirements from epics down to user stories.

**Target Domain**: Tier 1 Canadian Bank financial systems serving business clients with customer and employee facing features and APIs.

## Architecture & Domain Model

### Core Bounded Contexts
1. **Requirements Management** (Core) - Product, Epic, Feature, UserStory hierarchy
2. **AI-Assisted Discovery** (Core) - Conversational sessions with RAG context
3. **Domain Modeling** (Core) - Bounded contexts, domain objects, ubiquitous language
4. **Collaboration & Workflow** (Supporting) - Git-style change management, approvals
5. **Enterprise Integration** (Supporting) - Jira, Git, Confluence, SharePoint sync
6. **Identity & Access Management** (Supporting) - Role-based access control

### Key Domain Concepts
- **RAG Context**: Retrieval-Augmented Generation for conversation history across sessions/users
- **Inconsistency**: Conflicting requirements with guided resolution workflows
- **Bounded Context**: DDD concept with domain objects, relationships, and ubiquitous language
- **Anti-Corruption Layer (ACL)**: Integration adapters for external system protection
- **Event Storming**: Domain discovery technique (Domain Designer role only)

## Development Commands

### Dependencies and Setup
```bash
# Python-based application (assumed stack)
pip install -r requirements.txt
python -m pytest tests/
python -m ruff check .
python -m mypy .
```

### Testing Strategy
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# End-to-end tests
python -m pytest tests/e2e/

# Domain model validation
python -m pytest tests/domain/
```

### API Development
```bash
# Start development server
python -m uvicorn app.main:app --reload

# API documentation
open http://localhost:8000/docs

# Database migrations
alembic upgrade head
```

## File Structure and Conventions

### Repository Organization
```
/products/{product-id}/
├── vision.md
├── bounded-contexts/{context-name}.md
├── epics/{epic-id}.md
├── features/{feature-id}.md
├── user-stories/{story-id}.md
├── domain-model/{entities,value-objects,aggregates}.yaml
├── diagrams/{context-map,domain-relationships,user-journey}.mermaid
└── metadata/{conversations,inconsistencies,approvals}.json
```

### Business Context Configuration
- Located in `/business-contexts/{context-name}.md`
- Configures AI research guidelines, compliance requirements, integration patterns
- Current context: Tier 1 Canadian bank with OSFI, PIPEDA, PCMLTFA compliance

## Key Implementation Patterns

### Conversation Sessions with RAG
- Maintain context across sessions and users within teams
- Vector database for semantic search of historical conversations
- Inconsistency detection with resolution workflows
- Context optimization for performance

### Git-Style Change Management
- Branch creation for requirement changes: `req/{product-id}/{change-type}/{description}`
- Pull request workflow with approval process
- Commit messages include conversation metadata and session IDs
- Squash merge with comprehensive commit descriptions

### Role-Based Access Control
- **Reader**: View, comment, suggest changes
- **Contributor**: Create/edit requirements, participate in sessions
- **Approver**: Approve changes, resolve inconsistencies
- **Domain Designer**: Event storming, bounded context design
- **Team Lead**: Manage access, configure business context

### Enterprise Integrations
- **Jira**: Automatic epic/story creation, bidirectional sync, import/export fallback
- **Git**: Repository management, webhook integration, commit automation
- **Confluence**: Documentation export with diagram embedding
- **SharePoint**: Document storage with permission mapping

## AI Integration Guidelines

### OpenAI API Configuration
- Configurable models and prompts per business context
- Template-based question generation (functional, non-functional, compliance)
- Research automation with competitive analysis
- Domain boundary suggestions with rationale

### Diagram Generation
- Mermaid format for context maps, ERDs, user journeys
- AI-prompted updates with preview/approval workflow
- Automatic generation triggers on requirement changes
- Version control for diagram evolution

## Development Priorities

### Phase 1 (MVP)
1. Conversational requirements interface with basic RAG
2. Bounded context identification and domain object modeling
3. Git-style change management with role-based access

### Phase 2 (Full Platform)
1. Advanced RAG with cross-session context optimization
2. Jira and Git repository integration
3. Automated diagram generation (context maps, ERDs)

### Phase 3 (Advanced Features)
1. Event storming support for Domain Designer role
2. Confluence and SharePoint integration
3. AI-assisted diagram updates with user journey flows

## Compliance and Security

### Canadian Banking Regulations
- OSFI (Office of the Superintendent of Financial Institutions) requirements
- PIPEDA (Personal Information Protection and Electronic Documents Act)
- PCMLTFA (Proceeds of Crime Money Laundering and Terrorist Financing Act)
- Data residency requirements (Canadian data sovereignty)

### Enterprise Security
- SSO integration (SAML/OIDC)
- Multi-factor authentication required
- Comprehensive audit logging
- Role-based data access isolation
- API rate limiting and webhook signature verification

## Testing Strategy

### Domain Model Testing
- Aggregate invariant validation
- Business rule consistency checks
- Bounded context boundary verification
- Ubiquitous language consistency

### AI Integration Testing
- Conversation flow validation
- RAG context retrieval accuracy
- Inconsistency detection effectiveness
- Research result quality assessment

### Integration Testing
- Jira synchronization accuracy
- Git workflow automation
- Diagram generation correctness
- Enterprise SSO and permissions

## Performance Considerations

### RAG Optimization
- Vector database indexing for conversation history
- Context pruning for large conversation sessions
- Caching strategies for similar change patterns
- Progressive loading for large diagrams

### Scalability Requirements
- Support 100+ concurrent conversation sessions
- AI response time < 3 seconds
- 99.9% uptime for critical integrations
- Team-scoped data isolation for multi-tenancy