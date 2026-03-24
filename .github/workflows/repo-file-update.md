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

You are an automated assistant responsible for updating the files configuration as listed out in the tasks.

## Repository Context

- Repository: `${{ github.repository }}`
- Triggered by: `${{ github.event_name }}`

## Your Task

1. **Inspect the repository** to understand its current state and identify files that need updating.

2. **Update the weights** check the file loadbalancers/_config/dev.us-east-1.yaml and swap the target_group weights. If its 100 swap to 0 and vice-versa.

4. **Create a pull request** with all the changes:
   - Title should clearly describe what was updated (e.g., "chore: automated maintenance update YYYY-MM-DD")
   - Body should include a summary of what files were changed and why
   - The PR is created automatically via the `create-pull-request` safe output

## Guidelines

- Only modify files that genuinely need updating — do not make superficial changes
- Keep all changes minimal and clearly documented
- If no updates are needed, do not create a pull request (the workflow will warn and exit cleanly)
- Use ISO 8601 date format (YYYY-MM-DD) for any dates you write
