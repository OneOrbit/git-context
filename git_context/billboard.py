import os
import json
import urllib.request
from typing import Dict, Any, List, Optional

class BillboardGenerator:
    """
    Generates the viral PR comment markdown and manages posting to GitHub PRs.
    Every PR review acts as an autonomous distribution billboard to other engineers.
    """

    BILLBOARD_HEADER = "<!-- git-context-status -->"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")

    def format_pr_comment(
        self,
        summary: str,
        rules: List[str],
        conventions: List[str],
        deprecations: List[str],
        deps: List[Dict[str, Any]]
    ) -> str:
        """Formats an eye-catching, informative markdown summary for GitHub PR reviews."""
        lines = [
            self.BILLBOARD_HEADER,
            "## 🧠 GitContext: AI Codebase Memory Synced",
            "",
            f"**PR Architectural Summary:** {summary}",
            ""
        ]

        if deps:
            dep_lines = []
            for d in deps[:5]:
                act = "➕ Added" if d.get("action") == "added" else "➖ Removed"
                dep_lines.append(f"- {act} `{d.get('name')}` ({d.get('type')})")
            lines.append("### 📦 Dependencies")
            lines.extend(dep_lines)
            lines.append("")

        if rules:
            lines.append("### 📐 Rules Updated for AI Coding Assistants")
            lines.extend([f"- {r}" for r in rules])
            lines.append("")

        if conventions:
            lines.append("### 🛠️ Conventions Established")
            lines.extend([f"- {c}" for c in conventions])
            lines.append("")

        if deprecations:
            lines.append("### 🚫 Deprecations Detected")
            lines.extend([f"- ⚠️ {d}" for d in deprecations])
            lines.append("")

        lines.extend([
            "> *Your AI pair programmers (Cursor, Copilot, Claude Code) now have the latest architectural rules for this PR in `.llmrules`.*",
            "",
            "---",
            "<sub>⚡ Maintained by **[GitContext](https://oneorbit.dev)** by [OneOrbit](https://oneorbit.dev) — Living AI context for engineering teams. Free for Open Source • $12/mo for Private Orgs.</sub>"
        ])

        return "\n".join(lines)

    def post_or_update_pr_comment(self, repo_full_name: str, pr_number: int, comment_body: str) -> bool:
        """Posts or updates existing GitContext comment on the PR via GitHub REST API."""
        if not self.token:
            print("[GitContext] No GITHUB_TOKEN found; printing PR comment to stdout.")
            print(comment_body)
            return False

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitContext-Bot (OneOrbit)"
        }

        # 1. Check for existing comment from bot
        comments_url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
        req = urllib.request.Request(comments_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as resp:
                comments = json.loads(resp.read().decode('utf-8'))
                existing_id = None
                for c in comments:
                    if self.BILLBOARD_HEADER in c.get("body", ""):
                        existing_id = c["id"]
                        break

                if existing_id:
                    # Update existing comment
                    patch_url = f"https://api.github.com/repos/{repo_full_name}/issues/comments/{existing_id}"
                    patch_data = json.dumps({"body": comment_body}).encode('utf-8')
                    patch_req = urllib.request.Request(patch_url, data=patch_data, headers=headers, method="PATCH")
                    with urllib.request.urlopen(patch_req) as p_resp:
                        return p_resp.status == 200
                else:
                    # Create new comment
                    post_data = json.dumps({"body": comment_body}).encode('utf-8')
                    post_req = urllib.request.Request(comments_url, data=post_data, headers=headers, method="POST")
                    with urllib.request.urlopen(post_req) as p_resp:
                        return p_resp.status == 201

        except Exception as e:
            print(f"[GitContext] Error posting GitHub comment: {e}")
            return False
