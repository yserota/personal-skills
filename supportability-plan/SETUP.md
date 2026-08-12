# Supportability Plan — Setup Guide

This guide is for anyone who wants to run the supportability plan workflow using the `supportability-plan` Cursor AI skill. Follow the steps below once, then the agent does the work.

---

## Step 1 — Prerequisites

You need two things before you can use this skill.

### Cursor IDE

Download and install Cursor from [cursor.com](https://cursor.com).

### MCP Policy Broker with Jira and Confluence access

The skill calls Jira (to read ticket status) and Confluence (to publish the plan page) through an MCP server called the Policy Broker.

Ask the person who gave you this repo to send you the Policy Broker setup instructions, or follow the `onboard-cursor-skills` skill if it is available in your Cursor workspace.

Once installed, verify the connection is working:

1. Open Cursor Settings → MCP.
2. Confirm `user-policy-broker` is listed and enabled.
3. Confirm `jira_get_issue` and `confluence_update_page` appear as available tools.

---

## Step 2 — Get the repo

Clone the `personal-skills` repository and open it in Cursor:

```
File → Open Folder → select the personal-skills folder
```

---

## Step 3 — Deploy the canvas

The skill uses a live canvas that Cursor renders beside the chat. The canvas source is version-controlled in this repo; you need to copy it to the folder Cursor watches.

Open a PowerShell terminal in Cursor (**Terminal → New Terminal**).

**First time only** — allow locally-written scripts to run (no admin rights needed):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

Then deploy the canvases:

```powershell
.\deploy-canvases.ps1
```

This copies `canvases/supportability-plan-jul12.canvas.tsx` into your Cursor projects folder. You must open the workspace in Cursor at least once first so Cursor creates that folder.

Re-run `.\deploy-canvases.ps1` any time you update the canvas source (the execution policy step is a one-time setup).

---

## Step 4 — Create the exports folder

The skill writes versioned publish files (markdown + JSON) to a local folder outside the repo. Create it anywhere on your machine:

```
<exports-root>\
  supportability-publish\
```

Example path: `C:\Users\<your-username>\Documents\Supportability-Exports`

You will also need a copy of `project-plan-publish-20260712.json` (the metadata file that tracks the current Confluence version). Get this from a teammate who has already run the workflow, or create a fresh one with the structure below:

```json
{
  "snapshot_date": "YYYY-MM-DD",
  "published_version": 1,
  "previous_version": null,
  "covered": 0,
  "partial": 0,
  "gap": 0,
  "active_program_tickets": 0
}
```

Place this file at `<exports-root>\supportability-publish\project-plan-publish-20260712.json`.

---

## Step 5 — Update the SKILL.md paths

Open `supportability-plan/SKILL.md` and update the **Key artifacts** table to reflect your local exports root:

| Field | Replace with |
|-------|-------------|
| `<exports-root>` | Your actual path, e.g. `C:\Users\jsmith\Documents\Supportability-Exports` |

---

## Step 6 — Smoke test

In Cursor's chat panel, type:

> update supportability plan

The agent will read the canvas and metadata JSON, then ask what changed. If the MCP connection fails, it will tell you to check Policy Broker settings (see Step 1).

---

## Getting help

- `SKILL.md` — full step-by-step workflow reference
- `deploy-canvases.ps1` — canvas deployment script
- Ask the person who shared this repo for anything else.
