import os
import sys
import argparse
import json
from git_context.git_analyzer import GitAnalyzer
from git_context.rule_synthesizer import RuleSynthesizer
from git_context.memory_store import MemoryStore, DEFAULT_RULE_FILE
from git_context.billboard import BillboardGenerator

def _resolve_target_file(requested_file: str, format_type: str) -> str:
    if format_type == "ts" and requested_file == DEFAULT_RULE_FILE:
        return "context.d.ts"
    elif format_type == "toon" and requested_file == DEFAULT_RULE_FILE:
        return ".llmrules.toon"
    elif format_type == "yaml" and requested_file == DEFAULT_RULE_FILE:
        return "context.yaml"
    return requested_file

def cmd_init(args):
    repo_path = args.path
    analyzer = GitAnalyzer(repo_path)
    if not analyzer.is_git_repo():
        print(f"❌ Error: '{repo_path}' is not a valid git repository.")
        sys.exit(1)

    target_file = _resolve_target_file(args.file, args.format)
    store = MemoryStore(repo_path, target_file, format_type=args.format)
    print(f"🔍 Analyzing repository structure at {repo_path}...")
    
    # Analyze recent commit or current tree
    commits = analyzer.get_latest_commits(count=1)
    commit = commits[0] if commits else {"subject": "Initial repository context", "short_hash": "HEAD"}
    
    changed = analyzer.get_changed_files(target_ref="HEAD~1") if commits else []
    diff_text = analyzer.get_diff("HEAD~1") if commits else ""

    synthesizer = RuleSynthesizer()
    res = synthesizer.synthesize(commit, changed, diff_text)
    
    store.update(
        new_rules=res.get("rules", []),
        new_conventions=res.get("conventions", []),
        new_deprecations=res.get("deprecations", []),
        commit_entry=commit
    )
    
    benchmark = store.get_token_benchmark()
    current_tokens = benchmark[store.format_type]["tokens"]
    savings = benchmark[store.format_type]["savings_pct"]

    print(f"✅ Initialized AI Codebase Memory in '{target_file}' (Format: {store.format_type.upper()}).")
    print(f"   Conventions: {len(res.get('conventions', []))}")
    print(f"   Rules: {len(res.get('rules', []))}")
    if savings > 0:
        print(f"   ⚡ Token Efficiency: ~{current_tokens} tokens ({savings}% reduction vs standard Markdown)")
    else:
        print(f"   ⚡ Token Footprint: ~{current_tokens} tokens (TOON format saves ~{benchmark['toon']['savings_pct']}%)")
    print("💡 Cursor, Copilot, and Claude Code can now read this file for accurate project context.")

def cmd_sync(args):
    repo_path = args.path
    analyzer = GitAnalyzer(repo_path)
    if not analyzer.is_git_repo():
        print(f"❌ Error: '{repo_path}' is not a valid git repository.")
        sys.exit(1)

    target_ref = args.target_ref
    base_ref = args.base_ref

    commits = analyzer.get_latest_commits(count=1)
    commit = commits[0] if commits else {"subject": "Working changes", "short_hash": "HEAD"}

    changed = analyzer.get_changed_files(target_ref=target_ref, base_ref=base_ref)
    diff_text = analyzer.get_diff(target_ref=target_ref, base_ref=base_ref)

    if not changed and not diff_text:
        print("ℹ️ No code changes detected between target and base ref.")
        return

    deps = analyzer.extract_dependency_changes(diff_text)
    synthesizer = RuleSynthesizer()
    res = synthesizer.synthesize(commit, changed, diff_text)

    target_file = _resolve_target_file(args.file, args.format)
    store = MemoryStore(repo_path, target_file, format_type=args.format)
    store.update(
        new_rules=res.get("rules", []),
        new_conventions=res.get("conventions", []),
        new_deprecations=res.get("deprecations", []),
        commit_entry=commit
    )

    benchmark = store.get_token_benchmark()
    current_tokens = benchmark[store.format_type]["tokens"]
    savings = benchmark[store.format_type]["savings_pct"]

    savings_str = f" • -{savings}% tokens" if savings > 0 else ""
    print(f"✨ Synced architectural changes to '{target_file}' ({store.format_type.upper()} • ~{current_tokens} tokens{savings_str}):")
    for r in res.get("rules", []):
        print(f"   • {r}")
    for c in res.get("conventions", []):
        print(f"   • {c}")
    if res.get("deprecations"):
        for d in res.get("deprecations", []):
            print(f"   ⚠️  {d}")

def cmd_diff(args):
    repo_path = args.path
    analyzer = GitAnalyzer(repo_path)
    commits = analyzer.get_latest_commits(count=1)
    commit = commits[0] if commits else {"subject": "Working changes", "short_hash": "HEAD"}
    changed = analyzer.get_changed_files(target_ref=args.target_ref)
    diff_text = analyzer.get_diff(target_ref=args.target_ref)
    deps = analyzer.extract_dependency_changes(diff_text)

    synthesizer = RuleSynthesizer()
    res = synthesizer.synthesize(commit, changed, diff_text)

    target_file = _resolve_target_file(args.file, args.format)
    store = MemoryStore(repo_path, target_file, format_type=args.format)
    preview_data = {
        "conventions": res.get("conventions", []),
        "rules": res.get("rules", []),
        "deprecations": res.get("deprecations", []),
        "history": [f"[{commit['short_hash']}] {res.get('summary', commit['subject'])}"]
    }
    bench = store.get_token_benchmark(preview_data)

    print(f"🔬 GitContext Architectural Diff Preview:")
    print(f"Summary: {res.get('summary')}")
    print(f"Rules: {json.dumps(res.get('rules', []), indent=2)}")
    print(f"Conventions: {json.dumps(res.get('conventions', []), indent=2)}")
    print(f"Dependencies detected: {len(deps)}")
    print(f"⚡ Token Benchmarks: Markdown={bench['markdown']['tokens']}t | TOON={bench['toon']['tokens']}t (-{bench['toon']['savings_pct']}%) | TypeScript={bench['ts']['tokens']}t (-{bench['ts']['savings_pct']}%) | YAML={bench['yaml']['tokens']}t (-{bench['yaml']['savings_pct']}%)")

def cmd_action(args):
    """Execution mode for GitHub Actions CI."""
    print("🚀 Running GitContext in GitHub Action Mode...")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repo_full_name = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = None

    if event_path and os.path.isfile(event_path):
        try:
            with open(event_path, "r") as f:
                event_data = json.load(f)
                pr_number = event_data.get("pull_request", {}).get("number")
        except Exception as e:
            print(f"Warning: Could not parse GITHUB_EVENT_PATH: {e}")

    analyzer = GitAnalyzer(".")
    commits = analyzer.get_latest_commits(count=1)
    commit = commits[0] if commits else {"subject": "PR Changes", "short_hash": "PR"}

    # Compare against PR base or previous commit
    target_ref = "HEAD~1"
    changed = analyzer.get_changed_files(target_ref=target_ref)
    diff_text = analyzer.get_diff(target_ref=target_ref)
    deps = analyzer.extract_dependency_changes(diff_text)

    synthesizer = RuleSynthesizer()
    res = synthesizer.synthesize(commit, changed, diff_text)

    # Update file
    target_file = _resolve_target_file(args.file, args.format)
    store = MemoryStore(".", target_file, format_type=args.format)
    store.update(
        new_rules=res.get("rules", []),
        new_conventions=res.get("conventions", []),
        new_deprecations=res.get("deprecations", []),
        commit_entry=commit
    )

    benchmark = store.get_token_benchmark()
    token_info = {
        "format": store.format_type,
        "tokens": benchmark[store.format_type]["tokens"],
        "savings_pct": benchmark[store.format_type]["savings_pct"]
    }

    # Generate Billboard Comment
    billboard = BillboardGenerator()
    comment = billboard.format_pr_comment(
        summary=res.get("summary", ""),
        rules=res.get("rules", []),
        conventions=res.get("conventions", []),
        deprecations=res.get("deprecations", []),
        deps=deps,
        file_name=target_file,
        token_info=token_info
    )

    # Post to PR if in pull request
    if repo_full_name and pr_number:
        print(f"Posting PR review comment to {repo_full_name}#{pr_number}...")
        billboard.post_or_update_pr_comment(repo_full_name, pr_number, comment)
    else:
        print("GitHub Step Summary:")
        print(comment)

    # Write to step summary if in GitHub Actions
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a") as sf:
                sf.write("\n" + comment + "\n")
        except Exception:
            pass

def cmd_hook_install(args):
    repo_path = args.path
    hook_dir = os.path.join(repo_path, ".git", "hooks")
    if not os.path.isdir(hook_dir):
        print(f"❌ Error: '.git/hooks' not found at {repo_path}.")
        sys.exit(1)

    hook_file = os.path.join(hook_dir, "post-commit")
    script = """#!/usr/bin/env bash
# GitContext Auto-Sync Hook (supports global binary or uv run)
if command -v git-context >/dev/null 2>&1; then
    git-context sync > /dev/null 2>&1 &
elif command -v uv >/dev/null 2>&1; then
    uv run git-context sync > /dev/null 2>&1 &
fi
"""
    with open(hook_file, "w") as f:
        f.write(script)
    os.chmod(hook_file, 0o755)
    print(f"✅ Installed GitContext hook: {hook_file}")
    print("   Every local git commit will now automatically update your AI context!")

def main():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--file", default=DEFAULT_RULE_FILE, help="Rule file name (default: .llmrules)")
    common_parser.add_argument("--format", choices=["auto", "markdown", "toon", "ts", "yaml"], default="auto", help="Output format: markdown, toon (dense), ts (TypeScript d.ts), yaml (default: auto)")
    common_parser.add_argument("--path", default=".", help="Repository root path")

    parser = argparse.ArgumentParser(
        prog="git-context",
        description="Autonomous Living Memory & Rule Compiler for AI Coding Assistants.",
        parents=[common_parser]
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", parents=[common_parser], help="Initialize codebase context rules")
    p_init.set_defaults(func=cmd_init)

    # sync
    p_sync = subparsers.add_parser("sync", parents=[common_parser], help="Sync latest git commit diffs into rules")
    p_sync.add_argument("--target-ref", default="HEAD~1", help="Target git ref (default: HEAD~1)")
    p_sync.add_argument("--base-ref", default="HEAD", help="Base git ref (default: HEAD)")
    p_sync.set_defaults(func=cmd_sync)

    # diff
    p_diff = subparsers.add_parser("diff", parents=[common_parser], help="Preview architectural diff without writing")
    p_diff.add_argument("--target-ref", default="HEAD~1")
    p_diff.set_defaults(func=cmd_diff)

    # action (CI mode)
    p_action = subparsers.add_parser("action", parents=[common_parser], help="Run inside GitHub Actions CI")
    p_action.set_defaults(func=cmd_action)

    # hook
    p_hook = subparsers.add_parser("hook", parents=[common_parser], help="Install local git hooks")
    p_hook_subs = p_hook.add_subparsers(dest="hook_cmd", required=True)
    p_hook_inst = p_hook_subs.add_parser("install", parents=[common_parser], help="Install post-commit hook")
    p_hook_inst.set_defaults(func=cmd_hook_install)

    parsed = parser.parse_args()
    parsed.func(parsed)

if __name__ == "__main__":
    main()
