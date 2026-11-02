import subprocess
import os
import re
from typing import List, Dict, Any, Optional, Tuple

class GitAnalyzer:
    """Extracts architectural signals from git commits and diffs."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)

    def _run_git(self, args: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return ""

    def is_git_repo(self) -> bool:
        return os.path.isdir(os.path.join(self.repo_path, ".git")) or bool(self._run_git(["rev-parse", "--is-inside-work-tree"]))

    def get_current_branch(self) -> str:
        return self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "main"

    def get_latest_commits(self, count: int = 5) -> List[Dict[str, str]]:
        """Returns metadata for recent commits."""
        output = self._run_git(["log", f"-n{count}", "--pretty=format:%H|%an|%s|%cI"])
        commits = []
        if not output:
            return commits
        for line in output.split("\n"):
            parts = line.split("|")
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0],
                    "short_hash": parts[0][:7],
                    "author": parts[1],
                    "subject": parts[2],
                    "date": parts[3]
                })
        return commits

    def get_diff(self, target_ref: str = "HEAD~1", base_ref: str = "HEAD") -> str:
        """Gets full diff between two refs or uncommitted changes if none provided."""
        if target_ref == "working":
            # Uncommitted changes
            diff = self._run_git(["diff", "HEAD"])
            if not diff:
                diff = self._run_git(["diff"])
            return diff
        
        # Check if target_ref exists in history
        check = self._run_git(["rev-parse", "--verify", target_ref])
        if not check:
            # Fallback to initial commit diff or full repo snapshot
            return self._run_git(["diff", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "HEAD"])
        
        return self._run_git(["diff", target_ref, base_ref])

    def get_changed_files(self, target_ref: str = "HEAD~1", base_ref: str = "HEAD") -> List[Dict[str, str]]:
        """Returns list of changed files with their status (A=Added, M=Modified, D=Deleted)."""
        args = ["diff", "--name-status"]
        if target_ref == "working":
            args.append("HEAD")
        else:
            args.extend([target_ref, base_ref])

        output = self._run_git(args)
        if not output and target_ref == "working":
            output = self._run_git(["diff", "--name-status"])

        changed = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                status, path = parts[0], parts[1]
                changed.append({"status": status, "path": path})
        return changed

    def extract_dependency_changes(self, diff_text: str) -> List[Dict[str, Any]]:
        """Parses diff to detect added or removed packages across ecosystems."""
        deps = []

        # Python: requirements.txt or pyproject.toml
        py_matches = re.findall(r'^[+-]([a-zA-Z0-9_\-]+)(?:[=<>~]=?[0-9a-zA-Z._\-]+)?', diff_text, re.MULTILINE)
        
        # Node: package.json dependencies
        pkg_matches = re.findall(r'^[+-]\s*"([@a-zA-Z0-9_\-\/]+)":\s*"[^"]+"', diff_text, re.MULTILINE)

        # Detect package additions in diff
        for line in diff_text.splitlines():
            line_str = line.strip()
            # Node package.json
            if (line_str.startswith('+"') or line_str.startswith('-"')) and '": "' in line_str:
                m = re.match(r'^[+-]\s*"([@a-zA-Z0-9_\-\/]+)":\s*"([^"]+)"', line_str)
                if m:
                    action = "added" if line_str.startswith("+") else "removed"
                    deps.append({"name": m.group(1), "version": m.group(2), "action": action, "type": "npm"})

            # Python pyproject.toml dependencies: +"package>=version",
            elif (line_str.startswith('+"') or line_str.startswith('-"')) and not '": "' in line_str:
                m = re.match(r'^[+-]\s*"([a-zA-Z0-9_\-]+)(?:[=<>~]=?[0-9a-zA-Z._\-]+)?",?', line_str)
                if m:
                    action = "added" if line_str.startswith("+") else "removed"
                    deps.append({"name": m.group(1), "action": action, "type": "python"})
            
            # Python requirements.txt
            if (line_str.startswith('+') or line_str.startswith('-')) and not line_str.startswith('+++') and not line_str.startswith('---'):
                if re.match(r'^[+-][a-zA-Z0-9_\-]+(?:[=<>~]=?[0-9a-zA-Z._\-]+)?$', line_str):
                    action = "added" if line_str.startswith("+") else "removed"
                    pkg_clean = re.sub(r'^[+-]', '', line_str)
                    deps.append({"name": pkg_clean, "action": action, "type": "python"})

        return deps

    def extract_structural_changes(self, changed_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Detects new directory namespaces, architectural shifts, and deletions."""
        added_dirs = set()
        new_modules = []
        deleted_modules = []

        for f in changed_files:
            path = f["path"]
            status = f["status"]
            parts = path.split("/")

            if len(parts) > 1:
                # Top level or domain directories
                added_dirs.add(parts[0])

            if status == "A":
                new_modules.append(path)
            elif status == "D":
                deleted_modules.append(path)

        return {
            "root_directories": sorted(list(added_dirs)),
            "new_modules": new_modules[:15],
            "deleted_modules": deleted_modules[:10],
            "total_changes": len(changed_files)
        }
