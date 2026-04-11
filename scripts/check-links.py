#!/usr/bin/env python3
"""Check all links in data/entries.json for availability.

Usage:
    python3 scripts/check-links.py           # check all links
    python3 scripts/check-links.py --fix     # (reserved) auto-fix broken links
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TIMEOUT = 5
MAX_WORKERS = 10
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "entries.json")


def is_url(s):
    """Check if string looks like a URL."""
    return s.startswith("http://") or s.startswith("https://")


def check_url(url):
    """HEAD request to check URL availability. Falls back to GET if HEAD fails."""
    if not is_url(url):
        return url, 0, "Not a URL"
    try:
        req = Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        with urlopen(req, timeout=TIMEOUT) as resp:
            return url, resp.status, None
    except HTTPError as e:
        # Some servers reject HEAD; try GET
        if e.code == 405:
            try:
                req = Request(url, method="GET")
                req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                with urlopen(req, timeout=TIMEOUT) as resp:
                    return url, resp.status, None
            except Exception as e2:
                return url, 0, str(e2)
        return url, e.code, str(e)
    except (URLError, OSError) as e:
        return url, 0, str(e)
    except Exception as e:
        return url, 0, str(e)


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Collect all URLs
    urls = []
    for entry in data["entries"]:
        for link_type, url in entry.get("links", {}).items():
            if is_url(url):
                urls.append((entry["id"], entry["name"], link_type, url))

    # Deduplicate (same URL can appear in multiple entries)
    seen = set()
    unique_urls = []
    for eid, name, ltype, url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append((eid, name, ltype, url))

    print(f"Checking {len(unique_urls)} unique URLs (from {len(urls)} total link references)...")
    print()

    broken = []
    checked = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(check_url, url): (eid, name, ltype, url) for eid, name, ltype, url in unique_urls}
        for future in as_completed(futures):
            eid, name, ltype, url = futures[future]
            url_result, status, error = future.result()
            checked += 1
            if status >= 400 or status == 0:
                broken.append((eid, name, ltype, url, status, error))
                status_str = f"HTTP {status}" if status else "FAIL"
                print(f"  ✗ [{status_str}] {name} → {ltype}: {url}")
                if error:
                    print(f"    Error: {error}")
            elif checked % 20 == 0:
                print(f"  ... checked {checked}/{len(unique_urls)}", end="\r")

    elapsed = time.time() - start
    print()
    print(f"Done. {checked} URLs checked in {elapsed:.1f}s.")

    if broken:
        print(f"\n❌ {len(broken)} broken link(s) found:")
        for eid, name, ltype, url, status, error in broken:
            print(f"  - [{eid}] {name} | {ltype} | {url}")
        sys.exit(1)
    else:
        print("\n✅ All links are healthy!")
        sys.exit(0)


if __name__ == "__main__":
    main()
