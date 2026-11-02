import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from git_context.git_analyzer import GitAnalyzer
from git_context.rule_synthesizer import RuleSynthesizer
from git_context.memory_store import MemoryStore
from git_context.billboard import BillboardGenerator

def run_cmd(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({cmd}): {res.stderr}")
    return res.stdout.strip()

def run_simulation():
    demo_dir = Path("/tmp/git_context_demo_repo")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    demo_dir.mkdir(parents=True)

    print("================================================================")
    print("🚀 STARTING GITCONTEXT LIVING MEMORY SIMULATION")
    print("================================================================\n")

    # Step 1: Initialize Git Repo
    print("📦 [Step 1] Initializing mock Git repository...")
    run_cmd("git init -b main", cwd=demo_dir)
    run_cmd('git config user.name "Test Dev"', cwd=demo_dir)
    run_cmd('git config user.email "test@example.com"', cwd=demo_dir)

    # Initial Codebase setup
    (demo_dir / "app").mkdir()
    (demo_dir / "app" / "main.py").write_text("""from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get('/items')
def get_items():
    return [{'name': 'Laptop', 'price': 999.0}]
""")
    (demo_dir / "pyproject.toml").write_text("""[project]
name = "demo-service"
version = "0.1.0"
dependencies = [
    "fastapi>=0.110.0",
    "pydantic>=2.6.4",
    "uvicorn>=0.28.0",
]
""")

    run_cmd("git add .", cwd=demo_dir)
    run_cmd('git commit -m "feat: initial fastapi microservice setup"', cwd=demo_dir)

    # Step 2: Run git-context init
    print("🧠 [Step 2] Running 'git-context init' on initial commit...")
    analyzer = GitAnalyzer(str(demo_dir))
    commits = analyzer.get_latest_commits(1)
    changed = analyzer.get_changed_files("HEAD~1")
    diff_text = analyzer.get_diff("HEAD~1")

    synthesizer = RuleSynthesizer()
    res1 = synthesizer.synthesize(commits[0], changed, diff_text)

    store = MemoryStore(str(demo_dir), ".llmrules")
    store.update(
        new_rules=res1.get("rules", []),
        new_conventions=res1.get("conventions", []),
        new_deprecations=res1.get("deprecations", []),
        commit_entry=commits[0]
    )

    print("📄 Generated .llmrules contents after Commit 1:")
    print("----------------------------------------------------------------")
    print(store.file_path)
    with open(store.file_path) as f:
        print(f.read())
    print("----------------------------------------------------------------\n")

    # Step 3: Architectural Change (Auth & JWT Middleware)
    print("⚡ [Step 3] Developer adds JWT Auth Middleware in Commit 2...")
    (demo_dir / "app" / "auth.py").write_text("""import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    if not token or token != 'valid-secret':
        raise HTTPException(status_code=401, detail='Invalid Bearer Token')
    return {'sub': 'user-123'}
""")
    # Add JWT to pyproject.toml
    (demo_dir / "pyproject.toml").write_text("""[project]
name = "demo-service"
version = "0.1.0"
dependencies = [
    "fastapi>=0.110.0",
    "pydantic>=2.6.4",
    "uvicorn>=0.28.0",
    "pyjwt>=2.8.0",
]
""")

    run_cmd("git add .", cwd=demo_dir)
    run_cmd('git commit -m "feat(auth): introduce jwt bearer token security layer"', cwd=demo_dir)

    # Run git-context sync
    print("🔄 Running 'git-context sync' to absorb Commit 2 changes...")
    commits = analyzer.get_latest_commits(1)
    changed = analyzer.get_changed_files("HEAD~1")
    diff_text = analyzer.get_diff("HEAD~1")
    res2 = synthesizer.synthesize(commits[0], changed, diff_text)

    store.update(
        new_rules=res2.get("rules", []),
        new_conventions=res2.get("conventions", []),
        new_deprecations=res2.get("deprecations", []),
        commit_entry=commits[0]
    )

    # Step 4: Refactoring and Deprecation in Commit 3
    print("⚠️ [Step 4] Developer refactors endpoints and deprecates sync routes in Commit 3...")
    (demo_dir / "app" / "main.py").write_text("""from fastapi import FastAPI, Depends
from app.auth import verify_token

app = FastAPI()

# Deprecated synchronous routes replaced by async handlers
@app.get('/items')
async def get_items(user: dict = Depends(verify_token)):
    return [{'name': 'Laptop', 'price': 999.0, 'owner': user['sub']}]
""")
    run_cmd("git add .", cwd=demo_dir)
    run_cmd('git commit -m "refactor: deprecate sync routes in favor of async handlers with auth guard"', cwd=demo_dir)

    commits = analyzer.get_latest_commits(1)
    changed = analyzer.get_changed_files("HEAD~1")
    diff_text = analyzer.get_diff("HEAD~1")
    deps = analyzer.extract_dependency_changes(diff_text)
    res3 = synthesizer.synthesize(commits[0], changed, diff_text)

    store.update(
        new_rules=res3.get("rules", []),
        new_conventions=res3.get("conventions", []),
        new_deprecations=res3.get("deprecations", []),
        commit_entry=commits[0]
    )

    print("📄 Living .llmrules contents after all 3 commits:")
    print("----------------------------------------------------------------")
    with open(store.file_path) as f:
        print(f.read())
    print("----------------------------------------------------------------\n")

    # Step 5: Simulate GitHub PR Billboard Comment
    print("📢 [Step 5] Simulating the Viral Billboard PR Comment for reviewers...")
    billboard = BillboardGenerator()
    pr_comment = billboard.format_pr_comment(
        summary="Refactored API route handlers to async and enforced JWT token validation",
        rules=res3.get("rules", []),
        conventions=res3.get("conventions", []),
        deprecations=res3.get("deprecations", []),
        deps=deps
    )

    print("💬 Markdown that gets posted to the GitHub Pull Request:")
    print("================================================================")
    print(pr_comment)
    print("================================================================\n")
    print("🎉 SIMULATION COMPLETE: All architectural changes automatically tracked!")

if __name__ == "__main__":
    run_simulation()
