#!/usr/bin/env python3
"""Sync GitHub starred repos → classify via local Claude CLI → write stars.json.

Uses local tools:
  - gh CLI for GitHub API (auth already configured locally)
  - claude CLI for LLM classification (auth already configured locally)
  - git for commit & push (auth already configured locally)

Caching:
  - cache.json stores README excerpts and repo metadata
  - Full refresh reuses cached READMEs (no re-fetch from GitHub API)
  - Only new repos trigger fresh README fetches

No environment variables needed.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import yaml

CACHE_FILE = "cache.json"

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    """Load cache.json, return empty dict if not found."""
    if not os.path.exists(CACHE_FILE):
        return {"readmes": {}, "repos": {}}
    with open(CACHE_FILE) as f:
        return json.load(f)


def save_cache(cache: dict) -> None:
    cache["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# GitHub: fetch starred repos via gh CLI
# ---------------------------------------------------------------------------

def fetch_starred_repos() -> list[dict]:
    """Fetch all starred repos metadata (fast, no README fetch)."""
    result = subprocess.run(
        ["gh", "api", "/user/starred", "--paginate", "--jq", ".[]"],
        capture_output=True, text=True, check=True,
    )
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
            "updated_at": r.get("pushed_at", r.get("updated_at", "")),
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


def get_readme_excerpts(repos: list[dict], cache: dict) -> dict[str, str]:
    """Get README excerpts, using cache when available. Only fetches missing ones."""
    excerpts = {}
    cached_readmes = cache.get("readmes", {})
    new_fetches = 0

    for r in repos:
        fn = r["full_name"]
        if fn in cached_readmes and cached_readmes[fn]:
            excerpts[fn] = cached_readmes[fn]
        else:
            excerpt = fetch_readme_excerpt(fn)
            excerpts[fn] = excerpt
            cached_readmes[fn] = excerpt
            new_fetches += 1

    if new_fetches:
        cache["readmes"] = cached_readmes
        save_cache(cache)
        print(f"    Fetched {new_fetches} new README excerpts (cached: {len(cached_readmes) - new_fetches})")
    else:
        print(f"    All {len(excerpts)} README excerpts from cache")

    return excerpts


# ---------------------------------------------------------------------------
# Claude: classify repos via local claude CLI
# ---------------------------------------------------------------------------

def classify_repos_batch(
    repos: list[dict],
    readme_excerpts: dict[str, str],
    existing_categories: dict[str, dict] | None = None,
) -> dict[str, dict]:
    """Call local `claude` CLI to classify a batch of repos.

    existing_categories: {cid: {name, description}} — passed to each batch so
    the model reuses existing categories instead of creating new synonyms.

    Returns: {full_name: {category_ids, category_name, category_description, description_cn}}
    """
    repo_entries = []
    for r in repos:
        excerpt = (readme_excerpts.get(r["full_name"], "") or "")[:200]
        topics = ", ".join(r["topics"][:5]) if r["topics"] else "无"
        entry = (
            f"- {r['full_name']} | 描述:{r['description'][:100]} | 语言:{r['language']} | Topics:{topics}"
        )
        repo_entries.append(entry)

    # Build existing category context
    cat_context = ""
    if existing_categories:
        cat_list = "\n".join(
            f"  [{cid}] {info['name']} — {info.get('description','')}"
            for cid, info in sorted(existing_categories.items())
        )
        cat_context = f"\n已有分类（必须优先复用，非必要不创建新分类）:\n{cat_list}\n"

    prompt = (
        "分类以下 GitHub 项目，并将每个项目的英文描述翻译为简体中文，保留专有名词。"
        "使用宽泛的中文分类名（总计控制在 25 个以内），务必优先复用已有分类，相似项目归入同一类。"
        "一个项目可以同时属于多个分类（如既是 Skills 又是 AI Agent），返回数组。"
        "Skills 类型项目（AI 编程技能、提示词工程、工作流 Skill 等）统一归入「Skills」分类。"
        + cat_context + "\n"
        + "\n".join(repo_entries)
        + '\n\n返回格式: {"classifications":[{"full_name":"...","category_ids":["slug1","slug2"],"category_name":"中文主分类","category_description":"简短描述","description_cn":"中文项目描述"}]}'
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
                cat_ids = item.get("category_ids", [item.get("category_id", "uncategorized")])
                if isinstance(cat_ids, str):
                    cat_ids = [cat_ids]
                classifications[item["full_name"]] = {
                    "category_ids": cat_ids,
                    "category_name": item["category_name"],
                    "category_description": item["category_description"],
                    "description_cn": item.get("description_cn", ""),
                }
            return classifications
        except Exception as e:
            print(f"    Attempt {attempt + 1}/3 failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(5 * (attempt + 1))

    print(f"    WARNING: Failed to classify batch after 3 attempts", file=sys.stderr)
    return {}


# ---------------------------------------------------------------------------
# Load & merge overrides
# ---------------------------------------------------------------------------

CATALOG_TINTS = [
    "olive", "sage", "salmon", "peach", "lime", "sky", "steel", "periwinkle"
]


def load_overrides(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("overrides", {}) if data else {}


# ---------------------------------------------------------------------------
# Build stars.json
# ---------------------------------------------------------------------------

def load_existing_stars(path: str) -> dict:
    if not os.path.exists(path):
        return {"last_updated": "", "categories": [], "stars": []}
    with open(path) as f:
        return json.load(f)


def compute_new_stars(fetched: list[dict], existing: dict) -> list[dict]:
    existing_names = {s["full_name"] for s in existing.get("stars", [])}
    return [r for r in fetched if r["full_name"] not in existing_names]


def assign_tints(category_ids: list[str]) -> dict[str, str]:
    return {cid: CATALOG_TINTS[i % len(CATALOG_TINTS)] for i, cid in enumerate(category_ids)}


def build_stars_json(
    fetched: list[dict],
    classifications: dict[str, dict],
    overrides: dict,
) -> dict:
    # Build category registry from classifications
    category_registry: dict[str, dict] = {}
    for full_name, cls in classifications.items():
        for cid in cls["category_ids"]:
            if cid not in category_registry:
                category_registry[cid] = {
                    "id": cid,
                    "name": cls.get("category_name", cid),
                    "description": cls.get("category_description", ""),
                }

    star_entries = []
    for r in fetched:
        full_name = r["full_name"]
        override_data = overrides.get(full_name, {})
        if override_data.get("exclude", False):
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
                        "id": new_id, "name": cat_name,
                        "description": f"手动分类: {cat_name}",
                    }
                    matched_id = new_id
                cat_ids.append(matched_id)
            star_entries.append({**r, "categories": cat_ids,
                "analyzed_at": datetime.now(timezone.utc).isoformat(), "override": True})
        elif cls:
            star_entries.append({**r, "categories": cls["category_ids"],
                "analyzed_at": datetime.now(timezone.utc).isoformat(), "override": False})
        else:
            star_entries.append({**r, "categories": ["uncategorized"],
                "analyzed_at": "", "override": False})

    if any("uncategorized" in s["categories"] for s in star_entries):
        if "uncategorized" not in category_registry:
            category_registry["uncategorized"] = {
                "id": "uncategorized", "name": "未分类", "description": "尚未分类的项目",
            }

    category_order = sorted(category_registry.keys())
    tints = assign_tints(category_order)
    categories_out = []
    for cid in category_order:
        cdata = category_registry[cid]
        count = sum(1 for s in star_entries if cid in s["categories"])
        categories_out.append({**cdata, "count": count, "tint": tints[cid]})

    star_entries.sort(key=lambda s: (
        s["categories"][0] if s["categories"] else "zzz",
        -s.get("stargazers_count", 0),
    ))

    return {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "categories": categories_out,
        "stars": star_entries,
    }


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

def git_commit_push(file_path: str) -> None:
    subprocess.run(["git", "add", file_path], check=True)
    subprocess.run(["git", "commit", "-m", f"Update {file_path} — auto star sync"], check=True)
    subprocess.run(["git", "push"], check=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Always chdir to script directory, so relative paths work from cron
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    parser = argparse.ArgumentParser(description="Sync GitHub stars → classify → stars.json")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch stars, skip classification")
    parser.add_argument("--full-refresh", action="store_true", help="Re-classify ALL stars (uses cached READMEs)")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache, re-fetch all READMEs")
    args = parser.parse_args()

    cache = {} if args.no_cache else load_cache()
    if "readmes" not in cache:
        cache["readmes"] = {}

    # Step 1: Fetch star metadata (always from GitHub — fast)
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

    # Step 2: Determine what to classify
    if args.full_refresh:
        repos_to_classify = fetched
        print(f"  Full refresh: classifying all {len(repos_to_classify)} repos")
    else:
        repos_to_classify = compute_new_stars(fetched, existing)
        fetched_names = {r["full_name"] for r in fetched}
        removed = [s["full_name"] for s in existing.get("stars", []) if s["full_name"] not in fetched_names]
        if removed:
            print(f"  Removed (unstarred): {len(removed)} repos — will be dropped from stars.json")
        print(f"  Incremental: {len(repos_to_classify)} new repos to classify")

    # Step 3: Get README excerpts (from cache when possible)
    readme_excerpts = {}
    if repos_to_classify:
        print("  Loading README excerpts...")
        readme_excerpts = get_readme_excerpts(repos_to_classify, cache)

    # Step 4: Classify with Claude, passing accumulated categories across batches
    classifications = {}
    accumulated_cats: dict[str, dict] = {}
    if repos_to_classify:
        batch_size = 10
        for i in range(0, len(repos_to_classify), batch_size):
            batch = repos_to_classify[i:i + batch_size]
            print(f"  Classifying batch {i // batch_size + 1} ({len(batch)} repos) via claude CLI...")
            result = classify_repos_batch(batch, readme_excerpts, accumulated_cats if accumulated_cats else None)
            classifications.update(result)
            # Accumulate categories from this batch
            for cls in result.values():
                for cid in cls["category_ids"]:
                    if cid not in accumulated_cats:
                        accumulated_cats[cid] = {
                            "name": cls["category_name"],
                            "description": cls["category_description"],
                        }
            if i + batch_size < len(repos_to_classify):
                time.sleep(3)

    # Step 5: Apply translated descriptions
    for r in fetched:
        fn = r["full_name"]
        if fn in classifications and classifications[fn].get("description_cn"):
            r["description"] = classifications[fn]["description_cn"]

    # Step 6: Preserve existing classifications in incremental mode
    if not args.full_refresh:
        for s in existing.get("stars", []):
            if s["full_name"] not in classifications:
                classifications[s["full_name"]] = {
                    "category_ids": s["categories"] if s["categories"] else ["uncategorized"],
                    "category_name": "",
                    "category_description": "",
                }

    # Fill category names from existing data
    existing_cat_map = {c["id"]: c for c in existing.get("categories", [])}
    for full_name, cls in classifications.items():
        if cls["category_name"] == "" and cls["category_ids"]:
            first_id = cls["category_ids"][0]
            if first_id in existing_cat_map:
                cls["category_name"] = existing_cat_map[first_id]["name"]
                cls["category_description"] = existing_cat_map[first_id]["description"]

    # Step 7: Build and write stars.json
    stars_json = build_stars_json(fetched, classifications, overrides)

    with open("stars.json", "w") as f:
        json.dump(stars_json, f, indent=2, ensure_ascii=False)
    print(f"  Written stars.json: {len(stars_json['categories'])} categories, {len(stars_json['stars'])} stars")

    web_public = os.path.join("web", "public")
    os.makedirs(web_public, exist_ok=True)
    with open(os.path.join(web_public, "stars.json"), "w") as f:
        json.dump(stars_json, f, indent=2, ensure_ascii=False)
    print("  Copied to web/public/stars.json")

    # Step 8: Commit and push
    print("  Committing and pushing via local git...")
    git_commit_push("stars.json")


if __name__ == "__main__":
    main()
