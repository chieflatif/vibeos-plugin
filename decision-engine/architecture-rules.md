# Architecture Rules Decision Tree

## PURPOSE
Select and configure architecture enforcement rules based on the project's framework.

## INPUTS
- `stack.language`
- `stack.framework`
- `stack.source_dirs`

---

## RULE TYPES

The `enforce-architecture.sh` script supports 4 rule types:

```
forbidden_imports    — Module A cannot import from Module B
forbidden_patterns   — Pattern X must not appear in Module A
require_parameter    — Function calls in Module A must include parameter P
io_purity           — Module A cannot perform I/O operations
```

Each rule is defined in `architecture-rules.json`:

```json
{
  "rules": [
    {
      "name": "descriptive rule name",
      "type": "forbidden_imports|forbidden_patterns|require_parameter|io_purity",
      "source_module": "path/to/module/",
      "target_module": "path/to/forbidden/module/",   // for forbidden_imports
      "pattern": "regex pattern",                      // for forbidden_patterns
      "parameter": "param_name",                       // for require_parameter
      "io_patterns": ["open(", "requests.", ...],      // for io_purity
      "severity": "error|warning",
      "message": "Human-readable explanation"
    }
  ]
}
```

---

## UNIVERSAL RULES (all projects)

```json
[
  {
    "name": "no-raw-sql",
    "type": "forbidden_patterns",
    "source_module": "{source_dirs}",
    "pattern": "(cursor\\.execute|connection\\.execute)\\s*\\(\\s*f['\"]|(\\.execute\\s*\\(.*%s)",
    "severity": "error",
    "message": "Use parameterized queries, not string formatting for SQL"
  }
]
```

---

## FRAMEWORK-SPECIFIC RULES

### Python / FastAPI
```json
IF framework == "fastapi":
  RULES:
  [
    {
      "name": "router-isolation",
      "type": "forbidden_imports",
      "source_module": "routers/",
      "target_module": "routers/",
      "severity": "error",
      "message": "Routers cannot import from other routers — use shared services"
    },
    {
      "name": "api-purity",
      "type": "forbidden_patterns",
      "source_module": "routers/",
      "pattern": "(open\\(|subprocess\\.|os\\.system)",
      "severity": "error",
      "message": "Router endpoints must not perform direct I/O — delegate to services"
    },
    {
      "name": "dependency-injection",
      "type": "require_parameter",
      "source_module": "services/",
      "parameter": "db",
      "severity": "warning",
      "message": "Service functions should accept db session via dependency injection"
    },
    {
      "name": "no-raw-sql",
      "type": "forbidden_patterns",
      "source_module": "{source_dirs}",
      "pattern": "(cursor\\.execute|connection\\.execute)\\s*\\(\\s*f['\"]",
      "severity": "error",
      "message": "Use SQLAlchemy ORM or parameterized queries"
    }
  ]
```

### Python / Django
```json
IF framework == "django":
  RULES:
  [
    {
      "name": "app-isolation",
      "type": "forbidden_imports",
      "description": "Django apps should not import models from other apps directly",
      "severity": "warning",
      "message": "Use signals, services, or API calls between Django apps"
    },
    {
      "name": "orm-enforcement",
      "type": "forbidden_patterns",
      "source_module": "{source_dirs}",
      "pattern": "(cursor\\.execute|raw\\(|RawSQL)",
      "severity": "error",
      "message": "Use Django ORM — avoid raw SQL"
    },
    {
      "name": "view-separation",
      "type": "forbidden_patterns",
      "source_module": "*/views.py",
      "pattern": "(objects\\.create|objects\\.filter|objects\\.get|save\\(\\))",
      "severity": "warning",
      "message": "Views should delegate data operations to services or managers"
    },
    {
      "name": "no-raw-sql",
      "type": "forbidden_patterns",
      "source_module": "{source_dirs}",
      "pattern": "cursor\\.execute.*%",
      "severity": "error",
      "message": "Use parameterized queries with Django ORM"
    }
  ]
```

### Python / Flask
```json
IF framework == "flask":
  RULES:
  [
    {
      "name": "blueprint-isolation",
      "type": "forbidden_imports",
      "description": "Blueprints should not import from other blueprints",
      "severity": "error",
      "message": "Use shared services between blueprints"
    },
    {
      "name": "factory-pattern",
      "type": "forbidden_patterns",
      "source_module": "{source_dirs}",
      "pattern": "^app\\s*=\\s*Flask\\(",
      "severity": "warning",
      "message": "Use application factory pattern (create_app function)"
    },
    {
      "name": "no-raw-sql",
      "type": "forbidden_patterns",
      "source_module": "{source_dirs}",
      "pattern": "db\\.engine\\.execute|text\\(.*%",
      "severity": "error",
      "message": "Use SQLAlchemy ORM with parameterized queries"
    }
  ]
```

### TypeScript/JavaScript / Express
```json
IF framework == "express":
  RULES:
  [
    {
      "name": "middleware-isolation",
      "type": "forbidden_imports",
      "source_module": "middleware/",
      "target_module": "routes/",
      "severity": "error",
      "message": "Middleware cannot import route handlers"
    },
    {
      "name": "controller-separation",
      "type": "forbidden_patterns",
      "source_module": "routes/",
      "pattern": "(mongoose\\.|prisma\\.|knex\\.|db\\.)",
      "severity": "warning",
      "message": "Route handlers should delegate data access to controllers/services"
    },
    {
      "name": "async-patterns",
      "type": "forbidden_patterns",
      "source_module": "routes/",
      "pattern": "\\.then\\(",
      "severity": "warning",
      "message": "Use async/await instead of .then() chains in route handlers"
    }
  ]
```

### TypeScript / NestJS
```json
IF framework == "nestjs":
  RULES:
  [
    {
      "name": "module-isolation",
      "type": "forbidden_imports",
      "description": "NestJS modules should only import through module system, not direct file imports",
      "severity": "error",
      "message": "Use NestJS module imports, not direct cross-module file imports"
    },
    {
      "name": "service-purity",
      "type": "forbidden_patterns",
      "source_module": "*.controller.ts",
      "pattern": "(Repository|getRepository|createQueryBuilder)",
      "severity": "error",
      "message": "Controllers should not access repositories directly — use services"
    }
  ]
```

### TypeScript/JavaScript / Next.js
```json
IF framework == "nextjs":
  RULES:
  [
    {
      "name": "server-client-boundary",
      "type": "forbidden_patterns",
      "source_module": "app/",
      "pattern": "('use client'[\\s\\S]*import.*from.*\\/api\\/)",
      "severity": "warning",
      "message": "Client components should not import server API routes directly"
    }
  ]
```

### No Framework / Custom
```json
IF framework == "none":
  RULES:
  [
    {
      "name": "no-raw-sql",
      "type": "forbidden_patterns",
      "source_module": "{source_dirs}",
      "pattern": "(cursor\\.execute|connection\\.execute|db\\.execute|query\\()\\s*\\(\\s*[f'\"]|(\\.execute\\s*\\(.*%s)",
      "severity": "error",
      "message": "Use parameterized queries"
    }
  ]

  PROMPT USER:
    "Your project doesn't use a standard framework. Would you like to define custom module boundaries?"
    IF yes:
      ASK: "What are your main modules/directories and which should NOT import from each other?"
      GENERATE: forbidden_imports rules based on user answers
    IF no:
      USE: only no-raw-sql rule
```

---

## EXISTING PROJECT ADAPTATION (Phase 6)

When ingesting an existing project, architecture rules must be NON-PUNITIVE:

```
1. Scan existing import graph
2. FOR EACH proposed rule:
   COUNT violations in existing codebase
   IF violations > 5:
     WARN: "This rule has {count} existing violations. Options:"
     a) ADAPT rule to exclude existing patterns (add exceptions)
     b) KEEP rule and document violations as baselines
     c) REMOVE rule for now
   IF violations == 0:
     ENABLE rule as-is (project already follows this pattern)
   IF violations 1-5:
     ENABLE rule, add violations as baselines
```

---

## OUTPUT

```json
{
  "architecture_rules": [
    {
      "name": "string",
      "type": "forbidden_imports|forbidden_patterns|require_parameter|io_purity",
      "config": { ... },
      "severity": "error|warning"
    }
  ],
  "rules_file_path": "scripts/architecture-rules.json",
  "adapted_rules": ["<rules modified for existing codebase>"],
  "custom_rules": ["<rules added by user>"]
}
```
