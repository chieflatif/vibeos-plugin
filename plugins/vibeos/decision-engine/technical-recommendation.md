# VibeOS Plugin — Technical Recommendation Decision Tree

Use this tree after product shaping. The goal is to recommend a starting stack, not to overfit every project.

## INPUT

- `project-definition.json`
- `docs/product/PRODUCT-ANCHOR.md`
- `docs/ENGINEERING-PRINCIPLES.md`
- product type
- platforms
- integrations
- sensitive-data profile
- user-confirmed constraints

## DECISIONS

### 1. Default Language

IF product_type is `web-saas`, `api-platform`, or `internal-tool`
THEN default language = `typescript`

ELSE IF product_type is `mobile-app`
THEN default language = `typescript`

ELSE IF the user explicitly prefers Python for backend-heavy or AI-heavy workflows
THEN language = `python`

ELSE keep `typescript`

### 2. Framework

IF platforms include `web` and `api`
THEN recommend `nextjs` or `nestjs` depending on whether the app is UI-first or API-first

IF platforms include `web` and product_type is `web-saas`
THEN recommend `nextjs`

IF platforms include `api` and not `web`
THEN recommend `fastapi` for Python or `express` for TypeScript

IF platforms include `mobile`
THEN recommend `react-native` or `expo` for app delivery and pair with an API backend if needed

IF the product is internal, CRUD-heavy, and delivery speed matters most
THEN prefer a boring full-stack web default over microservices

### 3. Database

IF the product has accounts, subscriptions, relational workflows, admin views, or reporting
THEN recommend `postgresql`

IF the product is document-heavy and relationship complexity is low
THEN `mongodb` is acceptable

IF the product is prototype-only or local-only
THEN `sqlite` is acceptable for the first pass

### 4. Deployment Shape

IF the product is a solo or small-team SaaS
THEN default deployment = `monolith-first`

IF the product has one primary app and one primary database
THEN do not recommend microservices by default

IF risk_level is high and platform set includes `api`
THEN recommend explicit service boundaries, audit logging, and stronger environment separation

### 5. Dependency Policy

IF the project is an application
THEN require lockfiles and prefer exact or bounded versions based on package manager policy

IF the stack is TypeScript or JavaScript
THEN generate recommendations for:
- package manager
- lockfile
- runtime version pin
- framework version strategy

IF the stack is Python
THEN generate recommendations for:
- package manager
- interpreter version pin
- lock or resolved dependency source

### 6. External Service Integration Pattern

When the product needs to integrate with external services (APIs, SaaS tools, cloud platforms):

IF the service has a mature, well-documented CLI (`gh`, `aws`, `kubectl`, `stripe`, `heroku`, etc.)
THEN default to CLI integration — do not recommend MCP

WHY: LLMs use CLIs reliably without additional tooling. CLIs are composable (pipe through `jq`, `grep`), human-debuggable (same command runs for both agent and developer), and use existing auth flows. MCP adds a background process, a new auth surface, and removes composability.

IF the service has no CLI equivalent
OR the team owns and operates the MCP server as internal infrastructure
THEN MCP is acceptable — document the reason in `docs/decisions/DEVIATIONS.md`

IF the product builds an AI agent that calls external services
THEN evaluate each integration against the CLI-first rule before proposing MCP

See `plugins/vibeos/reference/cli-vs-mcp.md` for full decision criteria and audit questions.

Store the decision in `project-definition.json` under `integration_pattern`:
- `default: "cli"` (the baseline)
- `mcp_exceptions: []` (list only services with no CLI alternative, each with a documented reason)

### 7. Freshness Requirement

IF a recommendation depends on external APIs, fast-moving framework behavior, version-specific setup, auth, billing, infrastructure, or security controls
THEN do not rely on model memory alone

AND require current evidence from primary sources

AND record the source and verification date in `docs/research/RESEARCH-REGISTRY.md`

## OUTPUT

Store the recommendation in `project-definition.json` with:

- `technical_recommendation.language`
- `technical_recommendation.framework`
- `technical_recommendation.database`
- `technical_recommendation.deployment_shape`
- `technical_recommendation.notes`
- `technical_recommendation.evidence_sources`
- `technical_recommendation.last_verified`

Mark recommendations as:

- `source = "inferred"` unless the user confirms them
- `confidence = "medium"` by default
- `impact = "high"` for language, framework, database, and deployment shape
- `source = "evidence-backed"` when current primary-source research was recorded
