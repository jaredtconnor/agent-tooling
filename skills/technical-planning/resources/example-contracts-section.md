# API Contract and Data Model Examples

This document provides detailed examples for defining API contracts and data models during technical planning.

## Data Model Templates

### Basic Entity Model

```markdown
**EntityName** (new model - create src/models/entity-name.ts)
- id: UUID (primary key)
- name: string, max 255 chars, indexed
- description: string, max 1000 chars, nullable
- status: enum (ACTIVE, INACTIVE, PENDING)
- createdAt: DateTime
- updatedAt: DateTime
- deletedAt: DateTime, nullable (soft delete)

**Validation:**
- name: required, min 3 chars, max 255 chars, alphanumeric + spaces
- description: optional, max 1000 chars
- status: must be valid enum value, defaults to PENDING

**Indexes:**
- Primary: id
- Unique: (name, status) for active records
- Performance: status (for filtering queries)

**Relationships:**
- belongsTo(User) via userId
- hasMany(RelatedEntity) via entityId
```

### Extending Existing Model

```markdown
**User** (extend existing src/models/user.ts)
- id: UUID (existing)
- email: string, unique, indexed (existing)
- passwordHash: string (NEW - bcrypt hash)
- lastLoginAt: DateTime, nullable (NEW)
- loginAttempts: integer, default 0 (NEW - for rate limiting)
- lockedUntil: DateTime, nullable (NEW - account lock expiry)
- createdAt: DateTime (existing)
- updatedAt: DateTime (existing)
- sessions: Session[] (NEW relationship)

**Migration Required:**
- Add column: passwordHash (string, 60 chars, not null)
- Add column: lastLoginAt (timestamp, nullable)
- Add column: loginAttempts (integer, default 0, not null)
- Add column: lockedUntil (timestamp, nullable)
- Add index: lockedUntil (for cleanup queries)

**Validation:**
- Email: valid format, max 255 chars (existing)
- Password (input only): min 8 chars, requires uppercase, lowercase, number, special char
- passwordHash: bcrypt hash, exactly 60 chars
- loginAttempts: 0-10 range (lock account after 10 failed attempts)
- lockedUntil: must be in future if set
```

### Complex Relationship Model

```markdown
**Session** (new model - create src/models/session.ts)
- id: UUID (primary key)
- userId: UUID (foreign key to User, not null, indexed)
- token: string (JWT hash, 64 chars, unique, indexed)
- deviceFingerprint: string, max 255 chars, nullable
- ipAddress: string, max 45 chars (IPv6), nullable
- userAgent: string, max 500 chars, nullable
- expiresAt: DateTime (not null)
- revokedAt: DateTime, nullable
- createdAt: DateTime

**Validation:**
- userId: must reference existing user
- token: SHA256 hash of JWT (for lookup), exactly 64 chars
- expiresAt: must be in future (at creation)
- ipAddress: valid IPv4 or IPv6 format if provided
- deviceFingerprint: custom validation (browser + OS hash)

**Indexes:**
- Primary: id
- Unique: token (fast lookup during auth)
- Performance: (userId, expiresAt) for user session queries
- Performance: expiresAt (for cleanup job)

**Relationships:**
- belongsTo(User) via userId (eager load user data on auth)

**Cascade Rules:**
- On user delete: CASCADE (delete all user sessions)
- On user update: NO ACTION (sessions reference user by ID)
```

## API Contract Templates

### POST Endpoint (Create Resource)

```markdown
**POST /api/auth/login**

**Purpose:** Authenticate user credentials and issue session token

**Request Headers:**
- Content-Type: application/json
- X-Request-ID: string (optional, for tracing)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123!"
}
```

**Validation:**

- email: required, valid email format, max 255 chars
- password: required, min 8 chars, max 72 chars (bcrypt limit)

**Response (200 OK):**

```json
{
  "token": "<example-jwt-access-token>",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "lastLoginAt": "2025-01-02T10:30:00Z"
  },
  "expiresAt": "2025-01-03T10:30:00Z"
}
```

**Error Responses:**

401 Unauthorized - Invalid credentials

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email or password is incorrect",
    "details": null
  }
}
```

401 Unauthorized - Account locked

```json
{
  "error": {
    "code": "ACCOUNT_LOCKED",
    "message": "Account locked due to too many failed attempts",
    "details": {
      "lockedUntil": "2025-01-02T11:00:00Z",
      "remainingMinutes": 15
    }
  }
}
```

400 Bad Request - Invalid input

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "email": "Invalid email format",
      "password": "Password must be at least 8 characters"
    }
  }
}
```

429 Too Many Requests - Rate limit exceeded

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many login attempts",
    "details": {
      "retryAfter": 300
    }
  }
}
```

**Behavior:**

- Successful authentication creates session in database
- Failed authentication increments loginAttempts counter
- After 10 failed attempts, account locked for 15 minutes
- Rate limiting: 5 requests per minute per IP
- Response time target: <200ms at P95

**Security Considerations:**

- Generic error message for invalid credentials (don't reveal if email exists)
- bcrypt password comparison (constant-time)
- Log failed attempts for security monitoring
- HTTPS required (redirect HTTP to HTTPS)

```

### GET Endpoint (Read Resource)

```markdown
**GET /api/auth/session**

**Purpose:** Validate current session and retrieve session metadata

**Request Headers:**
- Authorization: Bearer <token> (required)

**Request Parameters:** None

**Response (200 OK):**
```json
{
  "valid": true,
  "session": {
    "id": "650e8400-e29b-41d4-a716-446655440000",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "expiresAt": "2025-01-03T10:30:00Z",
    "createdAt": "2025-01-02T10:30:00Z"
  },
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

**Error Responses:**

401 Unauthorized - Invalid token

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Authentication token is invalid or malformed",
    "details": null
  }
}
```

401 Unauthorized - Expired session

```json
{
  "error": {
    "code": "SESSION_EXPIRED",
    "message": "Session has expired, please log in again",
    "details": {
      "expiredAt": "2025-01-02T10:30:00Z"
    }
  }
}
```

401 Unauthorized - Revoked session

```json
{
  "error": {
    "code": "SESSION_REVOKED",
    "message": "Session has been revoked",
    "details": {
      "revokedAt": "2025-01-02T09:00:00Z"
    }
  }
}
```

**Behavior:**

- Validates JWT signature
- Checks session not expired
- Checks session not revoked
- Returns user data for convenience
- Response time target: <100ms at P95

**Security Considerations:**

- Token validated cryptographically (JWT signature)
- Check both token expiry and session expiry (defense in depth)
- No sensitive data in response (no password hashes, etc.)

```

### POST Endpoint (Action/Command)

```markdown
**POST /api/auth/logout**

**Purpose:** Invalidate current session (explicit logout)

**Request Headers:**
- Authorization: Bearer <token> (required)

**Request Body:** None (optional body with all_devices flag)
```json
{
  "allDevices": false
}
```

**Response (204 No Content):**
No response body

**Error Responses:**

401 Unauthorized - Invalid token

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Authentication token is invalid or malformed",
    "details": null
  }
}
```

404 Not Found - Session not found

```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session does not exist or was already logged out",
    "details": null
  }
}
```

**Behavior:**

- Sets revokedAt timestamp on session record
- If allDevices=true, revokes all user sessions
- Token immediately invalid (no grace period)
- Idempotent (can call multiple times safely)
- Response time target: <150ms at P95

**Security Considerations:**

- Logout is immediate (no async processing)
- Token added to blacklist for remaining TTL
- Log logout events for security audit

```

### PATCH Endpoint (Partial Update)

```markdown
**PATCH /api/users/:userId**

**Purpose:** Update specific user fields (partial update)

**Request Headers:**
- Authorization: Bearer <token> (required)
- Content-Type: application/json

**URL Parameters:**
- userId: UUID (required)

**Request Body:** (all fields optional)
```json
{
  "email": "newemail@example.com",
  "displayName": "John Doe"
}
```

**Validation:**

- email: valid email format, max 255 chars, unique
- displayName: max 100 chars, alphanumeric + spaces

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newemail@example.com",
  "displayName": "John Doe",
  "updatedAt": "2025-01-02T10:35:00Z"
}
```

**Error Responses:**

403 Forbidden - Cannot update other users

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only update your own profile",
    "details": null
  }
}
```

409 Conflict - Email already exists

```json
{
  "error": {
    "code": "EMAIL_CONFLICT",
    "message": "Email address is already in use",
    "details": {
      "field": "email",
      "value": "newemail@example.com"
    }
  }
}
```

**Behavior:**

- Only updates fields provided in request body
- Validates ownership (user can only update their own profile)
- Admin users can update any profile (check role)
- Email change triggers verification email
- Response time target: <200ms at P95

**Security Considerations:**

- Authorization check (user owns resource or is admin)
- Email verification required before change takes effect
- Log profile changes for audit trail

```

### DELETE Endpoint (Remove Resource)

```markdown
**DELETE /api/users/:userId**

**Purpose:** Delete user account (soft delete)

**Request Headers:**
- Authorization: Bearer <token> (required)

**URL Parameters:**
- userId: UUID (required)

**Query Parameters:**
- hard: boolean (optional, default false) - Permanently delete if true

**Response (204 No Content):**
No response body

**Error Responses:**

403 Forbidden - Cannot delete other users
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only delete your own account",
    "details": null
  }
}
```

404 Not Found - User not found

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User does not exist or was already deleted",
    "details": null
  }
}
```

**Behavior:**

- Soft delete by default (sets deletedAt timestamp)
- Hard delete permanently removes record (admin only)
- Revokes all user sessions on delete
- Cascades to related entities per cascade rules
- Response time target: <300ms at P95 (due to cascade operations)

**Security Considerations:**

- Authorization check (user owns resource or is admin)
- Hard delete requires admin role
- Log deletions for audit trail
- Data retention policy: soft-deleted records purged after 90 days

```

## REST API Design Patterns

### Pagination

```markdown
**GET /api/users**

**Query Parameters:**
- page: integer, min 1, default 1
- limit: integer, min 1, max 100, default 20
- sort: string, format "field:direction", default "createdAt:desc"

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8,
    "hasNext": true,
    "hasPrev": false
  }
}
```

```

### Filtering

```markdown
**GET /api/users**

**Query Parameters:**
- status: enum (ACTIVE, INACTIVE, PENDING) - exact match
- email: string - case-insensitive partial match
- createdAfter: ISO 8601 date - range filter
- createdBefore: ISO 8601 date - range filter

**Example:**
GET /api/users?status=ACTIVE&email=john&createdAfter=2025-01-01T00:00:00Z

**Response:**
```json
{
  "data": [...],
  "filters": {
    "status": "ACTIVE",
    "email": "john",
    "createdAfter": "2025-01-01T00:00:00Z"
  },
  "pagination": {...}
}
```

```

### Bulk Operations

```markdown
**POST /api/users/bulk-update**

**Request:**
```json
{
  "ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "650e8400-e29b-41d4-a716-446655440001"
  ],
  "updates": {
    "status": "INACTIVE"
  }
}
```

**Response (200 OK):**

```json
{
  "updated": 2,
  "failed": 0,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "success": true
    },
    {
      "id": "650e8400-e29b-41d4-a716-446655440001",
      "success": true
    }
  ]
}
```

**Partial Failure Response (207 Multi-Status):**

```json
{
  "updated": 1,
  "failed": 1,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "success": true
    },
    {
      "id": "650e8400-e29b-41d4-a716-446655440001",
      "success": false,
      "error": {
        "code": "NOT_FOUND",
        "message": "User not found"
      }
    }
  ]
}
```

```

## GraphQL Contract Examples

### Query Schema

```graphql
type User {
  id: ID!
  email: String!
  displayName: String
  lastLoginAt: DateTime
  createdAt: DateTime!
  sessions(limit: Int = 10): [Session!]!
}

type Session {
  id: ID!
  userId: ID!
  expiresAt: DateTime!
  createdAt: DateTime!
  user: User!
}

type Query {
  currentUser: User
  user(id: ID!): User
  users(
    page: Int = 1
    limit: Int = 20
    status: UserStatus
  ): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

enum UserStatus {
  ACTIVE
  INACTIVE
  PENDING
}

scalar DateTime
```

### Mutation Schema

```graphql
type Mutation {
  login(input: LoginInput!): LoginPayload!
  logout(allDevices: Boolean = false): LogoutPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
}

input LoginInput {
  email: String!
  password: String!
}

type LoginPayload {
  token: String!
  user: User!
  expiresAt: DateTime!
}

type LogoutPayload {
  success: Boolean!
}

input UpdateUserInput {
  email: String
  displayName: String
}

type UpdateUserPayload {
  user: User!
  errors: [UserError!]
}

type UserError {
  field: String!
  message: String!
  code: String!
}
```

### Example Query

```graphql
query GetCurrentUser {
  currentUser {
    id
    email
    displayName
    sessions(limit: 5) {
      id
      expiresAt
      createdAt
    }
  }
}
```

### Example Mutation

```graphql
mutation LoginUser($email: String!, $password: String!) {
  login(input: { email: $email, password: $password }) {
    token
    user {
      id
      email
      lastLoginAt
    }
    expiresAt
  }
}
```

## Validation Rules Reference

### Common Field Validations

```markdown
**String Fields:**
- min: minimum length (inclusive)
- max: maximum length (inclusive)
- pattern: regex pattern (e.g., /^[a-zA-Z0-9_-]+$/)
- enum: list of allowed values
- format: predefined format (email, url, uuid, date)

**Numeric Fields:**
- min: minimum value (inclusive)
- max: maximum value (inclusive)
- positive: must be > 0
- integer: must be whole number
- precision: decimal places (for float/decimal)

**Date/Time Fields:**
- before: must be before this date
- after: must be after this date
- future: must be in future
- past: must be in past
- format: ISO 8601 recommended

**Relationship Fields:**
- required: foreign key must exist
- cascade: behavior on parent delete/update
- nullable: can be null
- unique: must be unique (or unique combination)

**Array Fields:**
- minItems: minimum number of items
- maxItems: maximum number of items
- uniqueItems: all items must be unique
- itemSchema: validation for each item
```

## Use These Templates

When defining contracts in Phase 5 of technical planning:

1. **Choose appropriate template** based on endpoint type (POST/GET/PATCH/DELETE)
2. **Customize for your domain** (replace auth examples with your entities)
3. **Include all error cases** from specification edge cases
4. **Define validation rules** that match specification requirements
5. **Specify performance targets** based on specification success criteria
6. **Document security considerations** for sensitive operations

The goal is comprehensive contracts that implementers can follow without ambiguity.
