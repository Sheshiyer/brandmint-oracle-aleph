#!/usr/bin/env python3
"""
download_tweet_assets.py — Download images + extract prompts from high-signal tweets.

Pulls tweets via bird CLI (reusing twitter_sync.py functions), downloads images from
tweet media URLs, extracts prompt text, and saves with linked naming convention:

    ref-tw-{NNN}-{author}-{slug}[-N].jpg       # image(s)
    ref-tw-{NNN}-{author}-{slug}.prompt.md      # paired prompt
    manifest.json                                # full index

Usage:
    python3 scripts/download_tweet_assets.py
    python3 scripts/download_tweet_assets.py --dry-run
    python3 scripts/download_tweet_assets.py --sources bookmarks --min-likes 200
    python3 scripts/download_tweet_assets.py --force

Dependencies: Python stdlib only (no pip install required).
Requires: bird CLI v0.8.0+ at /opt/homebrew/bin/bird
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Import shared functions from twitter_sync
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from twitter_sync import (
    run_bird, pull_bookmarks, pull_search, pull_account,
    dedup_tweets, score_relevance, extract_urls,
    SEARCH_QUERIES, TRACKED_ACCOUNTS, TRACKED_ACCOUNT_OVERRIDES,
)

# =====================================================================
# CONFIGURATION
# =====================================================================

ASSETS_DIR = os.path.join(os.path.dirname(SCRIPTS_DIR),
                          "references", "twitter-sync", "assets")
IMAGES_DIR = os.path.join(os.path.dirname(SCRIPTS_DIR),
                          "references", "images")
MANIFEST_PATH = os.path.join(ASSETS_DIR, "manifest.json")

DOWNLOAD_DELAY_SECS = 1
DOWNLOAD_TIMEOUT_SECS = 15

# Tag map for auto-tagging (same as twitter_sync but tuned for image/prompt context)
TAG_MAP = {
    "image-gen": ["image generation", "text to image", "ai image", "generate image"],
    "flux": ["flux"],
    "midjourney": ["midjourney"],
    "recraft": ["recraft"],
    "nano-banana": ["nano banana"],
    "dalle": ["dall-e", "dalle"],
    "brand-design": ["brand identity", "brand design", "branding"],
    "prompt-library": ["prompt library", "prompt collection", "prompt database"],
    "claude": ["claude", "anthropic"],
    "workflow": ["workflow", "automation", "pipeline"],
    "typography": ["typography", "font", "typeface"],
    "color-palette": ["color palette", "colour palette", "colors"],
    "logo": ["logo"],
    "packaging": ["packaging", "unboxing"],
}

# Patterns to strip from tweet text when generating slugs
SLUG_STRIP_RE = re.compile(
    r"https?://\S+|@\w+|#\w+|[^\w\s-]",
    re.UNICODE,
)


# =====================================================================
# SLUG GENERATION
# =====================================================================

def generate_slug(text, max_len=30):
    """Auto-generate a URL-safe slug from tweet text.

    Strips URLs, @mentions, #hashtags, emojis, and punctuation.
    Takes first 3-5 meaningful words, lowercased and hyphenated.
    """
    if not text:
        return "untitled"

    # Strip URLs, mentions, hashtags, non-word chars
    cleaned = SLUG_STRIP_RE.sub(" ", text.lower())

    # Collapse whitespace and split into words
    words = cleaned.split()

    # Filter out very short words (a, an, the, is, it, to, etc.)
    stop_words = {"a", "an", "the", "is", "it", "to", "in", "of", "and", "or",
                  "for", "on", "at", "by", "with", "this", "that", "my", "your",
                  "i", "you", "we", "he", "she", "rt", "via"}
    meaningful = [w for w in words if w not in stop_words and len(w) > 1]

    if not meaningful:
        # Fall back to first words if all were stop words
        meaningful = [w for w in words if len(w) > 1]

    if not meaningful:
        return "untitled"

    # Take first 3-5 words that fit within max_len
    slug_parts = []
    current_len = 0
    for word in meaningful[:5]:
        # Truncate individual words longer than 15 chars
        word = word[:15]
        needed = len(word) + (1 if slug_parts else 0)  # +1 for hyphen
        if current_len + needed > max_len:
            break
        slug_parts.append(word)
        current_len += needed

    slug = "-".join(slug_parts) if slug_parts else "untitled"

    # Clean any remaining non-alphanumeric chars (except hyphens)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")

    return slug or "untitled"


# =====================================================================
# IMAGE DOWNLOAD
# =====================================================================

def download_image(url, dest_path, timeout=DOWNLOAD_TIMEOUT_SECS):
    """Download an image from a URL to a local file.

    Returns True on success, False on failure.
    """
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BrandmintSync/1.0",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()

        if len(data) < 100:
            print(f"    WARN: Suspiciously small image ({len(data)} bytes): {url[:60]}", file=sys.stderr)
            return False

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)

        return True

    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        print(f"    WARN: Failed to download {url[:60]}: {e}", file=sys.stderr)
        return False


# =====================================================================
# PROMPT FILE WRITER
# =====================================================================

def write_prompt_file(path, tweet, images_info, seq, slug, author_handle):
    """Write a .prompt.md file with metadata, prompt text, and image links."""
    text = tweet.get("text", "")
    author = tweet.get("author", {})
    display_name = author.get("displayName", author_handle) if isinstance(author, dict) else author_handle
    likes = tweet.get("likeCount", 0) or 0
    rts = tweet.get("retweetCount", 0) or 0
    tweet_id = tweet.get("id", "")

    # Auto-title from first line
    first_line = text.split("\n")[0].strip()
    if len(first_line) > 80:
        title = first_line[:77] + "..."
    else:
        title = first_line or f"Tweet by @{author_handle}"

    # Auto-tags
    text_lower = text.lower()
    tags = []
    for tag, keywords in TAG_MAP.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)

    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# {title}",
        "",
        f"**Source:** https://x.com/{author_handle}/status/{tweet_id}",
        f"**Author:** @{author_handle} ({display_name})",
        f"**Likes:** {likes} | **RTs:** {rts}",
        f"**Tags:** {', '.join(tags) if tags else 'untagged'}",
        f"**Synced:** {date_str}",
        "",
        "## Prompt",
        "",
        text,
        "",
    ]

    if images_info:
        lines.append("## Images")
        lines.append("")
        for img in images_info:
            w = img.get("width", "?")
            h = img.get("height", "?")
            lines.append(f"- `{img['file']}` ({w}x{h})")
        lines.append("")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))


# =====================================================================
# MANIFEST
# =====================================================================

def load_manifest():
    """Load existing manifest.json or return empty structure."""
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"generated_at": None, "total_assets": 0, "entries": []}


def save_manifest(manifest):
    """Write manifest.json to disk."""
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["total_assets"] = len(manifest["entries"])

    os.makedirs(ASSETS_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def auto_tags(text):
    """Generate auto-tags from tweet text."""
    text_lower = text.lower()
    tags = []
    for tag, keywords in TAG_MAP.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    return tags


# =====================================================================
# MAIN ORCHESTRATION
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Brandmint — Download tweet images + prompts with linked naming"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without writing files",
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
        help="Override minimum likes threshold for filtering",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if tweet already exists in manifest",
    )
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",")]
    date_str = datetime.now().strftime("%Y-%m-%d")

    print()
    print("BRANDMINT — Tweet Asset Downloader")
    print("=" * 50)
    print(f"  Date: {date_str}")
    print(f"  Sources: {', '.join(sources)}")
    print(f"  Dry run: {args.dry_run}")
    print(f"  Force: {args.force}")
    print()

    # ── PULL TWEETS ──
    print("── Pulling tweets ──")
    all_raw = []

    if "bookmarks" in sources:
        all_raw.extend(pull_bookmarks(50))

    if "search" in sources:
        for key, query in SEARCH_QUERIES.items():
            all_raw.extend(pull_search(query, 20))

    if "accounts" in sources:
        for handle in TRACKED_ACCOUNTS:
            overrides = TRACKED_ACCOUNT_OVERRIDES.get(handle, {})
            count = overrides.get("count", 10)
            all_raw.extend(pull_account(handle, count))

    # Dedup and score
    all_tweets = dedup_tweets(all_raw)
    print(f"\n  Raw: {len(all_raw)} → Deduped: {len(all_tweets)}")

    scored = []
    for tweet in all_tweets:
        # Apply per-account min_likes for tracked accounts
        effective_min_likes = args.min_likes  # CLI override takes precedence
        if effective_min_likes is None:
            author = tweet.get("author", {})
            username = author.get("username", "") if isinstance(author, dict) else ""
            acct_overrides = TRACKED_ACCOUNT_OVERRIDES.get(username, {})
            if "min_likes" in acct_overrides:
                effective_min_likes = acct_overrides["min_likes"]
        tier, score = score_relevance(tweet, min_likes_override=effective_min_likes)
        if tier == 1:  # Only Tier 1 for asset downloads
            scored.append((tweet, tier, score))

    # Sort by score descending (highest signal first)
    scored.sort(key=lambda x: -x[2])
    print(f"  Tier 1 (high signal): {len(scored)} tweets")

    # Count tweets with media
    with_media = sum(1 for t, _, _ in scored
                     if any(m.get("type") == "photo"
                            for m in (t.get("media") or [])))
    print(f"  With photo media: {with_media}")
    print()

    # ── LOAD EXISTING MANIFEST ──
    manifest = load_manifest()
    existing_ids = set()
    if not args.force:
        existing_ids = {e["tweet_id"] for e in manifest.get("entries", [])}
        if existing_ids:
            print(f"  Existing manifest: {len(existing_ids)} tweets already downloaded")

    # Filter out already-downloaded
    to_process = [(t, tier, score) for t, tier, score in scored
                  if t.get("id") not in existing_ids]
    print(f"  New to download: {len(to_process)}")
    print()

    if not to_process:
        print("  Nothing new to download. Use --force to re-download.")
        return 0

    # ── DRY RUN ──
    if args.dry_run:
        print("── Dry Run Preview ──")
        # Determine starting sequence number
        if manifest["entries"]:
            next_seq = max(e["seq"] for e in manifest["entries"]) + 1
        else:
            next_seq = 1

        for i, (tweet, tier, score) in enumerate(to_process):
            seq = next_seq + i
            author = tweet.get("author", {})
            username = (author.get("username", "unknown") if isinstance(author, dict)
                        else "unknown")[:20]
            text = tweet.get("text", "")
            slug = generate_slug(text)
            media = [m for m in (tweet.get("media") or []) if m.get("type") == "photo"]
            likes = tweet.get("likeCount", 0) or 0

            base = f"ref-tw-{seq:03d}-{username}-{slug}"
            print(f"  [{seq:03d}] @{username} ({likes} likes, score={score:.2f})")
            print(f"         {text[:80]}{'...' if len(text) > 80 else ''}")
            if media:
                for j, m in enumerate(media):
                    suffix = f"-{j + 1}" if j > 0 else ""
                    print(f"         -> {base}{suffix}.jpg ({m.get('width', '?')}x{m.get('height', '?')})")
            print(f"         -> {base}.prompt.md")
            print()

        total_images = sum(
            len([m for m in (t.get("media") or []) if m.get("type") == "photo"])
            for t, _, _ in to_process
        )
        print(f"  Summary: {len(to_process)} tweets, {total_images} images to download")
        print("  (No files written — dry run)")
        return 0

    # ── DOWNLOAD + SAVE ──
    print("── Downloading assets ──")
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # Determine starting sequence number
    if manifest["entries"]:
        next_seq = max(e["seq"] for e in manifest["entries"]) + 1
    else:
        next_seq = 1

    new_entries = []
    download_count = 0
    skip_count = 0

    for i, (tweet, tier, score) in enumerate(to_process):
        seq = next_seq + i
        author = tweet.get("author", {})
        username = (author.get("username", "unknown") if isinstance(author, dict)
                    else "unknown")[:20]
        text = tweet.get("text", "")
        slug = generate_slug(text)
        tweet_id = tweet.get("id", "")
        likes = tweet.get("likeCount", 0) or 0

        base = f"ref-tw-{seq:03d}-{username}-{slug}"
        print(f"\n  [{seq:03d}] @{username} — {slug}")

        # Download images
        media = [m for m in (tweet.get("media") or []) if m.get("type") == "photo"]
        images_info = []

        for j, m in enumerate(media):
            url = m.get("url", "")
            if not url:
                continue

            suffix = f"-{j + 1}" if j > 0 else ""
            # Determine extension from URL or default to jpg
            ext = "jpg"
            if ".png" in url.lower():
                ext = "png"
            filename = f"{base}{suffix}.{ext}"
            dest = os.path.join(ASSETS_DIR, filename)

            # Rate limit between downloads
            if download_count > 0:
                time.sleep(DOWNLOAD_DELAY_SECS)

            print(f"    Downloading: {filename}")
            if download_image(url, dest):
                download_count += 1
                images_info.append({
                    "file": filename,
                    "url": url,
                    "width": m.get("width"),
                    "height": m.get("height"),
                })
                # Copy to consolidated references/images/ dir
                os.makedirs(IMAGES_DIR, exist_ok=True)
                shutil.copy2(dest, os.path.join(IMAGES_DIR, filename))
            else:
                skip_count += 1

        # Write prompt file
        prompt_filename = f"{base}.prompt.md"
        prompt_path = os.path.join(ASSETS_DIR, prompt_filename)
        write_prompt_file(prompt_path, tweet, images_info, seq, slug, username)
        print(f"    Wrote: {prompt_filename}")

        # Build manifest entry
        entry = {
            "seq": seq,
            "tweet_id": tweet_id,
            "author": username,
            "slug": slug,
            "relevance_score": score,
            "likes": likes,
            "prompt_file": prompt_filename,
            "images": images_info,
            "tags": auto_tags(text),
        }
        new_entries.append(entry)

    # ── UPDATE MANIFEST ──
    if args.force:
        # Replace entries for re-downloaded tweets
        existing_tweet_ids = {e["tweet_id"] for e in new_entries}
        manifest["entries"] = [e for e in manifest["entries"]
                               if e["tweet_id"] not in existing_tweet_ids]

    manifest["entries"].extend(new_entries)
    # Re-sort by seq
    manifest["entries"].sort(key=lambda e: e["seq"])
    save_manifest(manifest)

    # ── SUMMARY ──
    print()
    print("=" * 50)
    print(f"  Complete: {date_str}")
    print(f"  New tweets processed: {len(new_entries)}")
    print(f"  Images downloaded: {download_count}")
    print(f"  Images failed: {skip_count}")
    print(f"  Prompt files written: {len(new_entries)}")
    print(f"  Manifest entries: {len(manifest['entries'])} total")
    print(f"  Assets dir: {ASSETS_DIR}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
