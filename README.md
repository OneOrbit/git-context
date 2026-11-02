# 🧠 GitContext

> **Autonomous Living Memory & Rule Compiler for AI Coding Assistants**  
> *Keeps `.llmrules` and `.cursorrules` continuously updated from Git diffs so Cursor, Claude Code, Copilot, and Antigravity never hallucinate outdated conventions.*

[![GitHub Action](https://img.shields.io/badge/GitHub_Action-Marketplace-blue.svg)](https://github.com/marketplace/actions/gitcontext)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 💥 The Problem: "Context Rot"

Every engineer using modern AI coding assistants (Cursor, GitHub Copilot, Claude Code, Windsurf) relies on context files like `.cursorrules`, `.llmrules`, or `CLAUDE.md`.

**The fatal flaw?** Nobody maintains them.
- Within 2 weeks of fast-paced commits, libraries are upgraded, directories are reorganized, and functions are deprecated.
- The AI keeps suggesting deprecated imports, wrong database patterns, and stale architecture conventions because its rules file hasn't been updated since day one.

**GitContext solves this completely autonomously.**

---

## ⚡ How It Works

GitContext hooks into your Git workflow (either locally as a Git hook or automatically in your CI via GitHub Actions):

```
 Git Commit / PR ──▶ GitContext Analyzer ──▶ Rule Synthesizer ──▶ Living .llmrules
 (Code Diffs & AST)  (Detects Deps, APIs &)  (Condenses into    (Ready for Cursor,
                      Directory Shifts)       Token-Dense Rules) Copilot, & Claude)
```

1. **Diff Analysis:** Scans code changes, dependency shifts (`package.json`, `requirements.txt`, `pyproject.toml`), new directory namespaces, and commit messages.
2. **Architectural Distillation:** Extracts concrete conventions (e.g., *"Use async FastAPI handlers"*, *"Authentication uses JWT Bearer tokens in `app/auth.py`"*).
3. **Token-Budget Pruning:** Maintains `.llmrules` under an ultra-dense token budget so it never bloats your AI prompt context window.
4. **Viral PR Review Billboard:** When run in GitHub Actions, it posts a clear summary comment on every pull request, informing reviewers that AI context has been updated.

---

## 🚀 Quick Start (Local CLI)

Managed 100% via [`uv`](https://github.com/astral-sh/uv) — ultra-fast, zero-hassle execution with no manual venv management.

### 1. Run Instantly (No Installation Needed)

You can run GitContext directly with `uvx`:

```bash
uvx git-context init
```

### 2. Or Install as a Global Tool

```bash
uv tool install git-context
```

### 3. Initialize in your Repository

```bash
cd your-project-repo
git-context init
```

This inspects your project structure, frameworks, and dependencies, generating your initial `.llmrules`.

### 4. Automatic Local Sync (Git Hook)

Install the automatic post-commit hook:

```bash
git-context hook install
```

Now, every time you make a `git commit`, GitContext will silently update `.llmrules` in under **50ms**.

---

## 🛠️ Local Development & Testing

This project uses `uv` exclusively for dependency and workspace management:

```bash
# Clone the repository
git clone https://github.com/oneorbit/git-context.git
cd git-context

# Sync dependencies with uv
uv sync

# Run the 3-commit architectural simulation test
uv run python tests/demo_simulation.py

# Run git-context commands
uv run git-context --help
uv run git-context diff
```

---

## 🤖 GitHub Action (Automated Team Sync)

Add GitContext to your repository in 30 seconds by creating `.github/workflows/git-context.yml`:

```yaml
name: "GitContext AI Sync"

on:
  pull_request:
    types: [opened, synchronize]
  push:
    branches: [main]

jobs:
  sync-memory:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - uses: oneorbit/git-context@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          file: ".llmrules"
```

### What Reviewers See on Every Pull Request:

```markdown
<!-- git-context-status -->
## 🧠 GitContext: AI Codebase Memory Synced

**PR Architectural Summary:** Refactored API route handlers to async and enforced JWT token validation

### 📐 Rules Updated for AI Coding Assistants
- Feature Addition: Introduce JWT bearer token security layer
- Security: Authentication logic updated. Verify token validation in protected endpoints.
- Architectural Refactoring: Deprecate sync routes in favor of async handlers with auth guard

### 🛠️ Conventions Established
- Backend Framework: FastAPI with async route definitions
- Authentication: JWT Bearer tokens via Authorization headers
- Core Module Boundaries: `app/`

> *Your AI pair programmers (Cursor, Copilot, Claude Code) now have the latest architectural rules for this PR in `.llmrules`.*

---
<sub>⚡ Maintained by **[GitContext](https://oneorbit.dev)** by [OneOrbit](https://oneorbit.dev) — Living AI context for engineering teams. Free for Open Source • $12/mo for Private Orgs.</sub>
```

---

## 💡 The "No-Sales" Growth Playbook (Why this sells itself)

As an engineer, you never have to send a cold email, run ads, or jump on sales demos:

1. **GitHub Marketplace Organic Ingestion:** Developers searching the GitHub Marketplace for *"AI context"*, *"cursorrules"*, or *"codebase memory"* find GitContext directly.
2. **The PR Review Billboard Loop:** Every time GitContext runs on a team’s pull request, every reviewer and tech lead on that team sees the bot comment. Team adoption spreads organically without you doing any outreach.
3. **Impulse-Buy Pricing ($12/month):** Teams with private repositories upgrade via GitHub Marketplace billing directly onto their existing GitHub invoice. No procurement approvals needed.

---

## 🛠️ CLI Command Reference

| Command | Description |
| :--- | :--- |
| `git-context init` | Scans repo and creates the baseline `.llmrules` |
| `git-context sync` | Detects changes in the latest commit and updates `.llmrules` |
| `git-context diff` | Dry run: prints detected architectural changes to stdout without writing |
| `git-context action` | Runs in CI mode: updates memory and posts the GitHub PR comment |
| `git-context hook install` | Installs the local Git `post-commit` automatic hook |

---

## 📄 License

MIT License. Free for open source and personal use. Maintained by [OneOrbit](https://oneorbit.dev).
