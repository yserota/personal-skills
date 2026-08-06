---
name: pr-cycle-time
description: >-
  Calculate PR cycle time for the TW team by joining Jira StartWork with GitHub
  PR timestamps. Measures two segments per ticket: StartWork → PR opened
  (coding time) and StartWork → PR merged (full cycle time). Filters by manager
  team (Adam Christensen, Danielle Biber, Vita Gilin) using the dci-agent
  config files. Supports one or more GitHub repos; results are aggregated across
  all repos. Builds a canvas with summary stats, per-repo breakdown, and a
  per-ticket table with a Repo column.
  Use when the user asks about PR cycle time, coding time, time to merge,
  how long PRs took, or writer throughput metrics for a team.
disable-model-invocation: true
---

# PR Cycle Time

Joins two data sources to measure how long each ticket took to reach a merged PR.

| Segment | Formula | Meaning |
|---------|---------|---------|
| Cycle to open PR | `PR created_at − Jira StartWork` | Coding / drafting time |
| Cycle to merge PR | `PR merged_at − Jira StartWork` | Full active cycle |

---

## Config files (dci-agent repo root)

| File | Purpose |
|------|---------|
| `config/writer_manager_map.csv` | `writer_id, writer_name, manager_name, manager_id, pod, team` |
| `config/jira_username_map.csv` | `jira_username, writer_name` (one writer may have multiple rows / aliases) |

Repo root: `C:\Users\yserota\Documents\Cursor-AI\dci-agent`

---

## Step 1 — Gather inputs

Ask before fetching anything. Echo the confirmed scope back to the user.

| Input | Example |
|-------|---------|
| Period start | `2026-06-01` |
| Period end | `2026-07-31` |
| Team | `Adam Christensen` / `Danielle Biber` / `Vita Gilin` / `All` |
| GitHub repos | One or more `owner/repo` values, comma-separated (e.g. `tdocs/docs, tdocs/PAS, tdocs/EPM, tdocs/conjur-ent`) |

> Confirmed: **2026-06-01 to 2026-07-31 · Danielle Biber's team · tdocs/docs, tdocs/PAS**

If the user does not specify repos, default to `tdocs/docs`.

---

## Step 2 — Resolve writer → Jira usernames

Read both config files to build the team filter.

1. From `writer_manager_map.csv`, collect all `writer_name` values where `manager_name` matches the selected team (skip if "All").
2. From `jira_username_map.csv`, collect every `jira_username` row where `writer_name` is in that list. One writer may have multiple aliases — collect all of them.

**Adam Christensen's writers:** Matt Thies, Steve Goodman, Sabrina Jess, Sari Lorber, Gillian Candiloro, Megha Magaji  
**Danielle Biber's writers:** Rick Fox, Orna Kenet, Judy Wexler, Shuli Finkelstein, Kate Reuveny, Elisha Khera, Mark Lawrence  
**Vita Gilin's writers:** Rivka Teller, Yonit Bisk, Mike Ford, Ben Skelker, Adam Vinacoor

---

## Step 3 — Fetch Jira tickets

```
Tool: jira_search (user-policy-broker)
fields: key, summary, assignee, customfield_12258, customfield_16126
limit: 50  (paginate with start_at until no more results)
```

**JQL — with team filter:**
```
project = DOC
AND "StartWork" >= "START_DATE"
AND "StartWork" <= "END_DATE"
AND assignee IN (jira_username1, jira_username2, ...)
ORDER BY "StartWork" ASC
```

**JQL — All teams:**
```
project = DOC
AND "StartWork" >= "START_DATE"
AND "StartWork" <= "END_DATE"
ORDER BY "StartWork" ASC
```

For each issue collect:
- `key` → Jira ID
- `fields.summary` → Description
- `fields.assignee.name` → Jira username (look up display name via `jira_username_map.csv`)
- `fields.customfield_12258` → StartWork (date string, treat as start of day if time absent)
- `fields.customfield_16126` → Assigned Technical Writer (optional fallback for display name)

---

## Step 4 — Fetch GitHub PRs

Repeat for **each repo** in the confirmed list.

```
Tool: search_pull_requests (user-policy-broker)
query: "repo:OWNER/REPO is:pr is:merged merged:START_DATE..END_DATE"
perPage: 50  (paginate with page= until no more results; keep pages ≤ 50 to stay under the 200 KB output limit)
```

From each PR collect: `number`, `title`, `created_at`, `merged_at` (from `pull_request.merged_at`), `user.login`.

Tag every PR with the repo it came from (e.g. `"tdocs/docs"`).

Build a combined lookup dict keyed by extracted Jira key:
- Extract the first `DOC-\d+` match from the PR **title** (case-insensitive)
- e.g. title `"DOC-1234 Fix auth"` → key `DOC-1234`
- If the same DOC key appears in multiple repos, keep all matches — report each separately
- Store: `{ "DOC-1234": [{ pr_number, repo, title, created_at, merged_at }] }`

If a title contains no `DOC-\d+` pattern, skip that PR (it has no Jira ticket link).

> **Output limit note:** The `search_pull_requests` result is large JSON. Use `perPage: 50` and save each page to a temp file via the extract_prs Python script (`agent-tools/extract_prs_julaug.py`) if the output exceeds the inline limit. Accumulate all pages before proceeding.

---

## Step 5 — Match and compute cycle times

For each Jira ticket:
1. Look up its key in the combined PR dict.
2. If found (one or more repo matches), use the **first** match (by merged_at ascending). Record the `repo` field.
3. Compute (round to 1 decimal place):
   - `coding_days  = PR created_at − Jira StartWork`
   - `total_days   = PR merged_at  − Jira StartWork`
   - `review_days  = PR merged_at  − PR created_at`
4. If not found, record `pr = "—"` and all cycle times as `"no PR"`.
5. If `coding_days` is negative, flag as `"anomaly"` (PR opened before StartWork recorded) and exclude from averages/medians; still show in table.

Map the Jira `assignee.name` to a display name using `jira_username_map.csv`. If no match, use the raw Jira username.

---

## Step 6 — Build canvas

Read the canvas skill before building: `C:\Users\yserota\.cursor\skills-cursor\canvas\SKILL.md`

**Filename:** `pr-cycle-time-{team-slug}-{period}.canvas.tsx`  
(e.g. `pr-cycle-time-adam-danielle-jul19-aug1-2026.canvas.tsx`)

**Path:** `C:\Users\yserota\.cursor\projects\c-Users-yserota-personal-skills\canvases\`

### Canvas sections

**Header**  
H1 "PR Cycle Time", Pills for team name, period, and each repo.

**Summary stats strip**  
`Grid` of 6 `Stat` components (exclude unmatched and anomaly tickets from all averages):

| Stat | Value |
|------|-------|
| Tickets completed | N matched |
| Jira tickets in scope | N total |
| Avg total cycle | X.X days |
| Median total cycle | X.X days |
| Avg review time | X.X days |
| No PR found | N |

**Sprint/period context callout**  
If the period is ≤ 3 weeks, add a `Callout tone="info"` noting that the window is short and most in-progress tickets will appear in the next run.

**Charts row**  
Two `BarChart` components side by side:
- Total cycle time distribution (bucketed: 0–1 d, 1–3 d, 3–5 d, 5–7 d, 7–14 d, 14+ d)
- Avg total cycle by writer (first-name labels)

**Per-repo summary** (when more than one repo was queried)  
`Table` with columns: Repo · PRs with DOC key · Matched to Jira · Avg total (days)

**Per-writer summary**  
`Table` — Writer · PRs merged · Avg coding (days) · Avg review (days) · Avg total (days)  
`rowTone`: same thresholds as ticket table.

**PR table**  
`Table` — columns:

| Jira ID | Repo | Description | Writer | StartWork | Coding (days) | Review (days) | Total (days) |
|---------|------|-------------|--------|-----------|---------------|---------------|--------------|

- Sort by `total_days` ascending (fastest first)
- `rowTone`: `success` if total ≤ median, `warning` if {'>'}1.5× median, `danger` if {'>'}2× median
- Anomaly tickets: `rowTone: "warning"`, show `"anomaly"` in Coding column
- `striped`, `stickyHeader`
- **Final row (averages):** "Averages" in Jira ID cell, blanks elsewhere, computed avgs in metric columns
- Caption: `"Source: Jira StartWork (customfield_12258) · GitHub merged_at · repos: {repo list} · {period}"`

**Collapsible — in-progress tickets**  
Count of tickets with no matched PR; brief note that they will appear in the next run.

---

## Failure rules

| Failure | Action |
|---------|--------|
| No Jira tickets found | Stop; report period and team — no StartWork data |
| MCP unavailable | Stop; tell user to enable policy-broker |
| All PRs unmatched | Warn; check that the branch naming convention is `DOC-\d+` |
| `cycle_to_open_days` negative | Flag as anomaly; exclude from stats; show in table with `"anomaly"` label |
| Jira username not in map | Use raw Jira username as display name; note count in summary |
