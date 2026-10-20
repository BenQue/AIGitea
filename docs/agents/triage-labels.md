# Matt triage label mapping

These names map Matt's canonical category and state roles onto namespaced Gitea labels. Triage labels are orthogonal
to AISoftPlatform `type/*`, `complexity/*` and lifecycle labels.

## Category

| Canonical role | Gitea label |
|---|---|
| `bug` | `triage/bug` |
| `enhancement` | `triage/enhancement` |

## State

| Canonical role | Gitea label |
|---|---|
| `needs-triage` | `triage/needs-triage` |
| `needs-info` | `triage/needs-info` |
| `ready-for-agent` | `triage/ready-for-agent` |
| `ready-for-human` | `triage/ready-for-human` |
| `wontfix` | `triage/wontfix` |

Every triaged Issue carries exactly one category and one state. `triage/ready-for-agent` only means an Agent may take
the next preparation or implementation step; implementation still requires a complete contract and platform
`approved`. `triage/wontfix` closes the Issue without `completed` or `deployed`.

## Platform admission question

Applies only when the tracker is the AISoftPlatform repository itself (ADR 0001 D4). Before triaging a request that
comes from a downstream project, ask: **would it still hold if that project were replaced by any other registered
project?** If yes, triage it normally. If no, return it to the project repository, or first reduce it to a generic
extension point (a manifest field or a project-owned profile) and triage only that extension point. If the answer is
unclear, keep `triage/needs-info` and ask the owner.
