# Ready for Review Notifications Setup

## Overview

This workflow automatically notifies your team via Microsoft Teams whenever there are pull requests labeled as "ready for review". It runs every 2 hours and also triggers on pull request events.

## Setup Instructions

### 1. Create Teams Webhook

1. **In Microsoft Teams:**
   - Go to the channel where you want notifications
   - Click the "..." menu → **Connectors** → **Incoming Webhook**
   - Click **Configure** → **Add**
   - Give it a name: "GitHub PR Notifications"
   - Upload an icon (optional)
   - Click **Create**
   - **Copy the webhook URL** (you'll need this for step 2)

### 2. Configure Repository Secret

1. **In your GitHub repository:**
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `TEAMS_WEBHOOK_URL`
   - Value: Paste the webhook URL from Teams
   - Click **Add secret**

### 3. Configure PR Labels

The workflow looks for pull requests with these labels (case-insensitive):
- `ready for review`
- `ready-for-review`

Make sure to create and use these labels on your pull requests.

## How It Works

### Triggers
- **Every 2 hours** (automatic)
- **Pull request events:** opened, updated, labeled, unlabeled
- **Manual trigger** (workflow_dispatch)

### What It Does
1. Fetches all open pull requests
2. Filters for PRs with "ready for review" labels
3. Builds a formatted table with PR details
4. Sends notification to Teams channel

### Teams Message Format

The notification includes:
- **Header:** Summary with PR count and repository info
- **Table:** Details for each PR including:
  - PR number (linked)
  - Title (truncated if long)
  - Author
  - Created date  
  - Branch name
  - Assigned reviewers
  - Status (Draft/Ready)
- **Action Buttons:**
  - View all ready-for-review PRs
  - Go to repository

## Example Teams Message

```
🔍 Pull Requests Ready for Review
Repository: myorg/myproject
Total PRs Ready: 3

📋 Pull Request Details
| # | Title | Author | Created | Branch | Reviewers | Status |
|---|-------|--------|---------|---------|-----------|--------|
| [#123](link) | Add new authentication system | @johndoe | Nov 19 | feature/auth | @reviewer1, @reviewer2 | ✅ Ready |
| [#124](link) | Fix database connection issue... | @janedoe | Nov 18 | bugfix/db-conn | @reviewer1 | ✅ Ready |
| [#125](link) | Update documentation for API | @bobsmith | Nov 17 | docs/api-update | None | 🔄 Draft |
```

## Troubleshooting

### No Notifications Received
1. Check that `TEAMS_WEBHOOK_URL` secret is set correctly
2. Verify the webhook URL is still valid in Teams
3. Ensure PRs have the correct labels
4. Check workflow run logs in Actions tab

### Webhook Not Working
1. Test the webhook URL manually:
   ```bash
   curl -H "Content-Type: application/json" -d '{"text":"Test message"}' YOUR_WEBHOOK_URL
   ```
2. Regenerate the webhook in Teams if needed

### Missing PRs in Notification
- Verify PR has `ready for review` or `ready-for-review` label
- Check that PR is in "open" state
- Review workflow logs for any filtering issues

## Customization

You can customize the workflow by:
- Changing the schedule (modify the cron expression)
- Adjusting label matching logic
- Modifying the Teams message format
- Adding additional PR filters or data

## Files Created

- `.github/workflows/ready_for_review_notify.yml` - Main workflow
- This setup guide for reference