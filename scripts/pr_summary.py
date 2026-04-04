#!/usr/bin/env python3
"""
PR Summary Activity Script

This script fetches and summarizes pull request activity for the past 30 days.
It generates a summary including:
- Total PRs opened
- Total PRs merged
- Total PRs closed without merging
- Currently open PRs
- Top contributors
- Average time to merge
- Detailed PR listing

Usage:
    GITHUB_TOKEN=<token> GITHUB_REPOSITORY=<owner/repo> python scripts/pr_summary.py

Optional environment variables:
    DAYS: Number of days to look back (default: 30)
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from github import Github, Auth


class PRSummary:
    def __init__(self):
        """Initialize the PRSummary with environment variables."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repository = os.getenv('GITHUB_REPOSITORY')
        self.days = int(os.getenv('DAYS', '30'))

        if not self.github_token:
            print("Error: GITHUB_TOKEN environment variable is required")
            sys.exit(1)
        if not self.github_repository:
            print("Error: GITHUB_REPOSITORY environment variable is required")
            sys.exit(1)

        auth = Auth.Token(self.github_token)
        self.gh = Github(auth=auth)
        self.repo = self.gh.get_repo(self.github_repository)

    def get_pr_summary(self):
        """Fetch and summarize PR activity for the past N days."""
        since = datetime.now(timezone.utc) - timedelta(days=self.days)

        print(f"\n{'='*60}")
        print(f"PR Summary Activity - Past {self.days} Days")
        print(f"Repository: {self.github_repository}")
        print(f"Period: {since.strftime('%Y-%m-%d')} to {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
        print(f"{'='*60}\n")

        # Fetch PRs created within the past N days.
        # Results are sorted by creation date descending, so we stop early
        # once we encounter a PR created before the lookback window.
        recent_prs = []
        for pr in self.repo.get_pulls(state='all', sort='created', direction='desc'):
            if pr.created_at < since:
                break
            recent_prs.append(pr)

        # Categorize PRs
        merged_prs = [pr for pr in recent_prs if pr.merged]
        closed_prs = [pr for pr in recent_prs if pr.state == 'closed' and not pr.merged]
        open_prs = [pr for pr in recent_prs if pr.state == 'open']

        # Author statistics
        authors = defaultdict(int)
        for pr in recent_prs:
            authors[pr.user.login] += 1

        # Merge time statistics (in hours)
        merge_times = []
        for pr in merged_prs:
            if pr.merged_at:
                delta = pr.merged_at - pr.created_at
                merge_times.append(delta.total_seconds() / 3600)

        avg_merge_hours = sum(merge_times) / len(merge_times) if merge_times else 0

        # ── Overview ──────────────────────────────────────────────
        print("📊 OVERVIEW")
        print(f"  Total PRs Opened:          {len(recent_prs)}")
        print(f"  PRs Merged:                {len(merged_prs)}")
        print(f"  PRs Closed (unmerged):     {len(closed_prs)}")
        print(f"  PRs Still Open:            {len(open_prs)}")
        if merge_times:
            print(f"  Avg Time to Merge:         {avg_merge_hours:.1f} hours")
        else:
            print(f"  Avg Time to Merge:         N/A")

        # ── Top Contributors ──────────────────────────────────────
        print(f"\n👥 TOP CONTRIBUTORS")
        sorted_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)
        if sorted_authors:
            for author, count in sorted_authors[:10]:
                print(f"  @{author}: {count} PR(s)")
        else:
            print("  No contributors found in this period.")

        # ── Merged PRs ────────────────────────────────────────────
        if merged_prs:
            print(f"\n✅ MERGED PRs ({len(merged_prs)})")
            for pr in sorted(merged_prs, key=lambda x: x.merged_at, reverse=True):
                print(f"  #{pr.number} [{pr.user.login}] {pr.title}")
                print(f"         Merged: {pr.merged_at.strftime('%Y-%m-%d')}")

        # ── Open PRs ──────────────────────────────────────────────
        if open_prs:
            print(f"\n🔄 OPEN PRs ({len(open_prs)})")
            for pr in sorted(open_prs, key=lambda x: x.created_at, reverse=True):
                age_days = (datetime.now(timezone.utc) - pr.created_at).days
                print(f"  #{pr.number} [{pr.user.login}] {pr.title}")
                print(f"         Opened: {pr.created_at.strftime('%Y-%m-%d')} ({age_days} days ago)")

        # ── Closed Without Merging ────────────────────────────────
        if closed_prs:
            print(f"\n❌ CLOSED WITHOUT MERGING ({len(closed_prs)})")
            for pr in sorted(closed_prs, key=lambda x: x.closed_at, reverse=True):
                print(f"  #{pr.number} [{pr.user.login}] {pr.title}")
                print(f"         Closed: {pr.closed_at.strftime('%Y-%m-%d')}")

        if not recent_prs:
            print(f"  No pull request activity found in the past {self.days} days.")

        print(f"\n{'='*60}")
        print("Summary complete.")
        print(f"{'='*60}\n")

        return {
            'total': len(recent_prs),
            'merged': len(merged_prs),
            'closed': len(closed_prs),
            'open': len(open_prs),
            'avg_merge_hours': avg_merge_hours,
            'authors': dict(sorted_authors),
        }


if __name__ == '__main__':
    summary = PRSummary()
    summary.get_pr_summary()
