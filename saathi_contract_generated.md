# SAATHI --- SYSTEM CONTRACT

**Version:** 1.0.0\
**Status:** LOCKED\
**Purpose:** Single source of truth for frontend, backend, AI services,
database, and integration development.

------------------------------------------------------------------------

# 1. PRODUCT DEFINITION

## 1.1 Product Name

Saathi

## 1.2 Product Description

Saathi is a voice-first inventory management system designed for small
shops.

The system allows shop owners, staff, and authorized outsiders to report
inventory events naturally through speech instead of manually entering
every stock transaction.

Saathi identifies the speaker, converts speech into text, extracts the
inventory claim, evaluates the reliability and plausibility of the
claim, detects contradictions, and either automatically confirms the
statement or sends it to the owner's review queue.

The inventory is calculated from an append-only statement ledger.

## 1.3 Core Product Principle

The primary interaction model is:

``` text
Natural Speech
→ Speaker Identification
→ Speech Recognition
→ Claim Extraction
→ Entity Resolution
→ Unit Normalization
→ Trust Evaluation
→ Plausibility Check
→ Contradiction Check
→ Decision
→ Statement Ledger
→ Stock Calculation
```

## 1.4 Important Architecture Principle

The LLM must **NEVER** directly modify inventory.

The LLM only produces a structured claim.

The deterministic backend decision engine decides whether the claim is
confirmed, flagged, or rejected.

Only `CONFIRMED` statements can affect calculated inventory.

The backend/database is authoritative. The frontend must never calculate
or mutate authoritative inventory.

------------------------------------------------------------------------

# 2. COMPLETE USER WORKFLOW

## 2.1 Phase 0 --- One-Time Owner Setup

### Step 1 --- Owner Registration

The owner:

1.  Opens Saathi.
2.  Registers using a phone number.
3.  Completes authentication.
4.  Automatically receives the `OWNER` role.

### Step 2 --- Owner Voice Enrollment

The owner records approximately 10--20 seconds of speech.

The system:

1.  Receives audio.
2.  Validates audio quality.
3.  Generates a speaker embedding.
4.  Stores the voice profile.
5.  Associates the voice profile with the owner.

### Step 3 --- Shop Setup

The owner enters:

-   Shop name
-   Products
-   Default units

Example:

``` text
Rice
Sugar
Oil
Dal
```

Products can be edited later.

### Step 4 --- Add Members

The owner adds members using:

-   Name
-   Phone number
-   Role

Supported roles:

-   `STAFF`
-   `OUTSIDER`

### Step 5 --- Member Voice Enrollment

Each member enrolls their voice when they first access Saathi.

### Step 6 --- Baseline Stock

The owner enters the initial stock quantity for each product.

This is the primary deliberate manual inventory setup.

Example:

``` text
Rice: 100 bags
Sugar: 50 bags
Oil: 30 cartons
```

After baseline setup, regular inventory changes should be voice-derived
whenever possible.

------------------------------------------------------------------------

# 3. DAILY CAPTURE WORKFLOW

Anyone enrolled can report inventory events naturally.

Supported input channels:

1.  Mobile web application
2.  Live microphone
3.  Phone call through supported telephony integration

Examples:

``` text
"Ramesh sold five bags of rice."

"Kumar delivered two cartons of oil."
```

The system performs:

``` text
Audio
→ Speaker Identification
→ Speech-to-Text
→ Claim Extraction
→ Entity Resolution
→ Unit Normalization
→ Trust Evaluation
→ Plausibility Check
→ Contradiction Detection
→ Decision
```

------------------------------------------------------------------------

# 4. DECISION WORKFLOW

## 4.1 Auto-Confirm

A statement can be automatically confirmed when:

-   Speaker identity is sufficiently reliable.
-   Claim extraction confidence is sufficient.
-   Quantity is plausible.
-   No significant contradiction exists.
-   Speaker trust is sufficiently high.
-   Product and unit are resolved.

The confirmed statement is added to the ledger.

Inventory is recalculated from the baseline and confirmed statement
ledger.

The owner does not need to intervene.

## 4.2 Flag for Review

A statement is flagged when:

-   Speaker is unknown or uncertain.
-   Quantity is unusually large.
-   Speaker trust is low.
-   Claim confidence is low.
-   A contradiction exists.
-   Product or unit cannot be reliably resolved.
-   The transaction has significant inventory impact.

Flagged statements appear in the owner's review queue.

## 4.3 Reject

A statement can be rejected when:

-   It is clearly invalid.
-   The owner rejects it.
-   It cannot be reliably resolved.
-   It violates system rules.

Rejected statements do not affect inventory.

------------------------------------------------------------------------

# 5. OWNER INTERACTION

The owner can ask questions naturally.

Examples:

``` text
"Kitna rice hai?"
"How much rice is left?"
"Aaj kitna rice becha?"
"Ramesh ne kya becha?"
"Kal kitna maal aaya?"
```

The system:

1.  Converts the question into a structured query.
2.  Retrieves relevant information from the statement ledger.
3.  Calculates the result using authoritative backend data.
4.  Provides a concise explanation.
5.  Never invents inventory values.

------------------------------------------------------------------------

# 6. OWNER REVIEW

The owner can review flagged statements at any time.

Actions:

-   Approve
-   Reject
-   Override

Every owner decision must be recorded.

Owner overrides must update the relevant audit history and may influence
future speaker trust.

------------------------------------------------------------------------

# 7. PASSIVE INTELLIGENCE

The system should learn shop-specific information over time.

Examples:

-   Unit vocabulary
-   Unit conversions
-   Typical sales quantities
-   Typical delivery quantities
-   Speaker reliability
-   Product movement patterns
-   Review patterns

Learning must remain shop-specific.

One shop's vocabulary must not automatically become another shop's
vocabulary.

------------------------------------------------------------------------

# 8. USER ROLES

## 8.1 OWNER

The owner has full permissions for their shop.

Permissions:

-   Register
-   Manage shop
-   Manage products
-   Manage members
-   Enroll voice
-   View inventory
-   Submit inventory statements
-   View activity
-   Review flagged statements
-   Approve statements
-   Reject statements
-   Override decisions
-   View analytics
-   Query Saathi
-   Manage vocabulary
-   Manage settings

## 8.2 STAFF

Permissions:

-   Complete voice enrollment
-   Submit voice statements
-   View permitted inventory information
-   Ask permitted queries

Cannot:

-   Manage shop
-   Manage members
-   Change baseline stock
-   Approve statements
-   Reject statements
-   Override decisions

## 8.3 OUTSIDER

Permissions:

-   Complete voice enrollment
-   Submit inventory statements

Cannot:

-   Manage shop
-   Manage members
-   Change baseline stock
-   Review statements
-   Approve statements
-   Reject statements
-   Override decisions

------------------------------------------------------------------------

# 9. FRONTEND SCREENS

The frontend must contain the following conceptual screens.

## Authentication

-   Welcome
-   Phone Registration
-   OTP Verification
-   Login

## Owner Setup

-   Create Shop
-   Add Products
-   Baseline Stock
-   Add Members
-   Member Details
-   Voice Enrollment
-   Setup Complete

## Main Application

-   Dashboard
-   Inventory
-   Activity
-   Review Queue
-   Ask Saathi
-   Analytics
-   Profile
-   Settings

## Voice

-   Voice Capture
-   Recording
-   Processing
-   Result
-   Confirmation

## Review

-   Review List
-   Review Detail
-   Approve
-   Reject
-   Override

## Analytics

-   Stock Trends
-   Product Movement
-   Sales Activity
-   Speaker Reliability

------------------------------------------------------------------------

# 10. FRONTEND DESIGN RULES

## 10.1 Visual Style

Saathi must have a professional, modern, minimal, trustworthy visual
language.

The interface should feel:

-   Professional
-   Calm
-   Reliable
-   Modern
-   Clean
-   Voice-first

## 10.2 Icon Rule

**EMOJIS MUST NOT BE USED ANYWHERE IN THE PROJECT.**

Do not use emojis in:

-   Buttons
-   Navigation
-   Cards
-   Status indicators
-   Empty states
-   Error states
-   Notifications
-   Headings
-   Dashboard
-   Voice controls
-   Documentation UI examples

Use professional SVG icons from a consistent icon library such as Lucide
React.

Examples:

``` text
Mic
CheckCircle
AlertTriangle
User
Store
Package
History
Search
Settings
Bell
Phone
ChevronRight
```

Icons must have consistent:

-   Stroke width
-   Size
-   Alignment
-   Visual weight

## 10.3 Frontend Technology

Preferred:

-   React
-   Vite
-   TypeScript
-   Tailwind CSS
-   React Router
-   Axios
-   Lucide React

------------------------------------------------------------------------

# 11. BACKEND TECHNOLOGY

Preferred backend:

-   Python
-   FastAPI
-   Pydantic
-   SQLAlchemy
-   PostgreSQL
-   Alembic
-   JWT authentication

AI/ML services:

-   Whisper or equivalent multilingual ASR
-   pyannote.audio or equivalent speaker embedding system
-   LLM API for claim extraction and reasoning

Optional telephony:

-   Twilio

------------------------------------------------------------------------

# 12. API CONVENTIONS

## 12.1 Base Path

All application APIs use:

``` text
/api/v1
```

Examples:

``` text
/api/v1/auth/register
/api/v1/shops
/api/v1/products
/api/v1/health
```

The health endpoint is also versioned:

``` text
GET /api/v1/health
```

Do **not** create a separate application endpoint such as:

``` text
GET /health
```

## 12.2 Naming

Use lowercase resource names consistently.

Preferred:

``` text
/api/v1/shops
/api/v1/products
/api/v1/members
/api/v1/statements
```

Use nested resources where ownership/context is required.

Do not create duplicate naming conventions.

## 12.3 JSON

All request and response bodies use JSON unless an endpoint explicitly
requires multipart form data for audio/file upload.

## 12.4 IDs

Use stable unique identifiers.

Recommended format:

-   UUID
-   UUID-compatible string

## 12.5 Authentication

Authenticated endpoints use:

``` text
Authorization: Bearer <access_token>
```

## 12.6 Content Type

JSON endpoints use:

``` text
Content-Type: application/json
```

Audio upload endpoints may use:

``` text
Content-Type: multipart/form-data
```

## 12.7 Standard Success Response

Where a response wrapper is useful, use:

``` json
{
  "success": true,
  "data": {}
}
```

## 12.8 Standard Error Response

All application errors should follow:

``` json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message.",
    "details": null
  }
}
```

Do not expose stack traces or internal implementation details to
clients.

------------------------------------------------------------------------

# 13. HEALTH AND SYSTEM API

## GET /api/v1/health

Purpose:

Verify that the Saathi backend application is running.

Example response:

``` json
{
  "success": true,
  "status": "healthy"
}
```

The basic health endpoint must not expose:

-   Secrets
-   Environment variables
-   Database credentials
-   API keys
-   JWT secrets
-   Internal stack traces

A future database/readiness check may be implemented separately. Do not
overload the basic health endpoint with sensitive diagnostics.

------------------------------------------------------------------------

# 14. AUTHENTICATION API

## POST /api/v1/auth/register

Purpose:

Register a new owner.

Request:

``` json
{
  "phone": "+91XXXXXXXXXX",
  "name": "Owner Name"
}
```

Response should provide the registration/verification state according to
the authentication implementation.

A newly registered owner receives the `OWNER` role after successful
registration/authentication.

## POST /api/v1/auth/verify

Purpose:

Verify the phone authentication challenge/OTP.

The exact OTP provider may be implemented independently, but the API
contract must remain stable.

## POST /api/v1/auth/refresh

Purpose:

Refresh an access token using the supported refresh-token mechanism.

## GET /api/v1/users/me

Purpose:

Return the authenticated user's profile and role.

------------------------------------------------------------------------

# 15. SHOP API

## POST /api/v1/shops

Create a shop for the authenticated owner.

## GET /api/v1/shops/{shop_id}

Return shop details.

## PUT /api/v1/shops/{shop_id}

Update shop details.

Only authorized users may perform shop management.

------------------------------------------------------------------------

# 16. PRODUCT API

## POST /api/v1/shops/{shop_id}/products

Create a product.

Example:

``` json
{
  "name": "Rice",
  "default_unit": "bag"
}
```

## GET /api/v1/shops/{shop_id}/products

Return products belonging to the shop.

## PUT /api/v1/products/{product_id}

Update a product.

## DELETE /api/v1/products/{product_id}

Delete/deactivate a product according to the implementation's
referential-integrity rules.

Historical statements must not be silently rewritten because a product
is edited or deactivated.

------------------------------------------------------------------------

# 17. MEMBER API

## POST /api/v1/shops/{shop_id}/members

Add a member.

Request:

``` json
{
  "name": "Ramesh",
  "phone": "+91XXXXXXXXXX",
  "role": "STAFF"
}
```

Supported roles:

``` text
STAFF
OUTSIDER
```

## GET /api/v1/shops/{shop_id}/members

List shop members.

## PUT /api/v1/members/{member_id}

Update member information.

## DELETE /api/v1/members/{member_id}

Deactivate/remove a member according to implementation rules.

Historical statements must retain their original actor identity.

------------------------------------------------------------------------

# 18. VOICE ENROLLMENT API

## POST /api/v1/voice/enroll

Purpose:

Enroll a user's voice.

The endpoint accepts audio through multipart form data.

Processing:

``` text
Audio
→ Quality Validation
→ Speaker Embedding
→ Voice Profile
→ User Association
```

The response must communicate one of the defined enrollment outcomes:

``` text
ENROLLED
LOW_QUALITY
FAILED
```

Voice embeddings must be protected as sensitive biometric-related data.

------------------------------------------------------------------------

# 19. VOICE PROCESSING API

## POST /api/v1/voice/process

Purpose:

Process an inventory voice statement.

Input may include:

-   Audio
-   Optional channel metadata
-   Optional device/session metadata

Processing:

``` text
Audio
→ Speaker Identification
→ Speech Recognition
→ Claim Extraction
→ Entity Resolution
→ Unit Normalization
→ Trust Evaluation
→ Plausibility Check
→ Contradiction Check
→ Decision
```

The LLM must only produce a structured claim and reasoning.

The deterministic backend decides the final statement status.

The endpoint must never allow an LLM response to directly mutate
inventory.

------------------------------------------------------------------------

# 20. CLAIM EXTRACTION CONTRACT

The normalized claim should contain, where available:

``` json
{
  "product": "Rice",
  "quantity": 5,
  "unit": "bag",
  "direction": "OUT",
  "actor": "Ramesh",
  "time": null
}
```

Fields:

-   `product`
-   `quantity`
-   `unit`
-   `direction`
-   `actor`
-   `time`

The extraction layer may return unresolved/null values when the speech
does not contain sufficient information.

It must not invent missing facts.

------------------------------------------------------------------------

# 21. SPEAKER IDENTIFICATION

Speaker identification combines available signals such as:

-   Voice embedding similarity
-   Enrolled voice profile
-   Phone number
-   Device/session information

Possible speaker states:

``` text
IDENTIFIED
LOW_CONFIDENCE
UNKNOWN
```

Speaker identity must not be treated as certain solely because an LLM
inferred a person's name from the transcript.

------------------------------------------------------------------------

# 22. SPEECH RECOGNITION

The system must support multilingual and code-mixed speech where the
selected ASR system permits it.

Potential technologies include:

-   Whisper
-   Cloud multilingual speech-to-text
-   Equivalent ASR systems

ASR output must retain the original transcript sufficiently for later
auditing/debugging.

------------------------------------------------------------------------

# 23. ENTITY RESOLUTION

Entity resolution maps natural language references to shop-specific
entities.

Examples:

``` text
"rice bag"
"chawal"
"rice"
```

may resolve to the same shop product when the shop vocabulary
establishes that relationship.

Resolution must be shop-specific.

Unknown entities must not silently map to unrelated products.

------------------------------------------------------------------------

# 24. SHOP-SPECIFIC VOCABULARY API

## POST /api/v1/vocabulary

Create or update a shop-specific vocabulary mapping.

## GET /api/v1/vocabulary

Retrieve vocabulary mappings for the authorized shop.

Vocabulary may include:

-   Product aliases
-   Unit aliases
-   Unit conversions
-   Local terminology

Example:

``` text
"chawal" → Rice
"carton" → shop-defined unit
```

A vocabulary mapping must not automatically propagate between shops.

------------------------------------------------------------------------

# 25. UNIT NORMALIZATION

The system must normalize units before inventory calculation.

Examples:

``` text
bags
bag
cartons
carton
```

may be normalized according to shop-specific configuration.

Where a conversion is required, the conversion must be explicitly known
or configured.

The system must not invent conversion ratios.

------------------------------------------------------------------------

# 26. TRUST ENGINE

The trust engine evaluates speaker reliability.

Inputs may include:

-   Speaker identity confidence
-   Historical speaker reliability
-   Previous owner approvals/rejections
-   Override history
-   Statement consistency

Trust must be stored as auditable history rather than as an unexplained
opaque number.

Trust is shop-specific.

One shop's trust assessment must not automatically transfer to another
shop.

------------------------------------------------------------------------

# 27. PLAUSIBILITY ENGINE

The plausibility engine is deterministic.

It evaluates whether a claim is reasonable relative to shop-specific
historical behavior and current inventory context.

Examples:

-   Typical sales quantity
-   Typical delivery quantity
-   Current available stock
-   Recent transaction patterns

The plausibility engine must produce explainable deterministic results.

It must not silently modify the statement.

------------------------------------------------------------------------

# 28. CONTRADICTION ENGINE

The contradiction engine compares a new claim against relevant recent
statements and confirmed information.

Potential contradiction examples:

-   Conflicting quantities for the same event
-   Impossible stock movement
-   Duplicate transaction
-   Conflicting product/action
-   Conflicting actor attribution

A contradiction should cause the statement to be flagged/rejected
according to the decision rules.

------------------------------------------------------------------------

# 29. DECISION ENGINE

The decision engine is deterministic.

It combines:

-   Speaker confidence
-   Claim confidence
-   Trust
-   Plausibility
-   Contradiction result
-   Product resolution
-   Unit resolution
-   Inventory impact

Possible decisions:

``` text
AUTO_CONFIRMED
REQUIRES_REVIEW
REJECTED
```

The decision engine is the only component authorized to determine
whether a statement can affect inventory.

------------------------------------------------------------------------

# 30. STATEMENT LEDGER

Statements are append-only records.

A statement should preserve information such as:

-   Statement ID
-   Shop ID
-   User/actor ID when known
-   Speaker status
-   Original transcript
-   Structured claim
-   Decision
-   Statement status
-   Confidence information
-   Timestamps
-   Source/channel
-   Review information
-   Override information
-   Audit metadata

Historical statements must not be silently rewritten.

Corrections should be represented through review/override/audit
mechanisms.

------------------------------------------------------------------------

# 31. STATEMENT API

## GET /api/v1/statements

List statements for the authorized shop.

Supported filtering may include:

-   Product
-   User
-   Status
-   Decision
-   Date range
-   Direction

## GET /api/v1/statements/{statement_id}

Return a statement and its relevant processing/audit information.

------------------------------------------------------------------------

# 32. STATEMENT STATUS

Allowed statement statuses:

``` text
PENDING
PROCESSING
CONFIRMED
FLAGGED
REJECTED
```

Do not create alternate spellings such as:

``` text
APPROVED
APPROVE
REVIEW
FAILED
```

unless the contract is explicitly versioned and updated first.

------------------------------------------------------------------------

# 33. INVENTORY BASELINE API

## POST /api/v1/shops/{shop_id}/baseline

Create/update the initial inventory baseline according to owner
permissions and baseline rules.

Example:

``` json
{
  "product_id": "uuid",
  "quantity": 100,
  "unit": "bag"
}
```

Baseline changes must be auditable.

------------------------------------------------------------------------

# 34. INVENTORY ENGINE

## 34.1 Authoritative Formula

Current stock is calculated as:

``` text
Latest Baseline
+ Confirmed IN statements
- Confirmed OUT statements
```

Only confirmed statements affect calculated inventory.

## 34.2 Inventory APIs

### GET /api/v1/shops/{shop_id}/inventory

Return current inventory for the shop.

### GET /api/v1/products/{product_id}/inventory

Return current inventory for one product.

### GET /api/v1/products/{product_id}/history

Return the inventory movement/history derived from the baseline and
statement ledger.

## 34.3 Inventory Integrity

The following components must never directly write authoritative
inventory:

-   Frontend
-   LLM
-   ASR
-   Speaker identification
-   Claim extraction
-   Trust engine
-   Plausibility engine
-   Contradiction engine

Only confirmed ledger events and authorized baseline operations can
affect calculated inventory.

------------------------------------------------------------------------

# 35. REVIEW QUEUE API

## GET /api/v1/reviews

List statements requiring owner review.

## GET /api/v1/reviews/{review_id}

Return review details.

## POST /api/v1/reviews/{review_id}/approve

Approve a flagged statement.

## POST /api/v1/reviews/{review_id}/reject

Reject a flagged statement.

Only authorized owners may perform these actions.

------------------------------------------------------------------------

# 36. OWNER OVERRIDE API

## POST /api/v1/statements/{statement_id}/override

Purpose:

Allow the owner to explicitly override a statement decision.

Every override must record:

-   Owner ID
-   Previous decision/status
-   New decision/status
-   Reason when provided
-   Timestamp
-   Audit metadata

Overrides must never erase the original decision history.

------------------------------------------------------------------------

# 37. TRUST HISTORY

Trust changes must be auditable.

The system should retain:

-   Previous trust state
-   New trust state
-   Trigger/event
-   Related statement/review
-   Timestamp

Owner actions may influence future speaker trust.

------------------------------------------------------------------------

# 38. OWNER QUERY API

## POST /api/v1/query

Purpose:

Allow the owner to ask natural-language inventory questions.

Example request:

``` json
{
  "query": "How much rice is left?"
}
```

The query system should:

``` text
Natural Language Question
→ Intent Detection
→ Entity Resolution
→ Authoritative Ledger Retrieval
→ Deterministic Calculation
→ Explanation
```

The LLM may assist with intent parsing and explanation.

The LLM must not invent the numerical answer.

------------------------------------------------------------------------

# 39. QUERY INTENTS

Supported query intents may include:

``` text
CURRENT_STOCK
TODAY_SALES
PRODUCT_ACTIVITY
ACTOR_ACTIVITY
RECENT_INBOUND
RECENT_OUTBOUND
INVENTORY_HISTORY
```

The backend should reject or safely handle unsupported questions.

------------------------------------------------------------------------

# 40. EXPLAINABILITY

Saathi should provide concise explanations for important decisions.

Example:

``` text
Confirmed because:
- Ramesh was identified with high confidence.
- Rice was resolved to the shop's Rice product.
- Quantity was within the normal sales range.
- No contradiction was detected.
```

Explanations must reflect actual backend evidence.

Do not generate explanations that claim checks were performed when they
were not.

------------------------------------------------------------------------

# 41. TIME DECAY

Low-stakes flagged statements may become eligible for automatic
confirmation after a configured period if the contract's trust/risk
rules permit it.

Time decay must:

-   Be deterministic
-   Be auditable
-   Never silently bypass high-risk conditions
-   Never erase the original review state/history

------------------------------------------------------------------------

# 42. ANALYTICS

Analytics must be derived from authoritative statement and inventory
data.

Possible analytics:

-   Stock trends
-   Product movement
-   Sales activity
-   Speaker reliability
-   Review activity
-   Frequently moved products
-   Inventory changes over time

Analytics must not create a second authoritative inventory source.

------------------------------------------------------------------------

# 43. TELEPHONY / TWILIO

Telephony is optional.

If implemented:

``` text
Incoming Call
→ Phone Number Identification
→ Audio Capture
→ Speaker Identification
→ Speech Recognition
→ Claim Extraction
→ Entity Resolution
→ Trust/Plausibility/Contradiction
→ Decision
→ Statement Ledger
```

Phone number identification is an additional signal and does not replace
voice identification where voice verification is required.

Telephony credentials must be stored only in environment
variables/secrets management.

------------------------------------------------------------------------

# 44. DATABASE ENTITIES

The implementation should support, at minimum, the following conceptual
entities:

``` text
User
Shop
ShopMember
Product
Baseline
VoiceProfile
VocabularyEntry
Statement
StatementProcessing
Review
TrustHistory
AuditLog
```

The exact physical schema may use additional supporting tables.

Relationships must preserve shop isolation and historical auditability.

------------------------------------------------------------------------

# 45. DATABASE RULES

## 45.1 Shop Isolation

Users must only access data permitted for their shop and role.

## 45.2 Historical Integrity

Historical statements must remain auditable.

## 45.3 Inventory Source of Truth

The statement ledger plus baseline is the source of truth for inventory
calculation.

## 45.4 Soft Deactivation

Where historical relationships exist, products/users/members should
generally be deactivated rather than physically deleted if physical
deletion would destroy audit integrity.

------------------------------------------------------------------------

# 46. CORE ENUMS

## Roles

``` text
OWNER
STAFF
OUTSIDER
```

## Statement Status

``` text
PENDING
PROCESSING
CONFIRMED
FLAGGED
REJECTED
```

## Decision

``` text
AUTO_CONFIRMED
REQUIRES_REVIEW
REJECTED
```

## Direction

``` text
IN
OUT
```

## Speaker Status

``` text
IDENTIFIED
LOW_CONFIDENCE
UNKNOWN
```

## Voice Enrollment Status

``` text
ENROLLED
LOW_QUALITY
FAILED
```

Do not introduce duplicate semantic enum values.

------------------------------------------------------------------------

# 47. SECURITY REQUIREMENTS

The implementation must:

-   Hash/store credentials securely where applicable.
-   Never expose secrets to the frontend.
-   Never hardcode API keys.
-   Use authenticated API access.
-   Enforce role-based authorization.
-   Enforce shop-level data isolation.
-   Validate all input.
-   Validate uploaded audio.
-   Apply upload size/type restrictions.
-   Protect voice embeddings and audio data.
-   Avoid exposing internal stack traces.
-   Log security-relevant events.
-   Maintain audit history for owner actions.

------------------------------------------------------------------------

# 48. AUDIO AND VOICE PRIVACY

Voice data is sensitive.

The system must:

-   Store only what is necessary.
-   Protect voice embeddings.
-   Restrict access by role and shop.
-   Avoid exposing raw audio through public URLs.
-   Apply retention rules where defined by deployment requirements.
-   Avoid logging raw audio or sensitive biometric information.

------------------------------------------------------------------------

# 49. OBSERVABILITY

The backend should support:

-   Structured logging
-   Request correlation IDs
-   Processing-stage timing
-   Error logging
-   AI/ASR processing metrics
-   Database error monitoring
-   Decision-engine metrics

Do not log:

-   Secrets
-   Access tokens
-   Raw sensitive audio
-   Unnecessary personal data

------------------------------------------------------------------------

# 50. FRONTEND/BACKEND RESPONSIBILITY

## Frontend

The frontend is responsible for:

-   User interface
-   Navigation
-   Forms
-   Audio capture
-   API communication
-   Displaying backend results
-   Displaying explanations
-   Role-aware UI

The frontend is **not** authoritative for:

-   Inventory calculations
-   Trust decisions
-   Plausibility decisions
-   Contradiction decisions
-   Statement confirmation
-   Security authorization

## Backend

The backend is responsible for:

-   Authentication
-   Authorization
-   Data validation
-   Business logic
-   Statement processing
-   Inventory calculation
-   Trust
-   Plausibility
-   Contradiction
-   Decision making
-   Audit history
-   API contracts

## AI Services

AI services are responsible for:

-   Speech recognition
-   Speaker identification
-   Claim extraction
-   Query intent parsing
-   Natural-language explanation

AI services must not directly mutate authoritative inventory.

------------------------------------------------------------------------

# 51. API CHANGE POLICY

The contract is locked.

Before changing:

-   Endpoint paths
-   HTTP methods
-   Request fields
-   Response fields
-   Enum values
-   Authentication behavior
-   Database semantics
-   Inventory formula

the contract must be updated first.

The version should be incremented when a breaking change is introduced.

Frontend and backend implementations must follow the same contract
version.

------------------------------------------------------------------------

# 52. MOCK DATA RULE

Mock data may be used only for isolated UI development when the real API
is not yet available.

Mock data must:

-   Be clearly separated from production services.
-   Never be presented as authoritative inventory.
-   Never be committed as a replacement for real backend behavior.
-   Be removable without changing production architecture.

------------------------------------------------------------------------

# 53. LLM RULES

The LLM may:

-   Parse natural-language claims.
-   Extract structured fields.
-   Resolve natural-language intent.
-   Generate explanations.

The LLM may not:

-   Directly update inventory.
-   Directly approve statements.
-   Directly reject statements.
-   Change trust values.
-   Bypass deterministic validation.
-   Invent missing quantities.
-   Invent product mappings.
-   Invent unit conversions.
-   Invent historical transactions.

All critical decisions must be made by deterministic backend logic.

------------------------------------------------------------------------

# 54. ERROR HANDLING

Use stable error codes.

Examples:

``` text
AUTH_REQUIRED
AUTH_INVALID
FORBIDDEN
NOT_FOUND
VALIDATION_ERROR
INVALID_AUDIO
VOICE_ENROLLMENT_FAILED
SPEAKER_IDENTIFICATION_FAILED
TRANSCRIPTION_FAILED
CLAIM_EXTRACTION_FAILED
PRODUCT_NOT_RESOLVED
UNIT_NOT_RESOLVED
STATEMENT_REQUIRES_REVIEW
DATABASE_ERROR
INTERNAL_ERROR
```

Error messages should be human-readable.

Internal details belong in server logs, not API responses.

------------------------------------------------------------------------

# 55. DEVELOPMENT OWNERSHIP

## Gemini / Frontend AI

Responsible for:

-   Frontend UI/UX
-   React implementation
-   Responsive design
-   Component system
-   Frontend routing
-   API integration layer
-   Voice capture interface
-   Dashboard
-   Inventory screens
-   Review screens
-   Query interface
-   Analytics screens

Must follow the API contract exactly.

Must not invent backend endpoints.

## Claude / Backend AI

Responsible for:

-   Backend architecture
-   FastAPI APIs
-   Database models
-   Migrations
-   Authentication
-   Authorization
-   Voice pipeline
-   ASR integration
-   Speaker identification
-   Claim extraction
-   Entity resolution
-   Vocabulary
-   Trust engine
-   Plausibility engine
-   Contradiction engine
-   Decision engine
-   Statement ledger
-   Inventory calculation
-   Review system
-   Owner override
-   Query engine
-   Analytics APIs
-   Testing of backend logic

Must follow the API contract exactly.

## Human Integrator

Responsible for:

-   Integrating frontend and backend
-   Environment configuration
-   End-to-end testing
-   Debugging
-   Resolving integration issues
-   Testing real audio
-   Testing real user workflows
-   Deployment
-   Final hackathon demo validation

------------------------------------------------------------------------

# 56. NON-NEGOTIABLE RULES

1.  `SAATHI_CONTRACT.md` is the single source of truth.
2.  The contract must not be silently changed.
3.  All application APIs use `/api/v1`.
4.  `GET /api/v1/health` is the standard Phase 0 application health
    endpoint.
5.  The LLM must never directly modify inventory.
6.  Only confirmed statements affect inventory.
7.  Inventory is derived from baseline plus confirmed statements.
8.  The statement ledger is append-only/auditable.
9.  Trust decisions are deterministic and auditable.
10. Shop-specific learning must remain isolated by shop.
11. Frontend must never become the inventory source of truth.
12. No emojis anywhere in the Saathi project.
13. Use professional SVG icons such as Lucide React.
14. Secrets must never be committed.
15. Role permissions must be enforced by the backend.
16. Historical records must remain auditable.
17. AI-generated explanations must reflect actual backend evidence.
18. New API conventions must not be invented.
19. Breaking API changes require a contract version update.
20. Any conflict between an implementation prompt and this contract must
    be reported and resolved against this contract.

------------------------------------------------------------------------

# 57. COMPLETE SYSTEM FLOW

``` text
OWNER REGISTRATION
        ↓
PHONE AUTHENTICATION
        ↓
OWNER ROLE
        ↓
VOICE ENROLLMENT
        ↓
SHOP CREATION
        ↓
PRODUCT SETUP
        ↓
MEMBER SETUP
        ↓
MEMBER VOICE ENROLLMENT
        ↓
BASELINE STOCK
        ↓
────────────────────────────────
        DAILY OPERATION
────────────────────────────────
        ↓
VOICE / PHONE INPUT
        ↓
AUDIO
        ↓
SPEAKER IDENTIFICATION
        ↓
SPEECH RECOGNITION
        ↓
CLAIM EXTRACTION
        ↓
ENTITY RESOLUTION
        ↓
UNIT NORMALIZATION
        ↓
TRUST EVALUATION
        ↓
PLAUSIBILITY CHECK
        ↓
CONTRADICTION CHECK
        ↓
DETERMINISTIC DECISION ENGINE
        ↓
   ┌───────────────┬──────────────────┐
   ↓               ↓                  ↓
CONFIRMED       FLAGGED            REJECTED
   ↓               ↓                  ↓
LEDGER          REVIEW QUEUE       NO INVENTORY
   ↓               ↓
STOCK           OWNER DECISION
CALCULATION         ↓
                 LEDGER
                    ↓
                 STOCK
                    ↓
             OWNER QUESTIONS
                    ↓
          AUTHORITATIVE QUERY
                    ↓
               EXPLANATION
```

------------------------------------------------------------------------

# 58. CONTRACT COMPLETION RULE

Any future phase must:

1.  Read this contract first.
2.  Follow its terminology.
3.  Follow its endpoint definitions.
4.  Follow its enums.
5.  Follow its inventory rules.
6.  Follow its role permissions.
7.  Follow its AI boundaries.
8.  Avoid introducing conflicting architecture.
9.  Report ambiguities or conflicts before implementation.
10. Treat this document as authoritative until a new version is formally
    issued.
