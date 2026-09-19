# Saathi

## Voice-First, Trust-Aware Inventory Management

**Saathi** is a voice-first inventory management system designed for small shops. It converts natural speech into reliable inventory updates while considering **who made the statement, what was said, and whether the statement can be trusted**.

Instead of manually entering stock:

> "Received 20 bags of rice."

Saathi identifies the speaker, understands the statement, resolves the product and unit, validates the transaction, and updates inventory only when the statement passes the required trust and validation checks.

---

## 1. Problem

Small shops commonly face:

- Manual and time-consuming inventory entry
- Incorrect or accidental stock updates
- Unknown or unauthorized people reporting transactions
- Ambiguous product names and units
- Duplicate or contradictory statements
- No reliable explanation of how current stock was calculated

A conventional voice-to-text system only converts **speech into text**. It does not determine whether the information should be **trusted and allowed to change inventory**.

---

## 2. Our Solution

Saathi introduces a **Trust-Aware Voice Inventory Pipeline**:

``
Voice Input
     ↓
Speaker Identification
     ↓
Speech Recognition
     ↓
Claim Extraction
     ↓
Entity & Unit Resolution
     ↓
Trust Engine
     ↓
Plausibility & Contradiction Checks
     ↓
Deterministic Decision
     ↓
Statement Ledger
     ↓
Inventory
`

The system ensures that every inventory update has a traceable statement and a clear decision behind it.

---

## 3. Role-Based Access

Saathi supports three types of users:

| Role | Access |
|------|--------|
| **OWNER** | Full control over the shop, products, members, inventory, reviews, and settings |
| **WORKER** | Can submit voice-based inventory statements and access permitted inventory information |
| **OUTSIDER** | Can submit inventory statements through voice with restricted access |

---

## 4. OWNER

The **Owner** has complete control over the shop.

### Permissions

- Manage shop and products
- Add and manage Workers and Outsiders
- Enroll voice profiles
- Set baseline inventory
- View inventory and statement history
- Approve, reject, or override flagged statements
- Manage vocabulary and system settings
- Query inventory using natural language

---

## 5. WORKER

The **Worker** can perform permitted inventory operations but cannot manage the shop.

### Permissions

- Enroll voice
- Submit inventory statements
- Record stock **IN / OUT** transactions
- View permitted inventory information
- Use inventory queries

### Restrictions

- Cannot manage members
- Cannot change shop settings
- Cannot approve, reject, or override statements
- Cannot modify baseline inventory

---

## 6. OUTSIDER

An **Outsider** has the most restricted access.

### Permissions

- Enroll voice
- Submit inventory-related statements

### Restrictions

- Cannot manage products
- Cannot manage members
- Cannot modify baseline inventory
- Cannot approve, reject, or override statements

All Outsider statements are subjected to the **Trust Engine** before they can affect inventory.

---

## 7. Trust Engine

The **Trust Engine** is the core of Saathi.

It considers both:

### Who is speaking?

- Speaker identity
- User role
- Voice profile

### What are they saying?

- Product
- Quantity
- Unit
- Transaction type
- Inventory claim

The system then performs validation before deciding whether the statement can affect inventory.

'
                         SAATHI
                            |
                            v
                     Voice Input
                            |
                            v
                  Speaker Identification
                            |
                            v
                   Speech Recognition
                            |
                            v
                    Claim Extraction
                            |
                            v
                 Entity / Unit Resolution
                            |
                            v
                      TRUST ENGINE
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
         CONFIRMED       FLAGGED       REJECTED
              |             |             |
              v             v             v
       Statement Ledger   Owner Review   No Change
              |
              v
          INVENTORY


---

## 8. Decision Outcomes

| Decision | Meaning | Inventory Effect |
|----------|---------|------------------|
| **CONFIRMED** | Statement passes identity and validation checks | Inventory is updated |
| **FLAGGED** | Statement requires additional verification | Owner reviews it |
| **REJECTED** | Statement fails required checks | No inventory change |

This makes every inventory update **traceable, explainable, and controlled**.
