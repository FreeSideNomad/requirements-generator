# Technical Specifications and API Design

## Core API Specifications

### Authentication & Authorization

#### JWT Token Structure
```yaml
JWT_Payload:
  sub: userId (UUID)
  roles: List[Role]
  teams: List[TeamId]
  products: List[ProductId]
  permissions: List[Permission]
  exp: expiration_timestamp
  iat: issued_at_timestamp
  iss: "requirements-gathering-tool"

Authorization_Header:
  format: "Bearer {jwt_token}"
  required_for_all_endpoints: true
```

#### Role-Based Access Control
```yaml
Permission_Matrix:
  Reader:
    - products:read
    - conversations:read
    - comments:create
    - suggestions:create

  Contributor:
    - inherits: Reader
    - products:write
    - epics:create,update
    - features:create,update
    - sessions:create,participate

  Approver:
    - inherits: Contributor
    - changes:approve,reject
    - inconsistencies:resolve
    - reviews:create

  Domain_Designer:
    - inherits: Approver
    - bounded_contexts:create,update
    - domain_objects:create,update
    - event_storming:facilitate
    - diagrams:generate,update

  Team_Lead:
    - inherits: Domain_Designer
    - teams:manage
    - access_control:manage
    - business_context:configure
    - integrations:configure
```

### Products API

#### Create Product
```yaml
POST /api/products
Authorization: Required (Contributor+)
Request_Body:
  name: String (required, 3-100 chars)
  description: String (required, 10-1000 chars)
  businessContextId: UUID (required)
  vision: String (optional, max 5000 chars)
  teamIds: List[UUID] (required, min 1)

Response_201:
  id: UUID
  name: String
  description: String
  businessContext: BusinessContext
  vision: Vision (optional)
  status: "Draft"
  createdAt: DateTime
  createdBy: User
  teams: List[Team]

Error_Responses:
  400: Invalid input data
  403: Insufficient permissions
  404: Business context not found
  409: Product name already exists in team
```

#### Get Products
```yaml
GET /api/products
Authorization: Required (Reader+)
Query_Parameters:
  teamId: UUID (optional, filters by team)
  status: ProductStatus (optional)
  businessContext: UUID (optional)
  limit: Int (default 20, max 100)
  offset: Int (default 0)

Response_200:
  products: List[ProductSummary]
  total: Int
  hasMore: Boolean

ProductSummary:
  id: UUID
  name: String
  description: String
  status: ProductStatus
  lastModified: DateTime
  teamCount: Int
  epicCount: Int
  featureCount: Int
```

### Documentation Generation API

#### Generate Markdown Documentation
```yaml
POST /api/products/{productId}/documentation/generate
Authorization: Required (Reader+)
Request_Body:
  documentationType: DocumentationType (required)
  sections: List[DocumentSection] (optional, default all)
  format: OutputFormat (default "markdown")
  includeVisuals: Boolean (default false)

DocumentationType:
  enum: [FullProduct, BoundedContext, DomainModel, RequirementsOverview, IntegrationSpecs]

DocumentSection:
  enum: [Vision, Epics, Features, UserStories, DomainObjects, Relationships, Glossary, ComplianceNotes]

OutputFormat:
  enum: [markdown, json, yaml]

Response_200:
  documentId: UUID
  content: String (markdown content)
  metadata: DocumentMetadata
  generatedAt: DateTime
  wordCount: Int
  estimatedReadingTime: Int (minutes)

DocumentMetadata:
  title: String
  sections: List[SectionMetadata]
  crossReferences: List[CrossReference]
  tableOfContents: List[TOCEntry]
  glossaryTerms: List[GlossaryTerm]

SectionMetadata:
  id: String
  title: String
  level: Int (heading level)
  wordCount: Int
  lastUpdated: DateTime
```

#### Export Documentation
```yaml
GET /api/products/{productId}/documentation/export
Authorization: Required (Reader+)
Query_Parameters:
  format: ExportFormat (required)
  sections: List[DocumentSection] (optional)
  includeMetadata: Boolean (default true)
  template: TemplateId (optional)

ExportFormat:
  enum: [markdown, confluence, sharepoint, pdf, docx]

Response_200:
  content: String or Binary
  fileName: String
  mimeType: String
  size: Int (bytes)
  exportedAt: DateTime
```

### Conversation Sessions API

#### Start Conversation Session
```yaml
POST /api/sessions
Authorization: Required (Contributor+)
Request_Body:
  productId: UUID (required)
  sessionType: SessionType (required)
  title: String (optional, max 200 chars)
  participantIds: List[UUID] (optional, max 10)
  businessContext: BusinessContextOverride (optional)

SessionType:
  enum: [VisionDefinition, EpicDiscovery, FeatureDetailing, UserStoryCreation, RequirementRefinement]

Response_201:
  sessionId: UUID
  productId: UUID
  sessionType: SessionType
  status: "Active"
  participants: List[User]
  openingQuestion: String
  context: SessionContext
  createdAt: DateTime
  expiresAt: DateTime (4 hours from creation)

SessionContext:
  businessContext: BusinessContext
  relevantHistory: List[ContextualInformation]
  complianceReminders: List[ComplianceRequirement]
  suggestedTopics: List[String]
```

#### Send Message in Session
```yaml
POST /api/sessions/{sessionId}/messages
Authorization: Required (Participant in session)
Request_Body:
  content: String (required, max 5000 chars)
  messageType: MessageType (required)
  referencesMessageId: UUID (optional)
  isPrivateNote: Boolean (default false)

MessageType:
  enum: [Question, Answer, Clarification, Correction, Note]

Response_201:
  messageId: UUID
  sessionId: UUID
  senderId: UUID
  content: String
  messageType: MessageType
  timestamp: DateTime
  aiResponse: AIResponse (if applicable)

AIResponse:
  content: String
  followUpQuestions: List[String]
  contextualInformation: List[ContextualInfo]
  inconsistenciesDetected: List[Inconsistency]
  suggestedActions: List[ActionSuggestion]
  completenessScore: Float (0-1)
  confidenceScore: Float (0-1)
```

#### Get Session Messages
```yaml
GET /api/sessions/{sessionId}/messages
Authorization: Required (Participant in session)
Query_Parameters:
  since: DateTime (optional, get messages after timestamp)
  messageType: MessageType (optional filter)
  includePrivateNotes: Boolean (default false, only own notes)
  limit: Int (default 50, max 200)

Response_200:
  messages: List[Message]
  hasMore: Boolean
  nextCursor: String (for pagination)

Message:
  id: UUID
  senderId: UUID
  senderName: String
  content: String
  messageType: MessageType
  timestamp: DateTime
  isPrivateNote: Boolean
  aiResponse: AIResponse (optional)
  reactions: List[MessageReaction] (optional)
```

### RAG Context API

#### Retrieve Relevant Context
```yaml
POST /api/rag/context
Authorization: Required (Reader+)
Request_Body:
  query: String (required, max 1000 chars)
  productId: UUID (required)
  sessionId: UUID (optional, current session)
  contextTypes: List[ContextType] (optional)
  maxResults: Int (default 10, max 50)
  similarityThreshold: Float (default 0.7, range 0-1)

ContextType:
  enum: [ConversationHistory, DecisionsMade, RequirementsIdentified, ResearchFindings, DomainKnowledge]

Response_200:
  contextId: UUID
  query: String
  results: List[ContextResult]
  totalFound: Int
  processingTime: Float (seconds)

ContextResult:
  id: UUID
  type: ContextType
  content: String
  source: ContextSource
  relevanceScore: Float (0-1)
  timestamp: DateTime
  metadata: ContextMetadata

ContextSource:
  sessionId: UUID (optional)
  userId: UUID
  productId: UUID
  type: SourceType [Session, Research, Decision, Documentation]

ContextMetadata:
  participants: List[String] (if from session)
  approvalStatus: ApprovalStatus (if applicable)
  tags: List[String]
  businessContext: String
```

### Research API

#### Trigger Competitive Research
```yaml
POST /api/research/competitive
Authorization: Required (Contributor+)
Request_Body:
  productId: UUID (required)
  researchScope: List[ResearchCategory] (required)
  focusAreas: List[String] (optional)
  competitors: List[String] (optional)
  timeframe: ResearchTimeframe (optional, default "Current")

ResearchCategory:
  enum: [FeatureComparison, PricingAnalysis, RegulatoryCompliance, TechnologyStack, UserExperience, MarketPositioning]

ResearchTimeframe:
  enum: [Current, LastYear, LastTwoYears, Historical]

Response_202:
  researchJobId: UUID
  estimatedCompletionTime: DateTime
  status: "InProgress"
  notificationUrl: String (webhook for completion)

Background_Process_Response:
  researchId: UUID
  productId: UUID
  summary: String
  findings: List[ResearchFinding]
  sources: List[ResearchSource]
  recommendations: List[String]
  complianceNotes: List[ComplianceNote]
  confidence: Float (0-1)
  completedAt: DateTime

ResearchFinding:
  category: ResearchCategory
  title: String
  description: String
  relevanceScore: Float (0-1)
  evidenceStrength: EvidenceStrength [High, Medium, Low]
  source: ResearchSource
  implications: List[BusinessImplication]
  actionItems: List[String]

BusinessImplication:
  type: ImplicationType [Opportunity, Threat, Requirement, Constraint]
  impact: ImpactLevel [Critical, High, Medium, Low]
  description: String
  timeline: String
```

### Inconsistency Management API

#### Get Inconsistencies
```yaml
GET /api/products/{productId}/inconsistencies
Authorization: Required (Reader+)
Query_Parameters:
  status: InconsistencyStatus (optional)
  severity: Severity (optional)
  assignedTo: UUID (optional)
  createdAfter: DateTime (optional)
  limit: Int (default 20, max 100)

InconsistencyStatus:
  enum: [Open, InReview, Resolved, Dismissed]

Response_200:
  inconsistencies: List[Inconsistency]
  summary: InconsistencySummary

Inconsistency:
  id: UUID
  productId: UUID
  type: InconsistencyType
  severity: Severity
  description: String
  conflictingElements: List[RequirementElement]
  detectedAt: DateTime
  detectedBy: DetectionSource [AI, User, System]
  status: InconsistencyStatus
  assignedTo: User (optional)
  resolutionOptions: List[ResolutionOption]
  resolution: Resolution (optional)

InconsistencyType:
  enum: [Contradiction, Ambiguity, MissingInformation, RegulatoryConflict, BusinessRuleViolation]

RequirementElement:
  id: UUID
  type: ElementType [Epic, Feature, UserStory, DomainObject, BusinessRule]
  name: String
  content: String
  source: ElementSource
  lastModified: DateTime

ResolutionOption:
  id: UUID
  description: String
  pros: List[String]
  cons: List[String]
  impact: ImpactAssessment
  recommendationScore: Float (0-1)
  requiredApprovals: List[Role]
```

#### Resolve Inconsistency
```yaml
POST /api/inconsistencies/{inconsistencyId}/resolve
Authorization: Required (Approver+)
Request_Body:
  resolutionOptionId: UUID (required)
  rationale: String (required, max 2000 chars)
  additionalNotes: String (optional, max 1000 chars)
  notifyParticipants: Boolean (default true)

Response_200:
  inconsistencyId: UUID
  resolution: Resolution
  updatedElements: List[RequirementElement]
  auditTrail: AuditEntry

Resolution:
  id: UUID
  resolutionOptionId: UUID
  rationale: String
  resolvedBy: User
  resolvedAt: DateTime
  impactedElements: List[RequirementElement]
  followUpActions: List[Action]

AuditEntry:
  id: UUID
  action: AuditAction
  performedBy: User
  timestamp: DateTime
  details: AuditDetails

AuditAction:
  enum: [Created, Updated, Resolved, Dismissed, Reassigned]
```

## Data Models

### Core Entities

#### Product Entity
```yaml
Product:
  id: UUID (Primary Key)
  name: String (Unique within team, indexed)
  description: Text
  businessContextId: UUID (Foreign Key)
  vision: Text (optional)
  status: ProductStatus
  createdAt: DateTime
  updatedAt: DateTime
  createdBy: UUID (Foreign Key to User)

  # Relationships
  epics: OneToMany[Epic]
  sessions: OneToMany[ConversationSession]
  teams: ManyToMany[Team]
  boundedContexts: OneToMany[BoundedContext]

  # Indexes
  indexes:
    - name, businessContextId (compound unique)
    - status, updatedAt (compound)
    - createdBy, createdAt (compound)
```

#### ConversationSession Entity
```yaml
ConversationSession:
  id: UUID (Primary Key)
  productId: UUID (Foreign Key)
  sessionType: SessionType
  title: String (optional)
  status: SessionStatus [Active, Paused, Completed, Expired]
  createdAt: DateTime
  updatedAt: DateTime
  expiresAt: DateTime
  createdBy: UUID (Foreign Key to User)

  # RAG Context
  ragContextId: UUID (Foreign Key)
  contextVersion: Integer (optimistic locking)

  # Session Metadata
  metadata: JSONB {
    businessContextOverrides: {},
    participantPermissions: {},
    customPrompts: {},
    researchPreferences: {}
  }

  # Relationships
  messages: OneToMany[ConversationMessage]
  participants: ManyToMany[User]
  inconsistencies: OneToMany[Inconsistency]

  # Indexes
  indexes:
    - productId, status, updatedAt (compound)
    - createdBy, createdAt (compound)
    - status, expiresAt (compound, for cleanup)
```

#### ConversationMessage Entity
```yaml
ConversationMessage:
  id: UUID (Primary Key)
  sessionId: UUID (Foreign Key)
  senderId: UUID (Foreign Key to User, nullable for AI)
  content: Text
  messageType: MessageType
  timestamp: DateTime
  isPrivateNote: Boolean (default false)
  referencesMessageId: UUID (Foreign Key, optional)

  # AI Response Data
  aiResponseData: JSONB (optional) {
    followUpQuestions: [],
    contextualInfo: [],
    completenessScore: Float,
    confidenceScore: Float,
    processingTime: Float
  }

  # Vector Embedding for RAG
  contentEmbedding: Vector(384) (for semantic search)

  # Relationships
  reactions: OneToMany[MessageReaction]

  # Indexes
  indexes:
    - sessionId, timestamp (compound)
    - senderId, timestamp (compound)
    - messageType, timestamp (compound)
    - contentEmbedding (vector index for similarity search)
```

#### RAGContext Entity
```yaml
RAGContext:
  id: UUID (Primary Key)
  productId: UUID (Foreign Key)
  version: Integer (incremented on updates)
  lastUpdated: DateTime

  # Context Optimization
  totalDocuments: Integer
  activeDocuments: Integer (not pruned)
  lastOptimization: DateTime

  # Performance Metrics
  avgRetrievalTime: Float (milliseconds)
  avgRelevanceScore: Float

  # Relationships
  contextDocuments: OneToMany[ContextDocument]

  # Indexes
  indexes:
    - productId, version (compound unique)
    - lastUpdated (for cleanup jobs)
```

#### ContextDocument Entity
```yaml
ContextDocument:
  id: UUID (Primary Key)
  ragContextId: UUID (Foreign Key)
  sourceType: ContextSourceType
  sourceId: UUID (polymorphic reference)
  content: Text
  contentEmbedding: Vector(384)
  relevanceScore: Float (computed)

  # Metadata
  metadata: JSONB {
    participants: [],
    tags: [],
    businessContext: String,
    approvalStatus: String,
    source: {}
  }

  # Lifecycle
  createdAt: DateTime
  lastAccessed: DateTime
  accessCount: Integer
  isPruned: Boolean (default false)

  # Indexes
  indexes:
    - ragContextId, sourceType (compound)
    - contentEmbedding (vector index)
    - lastAccessed, accessCount (compound, for pruning)
    - isPruned (for active filtering)
```

### Business Logic Constraints

#### Data Validation Rules
```yaml
Validation_Rules:
  Product:
    name:
      - min_length: 3
      - max_length: 100
      - pattern: "^[a-zA-Z0-9\\s\\-_]+$"
      - unique_within_team: true
    description:
      - min_length: 10
      - max_length: 1000
      - required: true

  ConversationSession:
    participants:
      - max_count: 10
      - all_must_be_team_members: true
    title:
      - max_length: 200
      - no_special_characters: true
    expiration:
      - max_duration_hours: 4
      - auto_extend_on_activity: true

  ConversationMessage:
    content:
      - max_length: 5000
      - no_html_injection: true
      - profanity_filter: enabled
    messageType:
      - must_match_context: true
      - ai_messages_only_response: true
```

#### Business Rule Enforcement
```yaml
Business_Rules:
  Access_Control:
    - team_isolation: "Users can only access products assigned to their teams"
    - role_hierarchy: "Higher roles inherit lower role permissions"
    - private_notes: "Only visible to creator and team leads"

  Data_Integrity:
    - conversation_continuity: "Messages must maintain chronological order"
    - context_consistency: "RAG context must reflect current product state"
    - approval_workflow: "Changes require appropriate role approval"

  Performance:
    - session_timeout: "Inactive sessions auto-expire after 4 hours"
    - context_pruning: "Old, low-relevance context automatically pruned"
    - rate_limiting: "AI requests limited to 60 per minute per user"

  Compliance:
    - audit_trail: "All actions logged with user and timestamp"
    - data_retention: "Personal data purged after configured period"
    - encryption: "Sensitive data encrypted at rest and in transit"
```