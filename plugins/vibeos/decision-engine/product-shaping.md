# VibeOS Plugin — Product Shaping Decision Tree

Use this tree before technical stack selection. The goal is to classify the product from user intent and generate a stable `project-definition.json`.

## INPUT

- Freeform product description
- Personas
- Core workflows
- Stated platforms
- Sensitive-data signals
- Integrations

## DECISIONS

### 1. Product Type

IF the primary goal is a browser-delivered business product with accounts, dashboards, and subscriptions
THEN `product_type = "web-saas"`

ELSE IF the primary goal is an iOS/Android-first consumer or field workflow
THEN `product_type = "mobile-app"`

ELSE IF the primary output is a programmable service consumed by other systems
THEN `product_type = "api-platform"`

ELSE IF the primary users are internal employees or operators
THEN `product_type = "internal-tool"`

ELSE IF the product matches buyers and sellers, providers and clients, or multiple-sided participation
THEN `product_type = "marketplace"`

ELSE `product_type = "other"`

### 2. Platform Set

IF the user explicitly asks for iOS or Android
THEN include `mobile`

IF the user explicitly asks for browser access, dashboards, portals, or admin views
THEN include `web`

IF the product needs third-party integrations, partner access, or machine-to-machine consumption
THEN include `api`

IF the product is described as back office, operations, or staff-only
THEN include `internal`

### 3. Sensitive Data

IF the product stores names, emails, phone numbers, addresses, or customer profiles
THEN include `pii`

IF the product processes payments, invoices, cards, or subscription billing
THEN include `payments`

IF the product stores medical, wellness, or biometric data
THEN include `health`

IF the product stores bank, payroll, accounting, or investment data
THEN include `financial`

IF the product stores business secrets, client records, or internal documentation
THEN include `confidential-business-data`

### 4. Compliance Signals

IF sensitive_data includes `pii`
THEN recommend `gdpr` for confirmation

IF the product is sold into larger businesses, has audit-heavy workflows, or requires evidence trails
THEN recommend `soc2` for confirmation

IF the product is internet-facing
THEN recommend `owasp`

### 5. Governance Intensity

IF team size is solo and risk signals are low
THEN `governance_profile.team_size = "solo"` and `risk_level = "low"`

IF the product stores sensitive data or has customer-facing multi-user workflows
THEN `risk_level = "medium"`

IF the product handles regulated data, money movement, tenant isolation, or enterprise delivery
THEN `risk_level = "high"`

## OUTPUT

Write the inferred fields into `project-definition.json` with:

- `source = "inferred"`
- confidence based on signal strength
- impact based on downstream architectural/governance effect
