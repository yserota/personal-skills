# DCI Dashboard — Reference

## Jira export JQL (typical quarter)

```jql
project in (DOC, DOCS)
AND (
  "StartWork" >= "2026-01-01" AND "StartWork" <= "2026-03-31"
  OR "FinishWork" >= "2026-01-01" AND "FinishWork" <= "2026-03-31"
  OR created >= "2026-01-01" AND created <= "2026-03-31"
)
```

Export as CSV. Ensure columns include:

- `Custom field (StartWork)`, `Custom field (FinishWork)`, `Created`
- `Custom field (TW-AI Usage)` (may repeat as multi-select columns — pipeline merges them)
- `Assignee`, `Custom field (Assigned Technical Writer)`

## TW-AI Usage values

| Jira value | Treated as |
|------------|------------|
| `Generate first draft`, `Research`, `Grammar check`, etc. | AI-assisted |
| `No usage` | Manual |
| Blank | Untagged (included in overall DCI only) |

## DCI zones (operational)

| Range | Label |
|-------|-------|
| > 1.0 | Backlog building |
| 0.80 – 0.95 | Healthy runway |
| < 0.75 | Backlog drain |

## Current roster (Pod 2 / Danielle Biber)

Rick Fox, Orna Kenet, Judy Wexler, Shuli Finkelstein, Kate Reuveny, Elisha Khera, Mark Lawrence

## Formula version

Defined in `config/dci_formula.yaml` (currently includes AI segmentation in v1.2.0).

## Windows notes

Use `;` instead of `&&` between PowerShell commands. Run from `dci-agent` root so relative config paths resolve.
