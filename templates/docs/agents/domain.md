# Domain docs

Use a single-context layout by default:

- `GLOSSARY.md` at repository root defines domain terminology only.
- Accepted business rules belong in the relevant product/change contract; accepted architecture decisions belong
  in `docs/adr/`. A glossary entry may point to these sources but must not replace them.
- Add `GLOSSARY-MAP.md` and per-context glossaries only when the repository actually has multiple bounded contexts.

Matt skills should read these before triage, spec, tickets, implementation or review.

## Existing CONTEXT documents

Read existing `CONTEXT.md` and `CONTEXT-MAP.md` alongside any glossary. First inventory their terminology, durable
business rules, decisions and inbound references. Move only terminology into the glossary; preserve rules in their
existing authoritative contract or an explicitly approved destination, and retain compatibility pointers for old
links. Never bulk-rename downstream repositories or rewrite historical Change documents.

If legacy and new definitions disagree, stop the migration and identify the exact conflict; do not silently choose
one or merge business rules into a terminology-only file. Until reviewed, the legacy content remains available.
