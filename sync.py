#!/usr/bin/env python3
"""Sync GitHub starred repos → classify via local Claude CLI → write stars.json.

Uses local tools:
  - gh CLI for GitHub API (auth already configured locally)
  - claude CLI for LLM classification (auth already configured locally)
  - git for commit & push (auth already configured locally)

No environment variables needed.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import yaml

# ---------------------------------------------------------------------------
# GitHub: fetch starred repos via gh CLI
# ---------------------------------------------------------------------------


def fetch_starred_repos() -> list[dict]:
    """Fetch all starred repos using `gh api` (locally authenticated)."""
    result = subprocess.run(
        ["gh", "api", "/user/starred", "--paginate", "--jq", ".[]"],
        capture_output=True, text=True, check=True,
    )
    # --jq '.[]' outputs one JSON object per line (JSONL)
    repos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        r = json.loads(line)
        repos.append({
            "full_name": r["full_name"],
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "topics": r.get("topics") or [],
            "html_url": r["html_url"],
            "stargazers_count": r.get("stargazers_count", 0),
            "created_at": r.get("created_at", ""),
            "updated_at": r.get("updated_at", ""),
        })

    return repos


def fetch_readme_excerpt(full_name: str, max_chars: int = 200) -> str:
    """Fetch the first `max_chars` of a repo's README via `gh api`."""
    try:
        result = subprocess.run(
            ["gh", "api", f"/repos/{full_name}/readme"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return ""
        data = json.loads(result.stdout)
        import base64
        content = base64.b64decode(data["content"]).decode(errors="replace")
        return content[:max_chars]
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Claude: classify repos via local claude CLI
# ---------------------------------------------------------------------------


def classify_repos_batch(repos: list[dict], readme_excerpts: dict[str, str]) -> dict[str, dict]:
    """Call local `claude` CLI to classify a batch of repos.

    Returns: {full_name: {category_id, category_name, category_description}}
    """
    import time

    repo_entries = []
    for r in repos:
        excerpt = (readme_excerpts.get(r["full_name"], "") or "")[:200]
        topics = ", ".join(r["topics"][:5]) if r["topics"] else "无"
        entry = (
            f"- {r['full_name']} | 描述:{r['description'][:100]} | 语言:{r['language']} | Topics:{topics}"
        )
        repo_entries.append(entry)

    prompt = (
        "分类以下 GitHub 项目，返回 JSON。自由创建中文分类名，相似项目归入同一类。\n\n"
        + "\n".join(repo_entries)
        + '\n\n返回格式: {"classifications":[{"full_name":"...","category_id":"slug","category_name":"中文","category_description":"..."}]}'
    )

    for attempt in range(3):
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)

            text = result.stdout.strip()

            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(text)

            classifications = {}
            for item in parsed["classifications"]:
                classifications[item["full_name"]] = {
                    "category_id": item["category_id"],
                    "category_name": item["category_name"],
                    "category_description": item["category_description"],
                }
            return classifications
        except Exception as e:
            print(f"    Attempt {attempt + 1}/3 failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(5 * (attempt + 1))

    # All retries failed — return empty classifications
    print(f"    WARNING: Failed to classify batch after 3 attempts", file=sys.stderr)
    return {}


# ---------------------------------------------------------------------------
# Load & merge overrides
# ---------------------------------------------------------------------------

CATALOG_TINTS = [
    "olive", "sage", "salmon", "peach", "lime", "sky", "steel", "periwinkle"
]


def load_overrides(path: str) -> dict:
    """Load overrides.yml, return empty dict if file doesn't exist."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("overrides", {}) if data else {}


# ---------------------------------------------------------------------------
# Build stars.json
# ---------------------------------------------------------------------------

def load_existing_stars(path: str) -> dict:
    """Load existing stars.json, return empty structure if not found."""
    if not os.path.exists(path):
        return {"last_updated": "", "categories": [], "stars": []}
    with open(path) as f:
        return json.load(f)


def compute_new_stars(fetched: list[dict], existing: dict) -> list[dict]:
    """Return repos that are in fetched but not in existing stars."""
    existing_names = {s["full_name"] for s in existing.get("stars", [])}
    return [r for r in fetched if r["full_name"] not in existing_names]


def assign_tints(category_ids: list[str]) -> dict[str, str]:
    """Assign catalog tint colors to category IDs, round-robin."""
    return {cid: CATALOG_TINTS[i % len(CATALOG_TINTS)] for i, cid in enumerate(category_ids)}


def build_stars_json(
    fetched: list[dict],
    classifications: dict[str, dict],
    overrides: dict,
) -> dict:
    """Build the final stars.json structure."""
    # Build category registry from classifications
    category_registry: dict[str, dict] = {}
    for full_name, cls in classifications.items():
        cid = cls["category_id"]
        if cid not in category_registry:
            category_registry[cid] = {
                "id": cid,
                "name": cls["category_name"],
                "description": cls["category_description"],
            }

    # Build star entries
    star_entries = []
    for r in fetched:
        full_name = r["full_name"]
        override_data = overrides.get(full_name, {})
        is_excluded = override_data.get("exclude", False)

        if is_excluded:
            continue

        cls = classifications.get(full_name)
        override_categories = override_data.get("categories")

        if override_categories:
            cat_ids = []
            for cat_name in override_categories:
                matched_id = None
                for cid, cdata in category_registry.items():
                    if cdata["name"] == cat_name:
                        matched_id = cid
                        break
                if not matched_id:
                    new_id = cat_name.lower().replace("/", "-").replace(" ", "-")
                    category_registry[new_id] = {
                        "id": new_id,
                        "name": cat_name,
                        "description": f"手动分类: {cat_name}",
                    }
                    matched_id = new_id
                cat_ids.append(matched_id)

            star_entries.append({
                **r,
                "categories": cat_ids,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "override": True,
            })
        elif cls:
            star_entries.append({
                **r,
                "categories": [cls["category_id"]],
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "override": False,
            })
        else:
            star_entries.append({
                **r,
                "categories": ["uncategorized"],
                "analyzed_at": "",
                "override": False,
            })

    # Add "uncategorized" to registry if needed
    if any("uncategorized" in s["categories"] for s in star_entries):
        if "uncategorized" not in category_registry:
            category_registry["uncategorized"] = {
                "id": "uncategorized",
                "name": "未分类",
                "description": "尚未分类的项目",
            }

    # Compute category counts and assign tints
    category_order = sorted(category_registry.keys())
    tints = assign_tints(category_order)

    categories_out = []
    for cid in category_order:
        cdata = category_registry[cid]
        count = sum(1 for s in star_entries if cid in s["categories"])
        categories_out.append({
            **cdata,
            "count": count,
            "tint": tints[cid],
        })

    # Sort stars by category then by stargazers_count descending
    star_entries.sort(key=lambda s: (s["categories"][0] if s["categories"] else "zzz", -s.get("stargazers_count", 0)))

    return {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "categories": categories_out,
        "stars": star_entries,
    }


# ---------------------------------------------------------------------------
# Git commit & push (uses local git auth)
# ---------------------------------------------------------------------------

def git_commit_push(file_path: str) -> None:
    """Commit and push the updated file using local git (auth already configured)."""
    subprocess.run(["git", "add", file_path], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Update {file_path} — auto star sync"],
        check=True,
    )
    subprocess.run(["git", "push"], check=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Sync GitHub stars → classify → stars.json")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch stars, skip classification")
    parser.add_argument("--full-refresh", action="store_true", help="Re-classify ALL stars, not just new ones")
    args = parser.parse_args()

    print("Fetching starred repos via gh CLI...")
    fetched = fetch_starred_repos()
    print(f"  Found {len(fetched)} starred repos")

    if args.fetch_only:
        with open("stars_raw.json", "w") as f:
            json.dump(fetched, f, indent=2, ensure_ascii=False)
        print("  Written to stars_raw.json (--fetch-only mode)")
        return

    existing = load_existing_stars("stars.json")
    overrides = load_overrides("overrides.yml")

    if args.full_refresh:
        repos_to_classify = fetched
        print(f"  Full refresh: classifying all {len(repos_to_classify)} repos")
    else:
        repos_to_classify = compute_new_stars(fetched, existing)
        print(f"  Incremental: {len(repos_to_classify)} new repos to classify")

    # Fetch README excerpts for repos to classify
    readme_excerpts = {}
    if repos_to_classify:
        print("  Fetching README excerpts via gh CLI...")
        for r in repos_to_classify:
            excerpt = fetch_readme_excerpt(r["full_name"])
            readme_excerpts[r["full_name"]] = excerpt

    # Classify in batches of 10 via local claude CLI
    classifications = {}
    if repos_to_classify:
        import time
        batch_size = 10
        for i in range(0, len(repos_to_classify), batch_size):
            batch = repos_to_classify[i:i + batch_size]
            print(f"  Classifying batch {i // batch_size + 1} ({len(batch)} repos) via claude CLI...")
            result = classify_repos_batch(batch, readme_excerpts)
            classifications.update(result)
            if i + batch_size < len(repos_to_classify):
                time.sleep(3)  # Brief pause between batches

    # For incremental, preserve existing classifications from stars.json
    if not args.full_refresh:
        for s in existing.get("stars", []):
            if s["full_name"] not in classifications:
                classifications[s["full_name"]] = {
                    "category_id": s["categories"][0] if s["categories"] else "uncategorized",
                    "category_name": "",
                    "category_description": "",
                }

    # Fill category names for existing entries from the existing categories list
    existing_cat_map = {c["id"]: c for c in existing.get("categories", [])}
    for full_name, cls in classifications.items():
        if cls["category_name"] == "" and cls["category_id"] in existing_cat_map:
            cls["category_name"] = existing_cat_map[cls["category_id"]]["name"]
            cls["category_description"] = existing_cat_map[cls["category_id"]]["description"]

    # Build final stars.json
    stars_json = build_stars_json(fetched, classifications, overrides)

    # Write stars.json
    with open("stars.json", "w") as f:
        json.dump(stars_json, f, indent=2, ensure_ascii=False)
    print(f"  Written stars.json: {len(stars_json['categories'])} categories, {len(stars_json['stars'])} stars")

    # Copy to web/public/ for frontend access
    web_public = os.path.join("web", "public")
    os.makedirs(web_public, exist_ok=True)
    with open(os.path.join(web_public, "stars.json"), "w") as f:
        json.dump(stars_json, f, indent=2, ensure_ascii=False)
    print("  Copied to web/public/stars.json")

    # Commit and push
    print("  Committing and pushing via local git...")
    git_commit_push("stars.json")


if __name__ == "__main__":
    main()
