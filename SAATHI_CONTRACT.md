# SAATHI — SYSTEM CONTRACT

Version: 1.0.0
Status: LOCKED
Purpose: Single source of truth for frontend, backend, AI services, database, and integration development.

---

# 1. PRODUCT DEFINITION

## 1.1 Product Name

Saathi

## 1.2 Product Description

Saathi is a voice-first inventory management system designed for small shops.

The system allows shop owners, staff, and authorized outsiders to report inventory events naturally through speech instead of manually entering every stock transaction.

Saathi identifies the speaker, converts speech into text, extracts the inventory claim, evaluates the reliability and plausibility of the claim, detects contradictions, and either automatically confirms the statement or sends it to the owner's review queue.

The inventory is calculated from an append-only statement ledger.

## 1.3 Core Product Principle

The primary interaction model is:

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

## 1.4 Important Architecture Principle

The LLM must NEVER directly modify inventory.

The LLM only produces a structured claim.

The deterministic backend decision engine decides whether the claim is confirmed, flagged, or rejected.

Only CONFIRMED statements can affect calculated inventory.

---

# 2. COMPLETE USER WORKFLOW

## PHASE 0 — ONE-TIME OWNER SETUP

### Step 1 — Owner Registration

The owner:

1. Opens Saathi.
2. Registers using phone number.
3. Completes authentication.
4. Automatically receives the OWNER role.

### Step 2 — Owner Voice Enrollment

The owner records approximately 10–20 seconds of speech.

The system:

1. Receives audio.
2. Validates audio quality.
3. Generates speaker embedding.
4. Stores the voice profile.
5. Associates the voice profile with the owner.

### Step 3 — Shop Setup

The owner enters:

- Shop name
- Products
- Default units

Example:

Rice
Sugar
Oil
Dal

Products can be edited later.

### Step 4 — Add Members

The owner adds members using:

- Name
- Phone number
- Role

Supported roles:

- STAFF
- OUTSIDER

### Step 5 — Member Voice Enrollment

Each member enrolls their voice when they first access Saathi.

### Step 6 — Baseline Stock

The owner enters the initial stock quantity for each product.

This is the primary deliberate manual inventory setup.

Example:

Rice: 100 bags
Sugar: 50 bags
Oil: 30 cartons

After baseline setup, regular inventory changes should be voice-derived whenever possible.

---

# 3. DAILY CAPTURE WORKFLOW

Anyone enrolled can report inventory events naturally.

Supported input channels:

1. Mobile web application
2. Live microphone
3. Phone call through supported telephony integration

Example:

"Ramesh sold five bags of rice."

or:

"Kumar delivered two cartons of oil."

The system performs:

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

---

# 4. DECISION WORKFLOW

## AUTO-CONFIRM

A statement can be automatically confirmed when:

- Speaker identity is sufficiently reliable.
- Claim extraction confidence is sufficient.
- Quantity is plausible.
- No significant contradiction exists.
- Speaker trust is sufficiently high.
- Product and unit are resolved.

The confirmed statement is added to the ledger.

Inventory is recalculated.

The owner does not need to intervene.

## FLAG FOR REVIEW

A statement is flagged when:

- Speaker is unknown or uncertain.
- Quantity is unusually large.
- Speaker trust is low.
- Claim confidence is low.
- A contradiction exists.
- Product or unit cannot be reliably resolved.
- The transaction has significant inventory impact.

Flagged statements appear in the owner's review queue.

## REJECT

A statement can be rejected when:

- It is clearly invalid.
- The owner rejects it.
- It cannot be reliably resolved.
- It violates system rules.

Rejected statements do not affect inventory.

---

# 5. OWNER INTERACTION

The owner can ask questions naturally.

Examples:

"Kitna rice hai?"

"How much rice is left?"

"Aaj kitna rice becha?"

"Ramesh ne kya becha?"

"Kal kitna maal aaya?"

The system converts the question into a structured query, retrieves information from the statement ledger, calculates the result, and provides a concise explanation.

---

# 6. OWNER REVIEW

The owner can review flagged statements at any time.

Actions:

- Approve
- Reject
- Override

Every owner decision must be recorded.

Owner overrides must update the relevant audit history and may influence future speaker trust.

---

# 7. PASSIVE INTELLIGENCE

The system should learn shop-specific information over time.

Examples:

- Unit vocabulary
- Unit conversions
- Typical sales quantities
- Typical delivery quantities
- Speaker reliability
- Product movement patterns
- Review patterns

Learning must remain shop-specific.

One shop's vocabulary must not automatically become another shop's vocabulary.

---

# 8. USER ROLES

## 8.1 OWNER

The owner has full permissions for their shop.

Permissions:

- Register
- Manage shop
- Manage products
- Manage members
- Enroll voice
- View inventory
- Submit inventory statements
- View activity
- Review flagged statements
- Approve statements
- Reject statements
- Override decisions
- View analytics
- Query Saathi
- Manage vocabulary
- Manage settings

## 8.2 STAFF

Permissions:

- Complete voice enrollment
- Submit voice statements
- View permitted inventory information
- Ask permitted queries

Cannot:

- Manage shop
- Manage members
- Change baseline stock
- Approve statements
- Reject statements
- Override decisions

## 8.3 OUTSIDER

Permissions:

- Complete voice enrollment
- Submit inventory statements

Cannot:

- Manage shop
- Manage members
- Change baseline stock
- Review statements
- Approve statements
- Reject statements
- Override decisions

---

# 9. FRONTEND SCREENS

The frontend must contain the following conceptual screens.

## Authentication

- Welcome
- Phone Registration
- OTP Verification
- Login

## Owner Setup

- Create Shop
- Add Products
- Baseline Stock
- Add Members
- Member Details
- Voice Enrollment
- Setup Complete

## Main Application

- Dashboard
- Inventory
- Activity
- Review Queue
- Ask Saathi
- Analytics
- Profile
- Settings

## Voice

- Voice Capture
- Recording
- Processing
- Result
- Confirmation

## Review

- Review List
- Review Detail
- Approve
- Reject
- Override

## Analytics

- Stock Trends
- Product Movement
- Sales Activity
- Speaker Reliability

---

# 10. FRONTEND DESIGN RULES

## 10.1 Visual Style

Saathi must have a professional, modern, minimal, trustworthy visual language.

The interface should feel:

- Professional
- Calm
- Reliable
- Modern
- Clean
- Voice-first

## 10.2 Icon Rule

EMOJIS MUST NOT BE USED ANYWHERE IN THE PROJECT.

Do not use emojis in:

- Buttons
- Navigation
- Cards
- Status indicators
- Empty states
- Error states
- Notifications
- Headings
- Dashboard
- Voice controls
- Documentation UI examples

Use professional SVG icons from a consistent icon library such as Lucide React.

Examples:

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

Icons must have consistent:

- Stroke width
- Size
- Alignment
- Visual weight

## 10.3 Frontend Technology

Preferred:

- React
- Vite
- TypeScript
- Tailwind CSS
- React Router
- Axios
- Lucide React

---

# 11. BACKEND TECHNOLOGY

Preferred backend:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT authentication

AI/ML services:

- Whisper or equivalent multilingual ASR
- pyannote.audio or equivalent speaker embedding system
- LLM API for claim extraction and reasoning

Optional telephony:

- Twilio

---

# 12. API CONVENTIONS

## 12.1 Base URL

All application APIs use:

`/api/v1`

Example:

`/api/v1/auth/login`

## 12.2 Naming

Use lowercase kebab-case or lowercase resource names consistently.

Preferred:

`/api/v1/shops`

`/api/v1/products`

`/api/v1/members`

Do not create duplicate naming conventions.

## 12.3 JSON

All request and response bodies use JSON unless an endpoint explicitly requires multipart form data for audio/file upload.

## 12.4 IDs

Use stable unique identifiers.

Recommended format:

UUID or UUID-compatible string.

---

# 13. AUTHENTICATION API

## POST /api/v1/auth/register

Purpose:

Register a new owner.

Request:

```json
{
  "phone": "+91XXXXXXXXXX",
  "name": "Owner Name"
}