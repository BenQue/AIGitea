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
the next preparation or implementation step; Development Loop still requires a complete contract and platform
`approved`. `triage/wontfix` closes the Issue without `completed` or `deployed`.
