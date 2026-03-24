---
name: Repo File Update
description: Periodically checks out the repository, makes modifications to tracked files, and creates a pull request with the changes.
on:
  schedule:
    - cron: "weekly on monday"
  workflow_dispatch:
permissions:
  contents: read
  pull-requests: read
  issues: read
timeout-minutes: 20
tools:
  github:
    toolsets: [default]
  edit:
safe-outputs:
  create-pull-request:
    title-prefix: "[automated] "
    labels: [automated, file-update]
    draft: false
    if-no-changes: warn
---

# Repo File Update Workflow

You are an automated assistant responsible for keeping repository files up-to-date. Your job is to inspect certain files in the repository, apply necessary updates, and open a pull request with the changes.

## Repository Context

- Repository: `${{ github.repository }}`
- Triggered by: `${{ github.event_name }}`

## Your Task

1. **Inspect the repository** to understand its current state and identify files that need updating.

2. **Update `CHANGELOG.md`** at the root of the repository:
   - If the file does not exist, create it following the standard Keep-a-Changelog format
   - Add a new dated entry at the top noting the automated maintenance run date and any notable observations about the repository
   - If the file already exists, add a new `## [Unreleased]` section at the top (if one is not already present) with today's date as a comment
   - Do not duplicate existing entries — check whether today's date already appears in the file

3. **Update `README.md`** (if it exists and has a "Last Updated" or "Last Reviewed" badge/line):
   - Find any "last reviewed", "last updated", or similar timestamp indicators
   - Update the date to today's date
   - If no such indicator exists, skip this step

4. **Create a pull request** with all the changes:
   - Title should clearly describe what was updated (e.g., "chore: automated maintenance update YYYY-MM-DD")
   - Body should include a summary of what files were changed and why
   - The PR is created automatically via the `create-pull-request` safe output

## Guidelines

- Only modify files that genuinely need updating — do not make superficial changes
- Keep all changes minimal and clearly documented
- If no updates are needed, do not create a pull request (the workflow will warn and exit cleanly)
- Use ISO 8601 date format (YYYY-MM-DD) for any dates you write
