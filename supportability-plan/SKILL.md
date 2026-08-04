---
name: supportability-plan
description: >-
  Refresh and publish the CyberArk Supportability Documentation Program plan.
  Use when the user says "update supportability plan", "add new tickets to the
  plan", "refresh jira tickets", "re-publish to confluence", or "supportability
  program". Covers: querying Jira for live ticket status, updating the canvas
  and publish markdown, and pushing to Confluence.
---

# Supportability Plan — Refresh & Publish

## Key artifacts

| Artifact | Path |
| --- | --- |
| Canvas | `C:\Users\yserota\.cursor\projects\c-Users-yserota-Documents-GitHub-docs\canvases\supportability-plan-jul12.canvas.tsx` |
| Publish markdown | `C:\Users\yserota\Documents\Supportability-Exports\supportability-publish\` — always use the **highest** `v##` suffix (e.g. `project-plan-publish-20260712-v16.md`) |
| Metadata JSON | `C:\Users\yserota\Documents\Supportability-Exports\supportability-publish\project-plan-publish-20260712.json` |
| Confluence page ID | `700399537` |
| Jira base URL | `https://ca-il-jira.il.cyber-ark.com:8443/browse/` |
| MCP server | `user-policy-broker` |

---

## Step 1 — Read current state

Read the canvas `.tsx` and the metadata JSON to identify:
- All `DOC-` keys in `programTickets[]` (active tickets to refresh)
- Current coverage counts (covered / partial / gap) in `driverRows[]`
- Latest published Confluence version from `published_version` in the JSON

---

## Step 2 — Query Jira for live status

For each active `DOC-` ticket and any new tickets the user mentions, call:

```
Tool: jira_get_issue (user-policy-broker)
Param: issue_key = "DOC-XXXXX"
```

Capture `status`, `summary`, and `assignee` for each. Note any status changes (e.g. Open → Done, Blocked).

---

## Step 3 — Update the canvas

File: `supportability-plan-jul12.canvas.tsx`

- **Changed tickets**: update `status`, `summary`, `kind` fields in `programTickets[]`
- **New Jira tickets (replacing NEW-XX)**: replace the `NEW-XX` entry with the real `DOC-` key; set `kind: "active"`, `status: "Open"`; update the matching `driverRows[]` entry from `coverage: "gap"` to `coverage: "covered"` and set `existingDoc`
- **New tickets with no prior NEW-XX**: add a new row to both `programTickets[]` and `driverRows[]`
- **Coverage pills / stats**: the covered/partial/gap counts are computed dynamically from `driverRows[]` — they update automatically when `coverage` values change
- **Pill counts** (e.g. "15 gaps to file", "35 tickets after filing"): update manually to match the new totals
- **Callout summary text**: update to reflect the new state

The `isRealKey()` helper ensures all `DOC-` keys render as clickable Jira links automatically.

The `CrossLinks` component (already in the canvas) renders `CROSS-XXXX` values as clickable links. It handles:
- Single: `"CROSS-320"` → one link
- Slash-separated shorthand: `"CROSS-1059/1060"` → expands to `CROSS-1059` and `CROSS-1060` links
- Dash: `"-"` → plain text

---

## Step 4 — Generate the new publish markdown

1. Find the current highest version file in `supportability-publish\` (e.g. `v16.md`)
2. Write a new file incrementing by 1 (e.g. `v17.md`)
3. Apply these rules throughout:
   - All `DOC-` keys → `[DOC-XXXXX](https://ca-il-jira.il.cyber-ark.com:8443/browse/DOC-XXXXX)`
   - All `CROSS-XXXX` keys → `[CROSS-XXXX](https://ca-il-jira.il.cyber-ark.com:8443/browse/CROSS-XXXX)`
   - Cells with multiple CROSS refs (e.g. "CROSS-1059, CROSS-1060") → each ref gets its own link: `[CROSS-1059](...), [CROSS-1060](...)`
   - `NEW-XX` keys → plain text (no link, not yet in Jira)
   - Cells with `-` for CROSS → leave as plain `-` (no link)
   - Use only ASCII hyphens (`-`), never em-dashes (`—`) — Confluence garbles Unicode on migration
   - Update the snapshot date line at the top to today's date
4. Update all tables and counts to match the canvas state

---

## Step 5 — Publish to Confluence

```
Tool: confluence_update_page (user-policy-broker)
page_id: "700399537"
title: "Supportability Documentation Program - Project Plan"
content: <full markdown from the new vXX.md file>
content_format: "markdown"
enable_heading_anchors: true
version_comment: "vXX - <date>: <one-line description of what changed>"
```

Note the `version` number returned in the response — needed for Step 6.

---

## Step 6 — Update metadata JSON

In `project-plan-publish-20260712.json`, update:
- `snapshot_date` → today's date (YYYY-MM-DD)
- `previous_version` → the old `published_version` value
- `published_version` → the Confluence version number returned in Step 5
- Update any metric fields (covered, partial, gap, active_program_tickets, etc.) that changed

---

## Adding new tickets checklist

When the user says "we added tickets DOC-XXXXX and DOC-XXXXX":

- [ ] Fetch each from Jira (Step 2)
- [ ] In canvas: replace matching `NEW-XX` in `programTickets[]`; flip `driverRows[]` entry to `covered`
- [ ] In canvas: update pill counts and callout summary
- [ ] Write new markdown version (Step 4)
- [ ] Publish to Confluence (Step 5)
- [ ] Update metadata JSON (Step 6)
