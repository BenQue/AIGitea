# Domain docs

Use a single-context layout by default:

- `CONTEXT.md` at repository root defines the domain glossary and durable business rules.
- `docs/adr/` contains accepted architecture decisions.

Matt skills should read these before triage, spec, tickets, implementation or review. Add a `CONTEXT-MAP.md` and
per-context documents only for a genuinely large multi-package repository whose contexts require separate glossaries.
