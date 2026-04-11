#!/usr/bin/env python3
"""Discover new dev sources from Android Weekly and RSS lists.

Designed to be run as a cron task via OpenClaw.
Writes candidate sources to data/candidates.json (human review required).

Usage:
    python3 scripts/discover-sources.py
"""

import json
import os
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ENTRIES_PATH = os.path.join(DATA_DIR, "entries.json")
CANDIDATES_PATH = os.path.join(DATA_DIR, "candidates.json")
TIMEOUT = 10

USER_AGENT = "Dev-Feeds-Discoverer/1.0"


def fetch_url(url):
    """Fetch URL content as text."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_domains(html, existing_domains):
    """Extract unique domains from HTML that aren't in existing set."""
    # Find all http(s) links
    urls = re.findall(r'https?://([^/"\'<>#\s]+)', html)
    domains = set()
    for domain in urls:
        # Skip common non-blog domains
        skip = [
            "github.com", "google.com", "developer.android.com", "android.com",
            "reddit.com", "youtube.com", "twitter.com", "x.com", "medium.com",
            "stackoverflow.com", "linkedin.com", "facebook.com", "instagram.com",
            "goo.gl", "bit.ly", "t.co", "feedburner.com", "feedproxy.google.com",
        ]
        if any(domain == s or domain.endswith("." + s) for s in skip):
            continue
        if domain not in existing_domains:
            domains.add(domain)
    return domains


def load_existing_domains(data):
    """Extract all domains already in entries.json."""
    domains = set()
    for entry in data.get("entries", []):
        for url in entry.get("links", {}).values():
            match = re.match(r'https?://([^/"\'<>#\s]+)', url)
            if match:
                domains.add(match.group(1))
    return domains


def load_candidates():
    """Load existing candidates."""
    if os.path.exists(CANDIDATES_PATH):
        with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"candidates": []}


def save_candidates(candidates_data):
    with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates_data, f, indent=2, ensure_ascii=False)


def check_android_weekly(existing_domains):
    """Fetch Android Weekly issues page and extract new domains."""
    new_sources = []
    try:
        html = fetch_url("https://androidweekly.net/issues")
        domains = extract_domains(html, existing_domains)
        for domain in sorted(domains):
            new_sources.append({
                "domain": domain,
                "source": "android-weekly",
                "url": f"https://{domain}",
                "suggested_category": "android-blog",
            })
    except Exception as e:
        print(f"⚠️  Android Weekly fetch failed: {e}")
    return new_sources


def check_saveweb_rss_list(existing_domains):
    """Check saveweb/rss-list releases for new RSS feeds."""
    new_sources = []
    try:
        html = fetch_url("https://github.com/saveweb/rss-list/releases")
        domains = extract_domains(html, existing_domains)
        for domain in sorted(domains):
            new_sources.append({
                "domain": domain,
                "source": "saveweb/rss-list",
                "url": f"https://{domain}",
                "suggested_category": "general-tech",
            })
    except Exception as e:
        print(f"⚠️  saveweb/rss-list fetch failed: {e}")
    return new_sources


def main():
    print("🔍 Dev-Feeds Source Discovery")
    print("=" * 40)

    # Load existing data
    with open(ENTRIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    existing_domains = load_existing_domains(data)
    print(f"Existing domains in entries.json: {len(existing_domains)}")

    # Load existing candidates
    candidates_data = load_candidates()
    existing_candidates = {c["domain"] for c in candidates_data.get("candidates", [])}
    print(f"Existing candidates: {len(existing_candidates)}")

    # Discover
    all_new = []
    all_new.extend(check_android_weekly(existing_domains | existing_candidates))
    all_new.extend(check_saveweb_rss_list(existing_domains | existing_candidates))

    # Deduplicate
    seen = set()
    unique_new = []
    for item in all_new:
        if item["domain"] not in seen:
            seen.add(item["domain"])
            unique_new.append(item)

    if not unique_new:
        print("\n✅ No new sources discovered.")
        return

    # Merge with existing candidates
    for item in unique_new:
        if item["domain"] not in existing_candidates:
            candidates_data.setdefault("candidates", []).append(item)

    save_candidates(candidates_data)

    # Print summary
    print(f"\n📬 Found {len(unique_new)} new candidate(s):")
    for item in unique_new:
        print(f"  • {item['domain']} (from {item['source']})")

    print(f"\nTotal candidates awaiting review: {len(candidates_data.get('candidates', []))}")
    print(f"Candidates saved to: data/candidates.json")
    print("\n⚠️  These need human review before adding to entries.json")


if __name__ == "__main__":
    main()
