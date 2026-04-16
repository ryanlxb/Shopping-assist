# Architecture Rules

| ID | Rule | Rationale |
|----|------|-----------|
| R1 | All external API calls must go through a unified adapter layer | Isolate platform-specific logic, enable easy addition of new platforms |
| R2 | OCR results must be cached with product ID as key | Avoid redundant image processing, reduce cost |
| R3 | Sensitive credentials (API keys, tokens) must be in env vars, never in code | Security best practice |

## Invariants

- All 34+ tests must pass before committing
- `TemplateResponse` must use Starlette 1.0 signature: `TemplateResponse(request, name, context)`
- SQLAlchemy models must be imported before `Base.metadata.create_all()`
