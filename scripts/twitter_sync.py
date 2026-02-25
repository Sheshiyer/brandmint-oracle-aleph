#!/usr/bin/env python3
"""
twitter_sync.py — Weekly Twitter + Web sync for Brandmint references pool.

Pulls tweets from multiple sources via bird CLI, filters for relevance using
keyword matching + engagement thresholds, extracts URLs, fetches linked web
pages, and saves structured references locally.

Three-layer architecture:
  Layer 1: Twitter Discovery (bird CLI → filter → classify)
  Layer 2: Web Content Extraction (URLs → fetch → extract)
  Layer 3: Save (archive, curated, learnings, state)

Usage:
  python3 scripts/twitter_sync.py
  python3 scripts/twitter_sync.py --sources bookmarks,search --min-likes 100
  python3 scripts/twitter_sync.py --dry-run

Dependencies: Python stdlib only (no pip install required).
Requires: bird CLI v0.8.0+ at /opt/homebrew/bin/bird
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser


# =====================================================================
# CONFIGURATION
# =====================================================================

BIRD_CLI = "/opt/homebrew/bin/bird"

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "references", "twitter-sync")
WEB_CACHE_DIR = os.path.join(BASE_DIR, "web-cache")
LEARNINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "references", "learnings.md")

# Search queries for bird search
SEARCH_QUERIES = {
    "ai_prompts": "AI prompts",
    "brand_identity": "brand identity AI",
    "image_gen": "flux midjourney prompts",
}

# Accounts to track via bird user-tweets
TRACKED_ACCOUNTS = [
    "alex_prompter",
    "godofprompt",
]

# Domain allowlist for web fetching
ALLOWED_DOMAINS = {
    "godofprompt.ai",
    "www.godofprompt.ai",
    "promptbase.com",
    "www.promptbase.com",
    "github.com",
    "anthropic.com",
    "www.anthropic.com",
    "docs.anthropic.com",
    "openai.com",
    "www.openai.com",
    "platform.openai.com",
    "replicate.com",
    "www.replicate.com",
    "fal.ai",
    "www.fal.ai",
    "huggingface.co",
    "www.huggingface.co",
}

# Web fetch limits
WEB_FETCH_DELAY_SECS = 2
WEB_FETCH_MAX_PER_RUN = 20
WEB_CACHE_TTL_DAYS = 7

# Relevance scoring keywords
TIER_1_KEYWORDS = [
    "prompt", "brand", "identity", "visual", "design system", "color palette",
    "ai image", "flux", "midjourney", "dalle", "dall-e", "recraft", "claude",
    "gemini", "stable diffusion", "nano banana", "fal.ai",
]
TIER_1_MIN_LIKES = 50

TIER_2_KEYWORDS = [
    "marketing", "startup", "template", "workflow", "automation",
    "branding", "logo", "typography", "packaging",
]
TIER_2_MIN_LIKES = 100

# Blocklist patterns (regex) for spam filtering
BLOCKLIST_PATTERNS = [
    r"(?i)\b(crypto|nft|web3|airdrop|giveaway)\b",
    r"(?i)\b(follow.*like.*retweet|rt to win)\b",
    r"(?i)\b(dm me for|send me \$)\b",
]

# URL extraction regex (t.co links + full URLs)
URL_RE = re.compile(r"https?://[^\s)<>\"]+")


# =====================================================================
# LAYER 1: TWITTER DISCOVERY
# =====================================================================

def run_bird(args, timeout=30):
    """Run a bird CLI command and return parsed JSON output."""
    cmd = [BIRD_CLI] + args + ["--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            stderr = result.stderr.strip()
            print(f"  WARN: bird {' '.join(args[:2])} failed: {stderr}", file=sys.stderr)
            return []
        if not result.stdout.strip():
            return []
        # Clean invalid control characters that bird sometimes emits
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", result.stdout)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Bird occasionally emits truncated JSON for large payloads.
            # Try to salvage by finding the last complete object in an array.
            trimmed = cleaned.rstrip()
            if trimmed.startswith("["):
                # Find last complete }, then close the array
                last_brace = trimmed.rfind("}")
                if last_brace > 0:
                    candidate = trimmed[:last_brace + 1] + "]"
                    try:
                        data = json.loads(candidate)
                    except json.JSONDecodeError:
                        print(f"  WARN: bird {' '.join(args[:2])} JSON unrecoverable", file=sys.stderr)
                        return []
                else:
                    return []
            else:
                return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "tweets" in data:
            return data["tweets"]
        return [data] if data else []
    except subprocess.TimeoutExpired:
        print(f"  WARN: bird {' '.join(args[:2])} timed out after {timeout}s", file=sys.stderr)
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  WARN: bird {' '.join(args[:2])} error: {e}", file=sys.stderr)
        return []


def pull_bookmarks(count=50):
    """Pull bookmarked tweets via bird CLI."""
    print(f"  Pulling bookmarks (n={count})...")
    return run_bird(["bookmarks", "-n", str(count)])


def pull_search(query, count=20):
    """Pull search results for a query via bird CLI."""
    print(f"  Searching: \"{query}\" (n={count})...")
    return run_bird(["search", query, "-n", str(count)])


def pull_account(handle, count=10):
    """Pull recent tweets from a specific account via bird CLI."""
    print(f"  Pulling @{handle} tweets (n={count})...")
    return run_bird(["user-tweets", handle, "-n", str(count)])


def dedup_tweets(tweets):
    """Deduplicate tweets by ID, preserving order."""
    seen = set()
    unique = []
    for tweet in tweets:
        tid = tweet.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            unique.append(tweet)
    return unique


def extract_urls(text):
    """Extract URLs from tweet text."""
    if not text:
        return []
    return URL_RE.findall(text)


def is_blocked(text):
    """Check if tweet text matches any blocklist pattern."""
    if not text:
        return False
    for pattern in BLOCKLIST_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def score_relevance(tweet, min_likes_override=None):
    """Score a tweet's relevance. Returns (tier, score) or (0, 0.0) if irrelevant.

    Tier 1 = high signal (prompt/brand/AI image keywords + >50 likes)
    Tier 2 = moderate signal (marketing/startup keywords + >100 likes)
    Tier 0 = discard
    """
    text = (tweet.get("text") or "").lower()
    likes = tweet.get("likeCount", 0) or 0
    retweets = tweet.get("retweetCount", 0) or 0

    if is_blocked(text):
        return 0, 0.0

    # Check quoted tweet text too
    qt = tweet.get("quotedTweet")
    if qt:
        text += " " + (qt.get("text") or "").lower()

    # Tier 1 check
    t1_min = min_likes_override if min_likes_override is not None else TIER_1_MIN_LIKES
    t1_matches = sum(1 for kw in TIER_1_KEYWORDS if kw in text)
    if t1_matches > 0 and likes >= t1_min:
        score = min(1.0, 0.3 + (t1_matches * 0.1) + (likes / 1000) + (retweets / 500))
        return 1, round(score, 3)

    # Tier 2 check
    t2_min = min_likes_override if min_likes_override is not None else TIER_2_MIN_LIKES
    t2_matches = sum(1 for kw in TIER_2_KEYWORDS if kw in text)
    if t2_matches > 0 and likes >= t2_min:
        score = min(1.0, 0.2 + (t2_matches * 0.08) + (likes / 2000) + (retweets / 1000))
        return 2, round(score, 3)

    return 0, 0.0


# =====================================================================
# LAYER 2: WEB CONTENT EXTRACTION
# =====================================================================

class SimpleHTMLExtractor(HTMLParser):
    """Minimal HTML parser to extract title, meta description, and body text."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.body_text = []
        self._in_title = False
        self._in_body = False
        self._in_script = False
        self._in_style = False
        self._in_nav = False
        self._in_footer = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            if name == "description":
                self.description = attrs_dict.get("content", "")
        elif tag == "body":
            self._in_body = True
        elif tag == "script":
            self._in_script = True
        elif tag == "style":
            self._in_style = True
        elif tag == "nav":
            self._in_nav = True
        elif tag == "footer":
            self._in_footer = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "body":
            self._in_body = False
        elif tag == "script":
            self._in_script = False
        elif tag == "style":
            self._in_style = False
        elif tag == "nav":
            self._in_nav = False
        elif tag == "footer":
            self._in_footer = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif (self._in_body and not self._in_script and not self._in_style
              and not self._in_nav and not self._in_footer):
            text = data.strip()
            if text:
                self.body_text.append(text)

    def get_content(self, max_chars=5000):
        """Return extracted content truncated to max_chars."""
        full = " ".join(self.body_text)
        # Collapse whitespace
        full = re.sub(r"\s+", " ", full).strip()
        return full[:max_chars]


def is_allowed_domain(url):
    """Check if URL is from an allowlisted domain."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname in ALLOWED_DOMAINS
    except Exception:
        return False


def url_cache_path(url):
    """Return the cache file path for a URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.hostname or "unknown"
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return os.path.join(WEB_CACHE_DIR, domain, f"{url_hash}.json")


def is_cache_valid(cache_path):
    """Check if a cached page exists and is within TTL."""
    if not os.path.exists(cache_path):
        return False
    try:
        mtime = os.path.getmtime(cache_path)
        age = time.time() - mtime
        return age < (WEB_CACHE_TTL_DAYS * 86400)
    except OSError:
        return False


def fetch_page(url, fetch_counter):
    """Fetch a web page and extract content. Uses cache. Returns dict or None.

    fetch_counter is a mutable list [count] to track fetches across calls.
    """
    if not is_allowed_domain(url):
        return None

    if fetch_counter[0] >= WEB_FETCH_MAX_PER_RUN:
        return None

    cache_path = url_cache_path(url)

    # Check cache
    if is_cache_valid(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    # Rate limit
    if fetch_counter[0] > 0:
        time.sleep(WEB_FETCH_DELAY_SECS)

    fetch_counter[0] += 1
    print(f"    Fetching [{fetch_counter[0]}/{WEB_FETCH_MAX_PER_RUN}]: {url[:80]}...")

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BrandmintSync/1.0",
            "Accept": "text/html,application/xhtml+xml",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        extractor = SimpleHTMLExtractor()
        extractor.feed(html)

        result = {
            "url": url,
            "title": extractor.title.strip(),
            "description": extractor.description.strip(),
            "content_preview": extractor.get_content(5000),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save to cache
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(result, f, indent=2)

        return result

    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        print(f"    WARN: Failed to fetch {url[:60]}: {e}", file=sys.stderr)
        return None


def resolve_tco_url(url):
    """Attempt to resolve a t.co shortened URL to its destination."""
    if "t.co/" not in url:
        return url
    try:
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "Mozilla/5.0 BrandmintSync/1.0",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.url
    except Exception:
        return url


# =====================================================================
# LAYER 3: SAVE
# =====================================================================

def load_state():
    """Load sync state from disk."""
    state_path = os.path.join(BASE_DIR, "state.json")
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "last_sync": None,
        "bookmark_cursor": None,
        "search_cursors": {},
        "seen_tweet_ids": [],
    }


def save_state(state):
    """Save sync state to disk."""
    state_path = os.path.join(BASE_DIR, "state.json")
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def save_sync_archive(all_tweets, filtered_tweets, date_str, source_counts):
    """Save the daily sync archive."""
    archive = {
        "sync_date": date_str,
        "sources": source_counts,
        "tweets": all_tweets,
        "stats": {
            "total_pulled": source_counts.get("_total_raw", 0),
            "after_dedup": len(all_tweets),
            "after_filter": len(filtered_tweets),
        },
    }
    # Remove internal stat
    archive["sources"].pop("_total_raw", None)

    path = os.path.join(BASE_DIR, f"sync-{date_str}.json")
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(archive, f, indent=2)
    print(f"  Archive: {path} ({len(all_tweets)} tweets)")
    return path


def load_curated():
    """Load existing curated.json or create empty."""
    path = os.path.join(BASE_DIR, "curated.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_updated": None, "entries": []}


def update_curated(curated, new_entries, date_str):
    """Append new entries to curated.json (deduped by tweet ID)."""
    existing_ids = {e["id"] for e in curated["entries"]}
    added = 0
    for entry in new_entries:
        if entry["id"] not in existing_ids:
            curated["entries"].append(entry)
            existing_ids.add(entry["id"])
            added += 1

    curated["last_updated"] = date_str

    path = os.path.join(BASE_DIR, "curated.json")
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(curated, f, indent=2)
    print(f"  Curated: {path} (+{added} new, {len(curated['entries'])} total)")
    return added


def update_learnings(high_signal_entries):
    """Auto-append high-signal entries to references/learnings.md."""
    if not high_signal_entries:
        return 0

    # Read existing to find next section number
    next_num = 15  # default after existing 14 sections
    if os.path.exists(LEARNINGS_PATH):
        try:
            with open(LEARNINGS_PATH, "r") as f:
                content = f.read()
            # Find highest existing section number
            nums = re.findall(r"^## (\d+)\.", content, re.MULTILINE)
            if nums:
                next_num = max(int(n) for n in nums) + 1
        except OSError:
            pass

    appended = 0
    lines = []
    for entry in high_signal_entries:
        title = entry.get("title") or f"Discovery from @{entry.get('author', 'unknown')}"
        # Clean title
        title = title.strip()
        if len(title) > 80:
            title = title[:77] + "..."

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## {next_num}. {title} (via Twitter Sync)")
        lines.append("")
        lines.append(f"**Source:** {entry.get('url', 'N/A')} by @{entry.get('author', 'unknown')} ({entry.get('synced_at', 'N/A')})")

        likes = entry.get("likes", 0)
        rts = entry.get("retweets", 0)
        lines.append(f"**Signal:** {likes} likes, {rts} RTs")
        lines.append("")

        text = entry.get("text", "").strip()
        if text:
            lines.append(f"**Learning:** {text}")
            lines.append("")

        ext_links = entry.get("extracted_links", [])
        if ext_links:
            lines.append(f"**Reference:** {', '.join(ext_links[:5])}")
            lines.append("")

        web_content = entry.get("web_content")
        if web_content:
            wc_title = web_content.get("title", "")
            wc_preview = web_content.get("content_preview", "")[:500]
            if wc_title or wc_preview:
                summary = wc_title
                if wc_preview:
                    summary += f" — {wc_preview}" if summary else wc_preview
                lines.append(f"**Web Content:** {summary}")
                lines.append("")

        next_num += 1
        appended += 1

    if lines:
        with open(LEARNINGS_PATH, "a") as f:
            f.write("\n".join(lines))
        print(f"  Learnings: {LEARNINGS_PATH} (+{appended} new sections)")

    return appended


# =====================================================================
# ORCHESTRATION
# =====================================================================

def build_curated_entry(tweet, tier, score, web_contents, date_str):
    """Build a curated entry from a scored tweet + fetched web content."""
    text = tweet.get("text", "")
    urls = extract_urls(text)

    # Resolve t.co URLs
    resolved = []
    for u in urls:
        if "t.co/" in u:
            resolved.append(resolve_tco_url(u))
        else:
            resolved.append(u)

    # Auto-tag based on keywords
    tags = []
    text_lower = text.lower()
    tag_map = {
        "prompt-library": ["prompt library", "prompt collection", "prompt database"],
        "claude": ["claude", "anthropic"],
        "gemini": ["gemini"],
        "chatgpt": ["chatgpt", "gpt-4", "gpt4", "openai"],
        "midjourney": ["midjourney"],
        "flux": ["flux"],
        "recraft": ["recraft"],
        "brand-design": ["brand identity", "brand design", "branding"],
        "image-gen": ["image generation", "text to image", "ai image"],
        "workflow": ["workflow", "automation", "pipeline"],
    }
    for tag, keywords in tag_map.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)

    # Attach first matching web content
    web_content = None
    for ru in resolved:
        if ru in web_contents:
            web_content = web_contents[ru]
            break

    author = tweet.get("author", {})
    username = author.get("username", "unknown") if isinstance(author, dict) else "unknown"

    entry = {
        "id": tweet.get("id", ""),
        "url": f"https://x.com/{username}/status/{tweet.get('id', '')}",
        "author": f"@{username}",
        "text": text,
        "extracted_links": resolved,
        "tags": tags,
        "relevance_tier": tier,
        "relevance_score": score,
        "likes": tweet.get("likeCount", 0),
        "retweets": tweet.get("retweetCount", 0),
        "synced_at": date_str,
    }

    if web_content:
        entry["web_content"] = {
            "title": web_content.get("title", ""),
            "description": web_content.get("description", ""),
            "content_preview": web_content.get("content_preview", "")[:1000],
        }

    return entry


def main():
    parser = argparse.ArgumentParser(
        description="Brandmint — Weekly Twitter + Web Sync for References Pool"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pull and score tweets but don't write any files",
    )
    parser.add_argument(
        "--sources",
        default="bookmarks,search,accounts",
        help="Comma-separated sources: bookmarks,search,accounts (default: all)",
    )
    parser.add_argument(
        "--min-likes",
        type=int,
        default=None,
        help="Override minimum likes threshold for all tiers",
    )
    parser.add_argument(
        "--no-web",
        action="store_true",
        help="Skip web content fetching (Layer 2)",
    )
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",")]
    date_str = datetime.now().strftime("%Y-%m-%d")

    print()
    print("BRANDMINT — Twitter + Web Sync")
    print("=" * 50)
    print(f"  Date: {date_str}")
    print(f"  Sources: {', '.join(sources)}")
    print(f"  Dry run: {args.dry_run}")
    print(f"  Web fetch: {not args.no_web}")
    print()

    # Load state for dedup
    state = load_state()
    seen_ids = set(state.get("seen_tweet_ids", []))

    # ── LAYER 1: TWITTER DISCOVERY ──
    print("── Layer 1: Twitter Discovery ──")
    all_raw = []
    source_counts = {"_total_raw": 0}

    if "bookmarks" in sources:
        tweets = pull_bookmarks(50)
        source_counts["bookmarks"] = len(tweets)
        source_counts["_total_raw"] += len(tweets)
        all_raw.extend(tweets)

    if "search" in sources:
        for key, query in SEARCH_QUERIES.items():
            tweets = pull_search(query, 20)
            source_counts[f"search_{key}"] = len(tweets)
            source_counts["_total_raw"] += len(tweets)
            all_raw.extend(tweets)

    if "accounts" in sources:
        for handle in TRACKED_ACCOUNTS:
            tweets = pull_account(handle, 10)
            source_counts[f"account_{handle}"] = len(tweets)
            source_counts["_total_raw"] += len(tweets)
            all_raw.extend(tweets)

    # Dedup
    all_tweets = dedup_tweets(all_raw)
    print(f"\n  Raw: {source_counts['_total_raw']} → Deduped: {len(all_tweets)}")

    # Filter out already-seen tweets
    new_tweets = [t for t in all_tweets if t.get("id") not in seen_ids]
    print(f"  New (unseen): {len(new_tweets)}")

    # Score relevance
    scored = []
    for tweet in new_tweets:
        tier, score = score_relevance(tweet, min_likes_override=args.min_likes)
        if tier > 0:
            scored.append((tweet, tier, score))

    scored.sort(key=lambda x: (-x[1], -x[2]))  # Tier 1 first, then by score
    print(f"  After filter: {len(scored)} relevant tweets")
    print(f"    Tier 1 (high signal): {sum(1 for _, t, _ in scored if t == 1)}")
    print(f"    Tier 2 (moderate): {sum(1 for _, t, _ in scored if t == 2)}")
    print()

    # ── LAYER 2: WEB CONTENT EXTRACTION ──
    web_contents = {}
    if not args.no_web and not args.dry_run and scored:
        print("── Layer 2: Web Content Extraction ──")
        fetch_counter = [0]
        for tweet, tier, score in scored:
            text = tweet.get("text", "")
            urls = extract_urls(text)
            for url in urls:
                resolved = resolve_tco_url(url)
                if resolved not in web_contents and is_allowed_domain(resolved):
                    content = fetch_page(resolved, fetch_counter)
                    if content:
                        web_contents[resolved] = content
                if fetch_counter[0] >= WEB_FETCH_MAX_PER_RUN:
                    break
            if fetch_counter[0] >= WEB_FETCH_MAX_PER_RUN:
                break
        print(f"  Fetched {fetch_counter[0]} web pages ({len(web_contents)} with content)")
        print()

    # ── LAYER 3: SAVE ──
    if args.dry_run:
        print("── Dry Run Summary ──")
        print(f"  Would write sync archive: sync-{date_str}.json ({len(all_tweets)} tweets)")
        print(f"  Would update curated.json (+{len(scored)} entries)")
        t1_count = sum(1 for _, t, _ in scored if t == 1)
        print(f"  Would append to learnings.md: {t1_count} high-signal entries")
        print(f"  Would update state.json (+{len(new_tweets)} seen IDs)")

        # Print top scored tweets for preview
        if scored:
            print("\n  Top scored tweets:")
            for tweet, tier, score in scored[:10]:
                author = tweet.get("author", {})
                username = author.get("username", "?") if isinstance(author, dict) else "?"
                text = (tweet.get("text", "")[:100] + "...") if len(tweet.get("text", "")) > 100 else tweet.get("text", "")
                likes = tweet.get("likeCount", 0)
                print(f"    T{tier} [{score:.2f}] @{username} ({likes} likes): {text}")

        print()
        print("  (No files written — dry run)")
        return 0

    print("── Layer 3: Save ──")

    # Build curated entries
    curated_entries = []
    for tweet, tier, score in scored:
        entry = build_curated_entry(tweet, tier, score, web_contents, date_str)
        curated_entries.append(entry)

    # Save archive
    save_sync_archive(all_tweets, curated_entries, date_str, source_counts)

    # Update curated.json
    curated = load_curated()
    update_curated(curated, curated_entries, date_str)

    # Update learnings.md for Tier 1 entries with extractable insights
    high_signal = [e for e in curated_entries
                   if e["relevance_tier"] == 1
                   and (e.get("extracted_links") or e.get("web_content"))]
    update_learnings(high_signal)

    # Update state
    new_seen = [t.get("id") for t in new_tweets if t.get("id")]
    state["seen_tweet_ids"] = list(set(state.get("seen_tweet_ids", [])) | set(new_seen))
    # Cap seen IDs to last 10000 to prevent unbounded growth
    if len(state["seen_tweet_ids"]) > 10000:
        state["seen_tweet_ids"] = state["seen_tweet_ids"][-10000:]
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print(f"  State: {len(state['seen_tweet_ids'])} seen IDs tracked")

    print()
    print("=" * 50)
    print(f"  Sync complete: {date_str}")
    print(f"  Tweets: {len(all_tweets)} pulled, {len(scored)} curated")
    print(f"  Web pages: {len(web_contents)} fetched")
    print(f"  Learnings: {len(high_signal)} appended")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
