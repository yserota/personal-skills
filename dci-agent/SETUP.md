# DCI Agent — Setup Guide for New Users

This guide is for a Technical Writer who wants to run the DCI pipeline using the three Cursor AI skills:

- **dci-fetch-jira** — pull Jira tickets automatically via MCP
- **dci-run-dashboard** — score writers and produce dashboard tab CSVs
- **dci-score-and-publish** — build the interactive SP-weighted canvas in Cursor

You do not need to be a developer. Follow the steps below once, then the agent does the work.

---

## Step 1 — Install prerequisites

You need two tools installed on your Windows machine.

### Cursor IDE

Download and install Cursor from [cursor.com](https://cursor.com).

Cursor is the AI-powered editor that runs the skills. All pipeline interactions happen through Cursor's chat panel.

### Python 3.10 or later

Download from [python.org](https://www.python.org/downloads/windows/). During installation, check **"Add Python to PATH"**.

Verify the install by opening a PowerShell terminal and running:

```powershell
python --version
```

You should see `Python 3.10.x` or higher.

---

## Step 2 — Get the repo

Clone or download the `dci-agent` repository and place it somewhere accessible, for example:

```
C:\Users\<your-username>\Documents\Cursor-AI\dci-agent
```

If you received a zip file, extract it to that location.

Open the `dci-agent` folder as a workspace in Cursor: **File → Open Folder → select the `dci-agent` folder**.

---

## Step 3 — Install the Python package

Open a Terminal in Cursor (**Terminal → New Terminal**) and run:

```powershell
python -m pip install -e .
```

This installs the pipeline package and its dependencies (PyYAML, gspread, google-auth, openpyxl). It only needs to be done once.

---

## Step 4 — Set up the MCP Policy Broker

The **dci-fetch-jira** skill pulls tickets directly from Jira through an MCP server called the Policy Broker. You need this configured in Cursor before the skill will work.

Ask the person who gave you this repo to send you the Policy Broker setup instructions, or follow the `onboard-cursor-skills` skill if it is available in your Cursor workspace.

Once installed, verify the connection is working:

1. Open Cursor Settings → MCP.
2. Confirm `policy-broker` is listed and enabled.
3. Confirm `jira_search` appears as an available tool under that server.

---

## Step 5 — Update the roster config files

The pipeline uses two CSV files to map Jira usernames to writer names, managers, and pods. These ship with the original team's data and **must be updated to reflect your team**.

### `config/writer_manager_map.csv`

One row per writer. Required columns:

| Column | Description |
|--------|-------------|
| `writer_id` | Lowercase Jira username (e.g. `jane_smith`) |
| `writer_name` | Display name (e.g. `Jane Smith`) |
| `manager_name` | Manager's display name |
| `manager_id` | Manager's Jira username |
| `pod` | Pod label (e.g. `Pod 1`) |
| `team` | Team label (e.g. `Execution`) |

Example:

```csv
writer_id,writer_name,manager_name,manager_id,pod,team
jane_smith,Jane Smith,Alex Manager,alex_manager,Pod 1,Execution
john_doe,John Doe,Sam Lead,sam_lead,Pod 2,Execution
```

### `config/jira_username_map.csv`

Maps Jira usernames to display names when the assignee field returns a username instead of a full name.

| Column | Description |
|--------|-------------|
| `jira_username` | Exact Jira username |
| `writer_name` | Display name matching `writer_manager_map.csv` |

---

## Step 6 — Configure environment (optional)

Copy the example env file and fill in your settings:

```powershell
copy .env.example .env
```

Open `.env` in any text editor. The defaults work for local CSV output with no Google Sheets. If you want to auto-publish scores to Google Sheets, fill in:

- `DCI_GOOGLE_SHEET_ID` — the ID from the spreadsheet URL
- `DCI_GOOGLE_SERVICE_ACCOUNT_JSON_PATH` — path to your GCP service account key JSON

---

## Step 7 — Smoke test

In Cursor's chat panel, type:

> Fetch Jira for DCI

The agent will ask for a start date and end date, then confirm the MCP connection with a 1-ticket test query. If the connection fails, it will tell you to check Policy Broker settings (see Step 4).

---

## Running the full pipeline

Once setup is complete, the typical workflow is:

1. **"Fetch Jira for DCI"** → pulls tickets for the period you specify, saves a CSV
2. **"Run DCI dashboard"** → scores writers, builds the dashboard tab CSVs in `out/dashboard/`
3. **"Build the DCI canvas"** → opens an interactive SP-weighted dashboard in Cursor

Each skill walks you through its steps in the chat.

---

## Updating the roster mid-cycle

If a writer joins or changes managers:

1. Add or edit their row in `config/writer_manager_map.csv`.
2. Add or edit their Jira username in `config/jira_username_map.csv`.
3. Re-run: **"Run DCI dashboard"** (no need to re-fetch Jira unless you want fresh data).

---

## Getting help

- `README.md` — technical reference for all scripts and the input CSV contract.
- `.cursor/skills/dci-run-dashboard/reference.md` — detailed field and metric reference.
- Ask the person who shared this repo for anything else.
