import os
import re
import json
import urllib.request
from typing import List, Dict, Any, Optional

class RuleSynthesizer:
    """
    Synthesizes actionable architectural rules and guidelines from git changes.
    Operates in two modes:
    1. Heuristic Mode (Fast, zero API key, runs offline & in lightweight CI)
    2. AI Mode (Deep context distillation via Gemini or OpenAI API when configured)
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "auto"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if provider == "auto":
            if os.environ.get("GEMINI_API_KEY"):
                self.provider = "gemini"
            elif os.environ.get("OPENAI_API_KEY"):
                self.provider = "openai"
            else:
                self.provider = "heuristic"
        else:
            self.provider = provider

    def synthesize(self, commit_info: Dict[str, Any], changed_files: List[Dict[str, str]], diff_text: str) -> Dict[str, Any]:
        """Synthesizes structured architectural directives from git signals."""
        if self.provider in ["gemini", "openai"] and self.api_key:
            try:
                ai_result = self._synthesize_with_llm(commit_info, changed_files, diff_text)
                if ai_result:
                    return ai_result
            except Exception as e:
                # Silently fallback to heuristic engine if LLM fails or is rate-limited
                pass

        return self._synthesize_with_heuristics(commit_info, changed_files, diff_text)

    def _synthesize_with_heuristics(self, commit_info: Dict[str, Any], changed_files: List[Dict[str, str]], diff_text: str) -> Dict[str, Any]:
        """Local deterministic analyzer that extracts clear architectural facts."""
        rules = []
        dep_updates = []
        conventions = []
        deprecations = []

        commit_msg = commit_info.get("subject", "")

        # 1. Analyze Conventional Commits (feat, refactor, fix, deprecate)
        if commit_msg.startswith("feat"):
            feature_desc = re.sub(r'^feat(\([^)]+\))?:\s*', '', commit_msg)
            rules.append(f"Feature Addition: {feature_desc}")
        elif commit_msg.startswith("refactor"):
            refactor_desc = re.sub(r'^refactor(\([^)]+\))?:\s*', '', commit_msg)
            rules.append(f"Architectural Refactoring: {refactor_desc}")
        elif commit_msg.startswith("deprecate"):
            dep_desc = re.sub(r'^deprecate(\([^)]+\))?:\s*', '', commit_msg)
            deprecations.append(f"Deprecated: {dep_desc}")

        # 2. Pattern & Technology Detection from File Paths & Diffs
        file_paths = [f["path"] for f in changed_files]
        diff_lower = diff_text.lower()

        # Architecture & Framework Detection
        if any("fastapi" in p or "app/main.py" in p for p in file_paths) or "fastapi" in diff_lower:
            conventions.append("Backend Framework: FastAPI with async route definitions")
        if any("pydantic" in p for p in file_paths) or "pydantic" in diff_lower or "basemodel" in diff_lower:
            conventions.append("Data Validation: Use Pydantic models for request/response payloads")
        if any("uv.lock" in p or "pyproject.toml" in p for p in file_paths) or "tool.uv" in diff_lower:
            conventions.append("Packaging & Tooling: uv package manager with standard pyproject.toml")
        if any("sqlalchemy" in diff_lower or "alembic" in p for p in file_paths):
            conventions.append("Database / ORM: SQLAlchemy models with Alembic database migrations")
        if any(p.endswith(".tsx") or p.endswith(".jsx") for p in file_paths):
            if any("tailwind" in p for p in file_paths) or "tailwind" in diff_lower or "classname=" in diff_lower:
                conventions.append("Styling: Tailwind CSS utility classes")
            if any("zustand" in diff_lower for p in file_paths) or "zustand" in diff_lower:
                conventions.append("State Management: Zustand reactive client stores")

        # Security & Auth patterns
        if any("auth" in p.lower() or "jwt" in p.lower() or "token" in p.lower() for p in file_paths):
            if "bearer" in diff_lower or "jwt" in diff_lower:
                conventions.append("Authentication: JWT Bearer tokens via Authorization headers")
            rules.append("Security: Authentication logic updated. Verify token validation in protected endpoints.")

        # Testing conventions
        if any("test" in p.lower() or p.startswith("tests/") for p in file_paths):
            if any(p.endswith(".py") for p in file_paths):
                conventions.append("Testing: Pytest test suites with standard fixtures")
            elif any(p.endswith(".ts") or p.endswith(".js") for p in file_paths):
                conventions.append("Testing: Vitest / Jest test specifications")

        # Structure & Namespace conventions
        dirs = set()
        for p in file_paths:
            parts = p.split("/")
            if len(parts) > 1:
                dirs.add(parts[0])

        if dirs:
            dir_list = ", ".join([f"`{d}/`" for d in sorted(list(dirs))[:5]])
            conventions.append(f"Core Module Boundaries: {dir_list}")

        # Deduplicate
        rules = list(dict.fromkeys(rules))
        conventions = list(dict.fromkeys(conventions))
        deprecations = list(dict.fromkeys(deprecations))

        # Fallback if no specific rule generated
        if not rules and commit_msg:
            rules.append(f"Recent Change: {commit_msg}")

        return {
            "summary": commit_msg or "Architectural update",
            "rules": rules,
            "conventions": conventions,
            "deprecations": deprecations,
            "synthesized_by": "heuristic-engine"
        }

    def _synthesize_with_llm(self, commit_info: Dict[str, Any], changed_files: List[Dict[str, str]], diff_text: str) -> Optional[Dict[str, Any]]:
        """Invokes LLM API to condense code diffs into token-dense AI rules."""
        file_summary = "\n".join([f"- {f['status']} {f['path']}" for f in changed_files[:25]])
        truncated_diff = diff_text[:12000] # Safe token limit

        prompt = f"""You are GitContext, a compiler that converts git commit diffs into crisp, token-dense architectural rules for AI coding assistants (Cursor, Copilot, Claude Code).

Commit: {commit_info.get('subject')} (by {commit_info.get('author')})
Files Changed:
{file_summary}

Git Diff:
```
{truncated_diff}
```

Extract the architectural impact of this commit. Return ONLY a valid JSON object with these keys:
{{
  "summary": "One sentence summary of the architectural change",
  "rules": ["1-3 concise rules for AI assistants based on what was added/changed"],
  "conventions": ["Any new coding conventions, naming rules, or libraries established"],
  "deprecations": ["Any functions, endpoints, patterns, or packages deprecated or removed"]
}}
Be ultra-concise. Output raw JSON only."""

        if self.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(raw_text)
                parsed["synthesized_by"] = "gemini-flash"
                return parsed

        return None
