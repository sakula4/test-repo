# Copilot Agent Instructions: PR Activity Agent (Issue Comment + Label Applied Time)

## Mission
Implement an automated “PR Activity Agent” for this repository that helps a project manager track pull requests waiting for review and reviewer activity over time.

The agent must add automation that:
1) Runs every 2 hours and publishes a “PRs waiting for review” dashboard.
2) Runs daily and publishes a “reviewer activity last 30 days” summary.

The dashboard must be published as an **upserted comment** on a designated GitHub **Issue** (a single tracking issue).

Waiting time must be computed from the time the label **`ready for review`** was **applied** (not PR created time).

---

## Functional Requirements

### A) 2-hour PR Review Queue Dashboard
**Schedule:** Every 2 hours.

**Scope of PRs:** Open PRs labeled exactly `ready for review` (configurable via env `READY_LABEL`, default: `ready for review`).

**Waiting time source (required):**
- Compute “time waiting for review” as `now - labelAppliedAt` where `labelAppliedAt` is the timestamp when the `ready for review` label was last applied to the PR.
- Use GitHub **GraphQL** to retrieve label timeline events or timeline items with timestamps, because REST does not provide label-applied timestamps reliably.

**Output:** A Markdown report with **two sections**:
1. **Waiting for review**: PRs where there is no active `CHANGES_REQUESTED` state (based on latest review per reviewer).
2. **Changes requested**: PRs where at least one reviewer’s latest review state is `CHANGES_REQUESTED`.

**For each PR**, show a table with columns:
- PR (link + number)
- Description (PR title)
- Time elapsed waiting for review (based on label applied time)
- Reviewers assigned (requested reviewers + requested teams)
- Reviews completed (show `X/Y approvals`, where `Y` defaults to **2** via `REQUIRED_APPROVALS`; also show changes requested count if present)

**Review status rules:**
- “Latest review state per reviewer” matches GitHub UI behavior: for each reviewer, consider only their most recent review state on that PR.
- Approvals count = number of reviewers whose latest state is `APPROVED`.
- Changes requested count = number of reviewers whose latest state is `CHANGES_REQUESTED`.

**Publishing mechanism (required):**
- Upsert (create or update) a single **issue comment** on a tracking issue configured via:
  - `PR_DASHBOARD_ISSUE_NUMBER`
- Use a hidden marker in the comment body to locate and update the same comment every run:
  - `<!-- pr-activity-agent:2h -->`

---

### B) Daily Reviewer Activity Summary (last 30 days)
**Schedule:** Daily.

**Window:** Last 30 days, based on review events and requested-reviewer info on PRs updated in that window.

**Output:** A Markdown report including:

1) **Who is actively reviewing** (table sorted by total reviews left)
   - Reviewer
   - Total PRs reviewed
   - Approvals
   - Changes requested
   - Commented (optional)

2) **Who is being requested but not reviewing**
   - Reviewer requested
   - PRs requested (no review left)

**Publishing mechanism (required):**
- Upsert a single **issue comment** on the same tracking issue as above.
- Use a distinct marker:
  - `<!-- pr-activity-agent:daily -->`

---

## Technical Requirements

### GitHub Actions Workflow
- Add `.github/workflows/pr-activity-agent.yml` with:
  - schedule cron every 2 hours
  - schedule cron daily
  - `workflow_dispatch` for manual runs
- Minimum permissions:
  - `pull-requests: read`
  - `issues: write`
  - `contents: read`
- Use `GITHUB_TOKEN` for auth.

### Script Requirements
- Add a script (Node.js recommended): `scripts/pr-activity-agent.js`
- Use `@actions/github` (Octokit).
- Use REST for PR listing + reviews:
  - `pulls.list` (open PRs)
  - `pulls.get` (requested reviewers/teams)
  - `pulls.listReviews` (review states)
- Use GraphQL for label-applied timestamp:
  - Query PR timeline items and find the most recent “label added” event for `READY_LABEL`.
  - Use the event timestamp as `labelAppliedAt`.
  - If the label was removed and re-added, the waiting time must reflect the most recent add.

**GraphQL guidance (required approach):**
- Query `repository { pullRequest(number: N) { timelineItems(...) { nodes { ... on LabeledEvent { createdAt label { name } } ... }}}}`
- Use `timelineItems` filtering by item types if possible to reduce payload.
- Paginate if needed, but optimize:
  - Only request labeled events (and only enough pages until the most recent match is found).
  - Cache results per PR during a single run.
- If label-applied timestamp cannot be determined (unexpected), fall back to PR `createdAt` but:
  - visibly mark it in output (e.g., append `*` to waiting time and add a footnote “*fallback: PR created time”).

### Performance / Rate Limit Constraints
- Minimize per-PR GraphQL calls if possible:
  - Preferred: one GraphQL query that fetches label events for multiple PRs is not supported directly; so do per-PR GraphQL but keep timelineItems small.
- Implement `per_page` pagination for REST list endpoints.
- Keep logs concise; do not print tokens or sensitive data.

---

## Configuration
Provide configuration via environment variables (document in README):
- `PR_DASHBOARD_ISSUE_NUMBER` (required to publish)
- `READY_LABEL` (default `ready for review`)
- `REQUIRED_APPROVALS` (default `2`)

---

## Deliverables (files to add/update)
1) `.github/workflows/pr-activity-agent.yml`
2) `scripts/pr-activity-agent.js`
3) `docs/pr-activity-agent.md` (or `README.md` section) explaining:
   - create the dashboard issue
   - set `PR_DASHBOARD_ISSUE_NUMBER`
   - required label (`ready for review`)
   - how waiting time is calculated (label applied time)
   - how to run manually

---

## Acceptance Criteria
- A PR labeled `ready for review` appears in the next 2-hour dashboard run.
- “Time waiting” reflects the **label applied time** (not created time).
- PRs with changes requested appear in a separate section.
- Approvals are displayed as `X/2` (or configured).
- Daily summary shows reviewer activity for last 30 days and highlights requested reviewers who did not review.
- The agent updates the same issue comments every run (no spam).

---

## Out of Scope (unless explicitly requested)
- Slack/email notifications
- Auto-labeling PRs
- Expanding team reviewer membership into individual users (requires extra permissions)
