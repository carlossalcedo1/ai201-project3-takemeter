"""
TakeMeter data collection script.

Pulls r/nba submissions and comments matching GOAT-debate search terms
using the pullpush.io API (a third-party historical Reddit archive that
does NOT require Reddit OAuth credentials, unlike PRAW).

Output: a CSV with columns: text, label, source, search_term, score, url
- `text` and `label` are your two required columns (label starts blank).
- The extra columns are just for your own traceability / debugging and
  won't interfere with anything that only reads text/label.

Usage:
    pip install requests
    python collect_goat_debate_data.py
"""

import csv
import time
import requests

# ---------------------------------------------------------------------------
# CONFIG — tweak these
# ---------------------------------------------------------------------------

SUBREDDIT = "nba"

SEARCH_TERMS = [
    "GOAT debate",
    "MJ vs LeBron",
    "Jordan vs LeBron",
    "Kobe vs LeBron",
    "is LeBron overrated",
    "top 10 all time",
    "Magic vs Bird",
    "Jordan rings argument",
]

# How many submissions AND how many comments to try to pull PER search term.
# 8 terms x (15 submissions + 15 comments) = up to 240 raw rows before dedup.
RESULTS_PER_TERM = 15

OUTPUT_CSV = "goat_debate_raw.csv"

BASE_SUBMISSION_URL = "https://api.pullpush.io/reddit/search/submission/"
BASE_COMMENT_URL = "https://api.pullpush.io/reddit/search/comment/"

# Be polite to the free API — small delay between requests.
REQUEST_DELAY_SECONDS = 1.5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_submissions(query, subreddit, size):
    """Fetch submissions (posts) matching a search query."""
    params = {
        "q": query,
        "subreddit": subreddit,
        "size": size,
        "sort": "desc",
        "sort_type": "score",
    }
    resp = requests.get(BASE_SUBMISSION_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json().get("data", [])


def fetch_comments(query, subreddit, size):
    """Fetch comments matching a search query."""
    params = {
        "q": query,
        "subreddit": subreddit,
        "size": size,
        "sort": "desc",
        "sort_type": "score",
    }
    resp = requests.get(BASE_COMMENT_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json().get("data", [])


def clean_text(text):
    """Collapse weird whitespace so each row stays on one logical CSV row."""
    if not text:
        return ""
    return " ".join(text.split())


def build_url(permalink):
    if permalink and permalink.startswith("/"):
        return f"https://reddit.com{permalink}"
    return permalink or ""


# ---------------------------------------------------------------------------
# Main collection loop
# ---------------------------------------------------------------------------

def main():
    rows = []
    seen_ids = set()  # avoid duplicate rows when search terms overlap

    for term in SEARCH_TERMS:
        print(f"Searching submissions for: {term!r}")
        try:
            submissions = fetch_submissions(term, SUBREDDIT, RESULTS_PER_TERM)
        except requests.RequestException as e:
            print(f"  submission search failed for {term!r}: {e}")
            submissions = []

        for sub in submissions:
            sub_id = sub.get("id")
            if not sub_id or sub_id in seen_ids:
                continue
            seen_ids.add(sub_id)

            title = clean_text(sub.get("title", ""))
            selftext = clean_text(sub.get("selftext", ""))
            # Combine title + body since GOAT-debate posts often put the
            # real argument in the title and elaborate in the body.
            full_text = f"{title} {selftext}".strip()

            # Skip removed/deleted or empty posts — useless for annotation.
            if not full_text or full_text.lower() in ("[removed]", "[deleted]"):
                continue

            rows.append({
                "text": full_text,
                "label": "",  # fill in during annotation
                "source": "submission",
                "search_term": term,
                "score": sub.get("score", ""),
                "url": build_url(sub.get("permalink", "")),
            })

        time.sleep(REQUEST_DELAY_SECONDS)

        print(f"Searching comments for: {term!r}")
        try:
            comments = fetch_comments(term, SUBREDDIT, RESULTS_PER_TERM)
        except requests.RequestException as e:
            print(f"  comment search failed for {term!r}: {e}")
            comments = []

        for com in comments:
            com_id = com.get("id")
            if not com_id or com_id in seen_ids:
                continue
            seen_ids.add(com_id)

            body = clean_text(com.get("body", ""))
            if not body or body.lower() in ("[removed]", "[deleted]"):
                continue

            rows.append({
                "text": body,
                "label": "",
                "source": "comment",
                "search_term": term,
                "score": com.get("score", ""),
                "url": build_url(com.get("permalink", "")),
            })

        time.sleep(REQUEST_DELAY_SECONDS)

    # Write CSV
    fieldnames = ["text", "label", "source", "search_term", "score", "url"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Wrote {len(rows)} rows to {OUTPUT_CSV}")
    print("Note: this is RAW data — you still need to:")
    print("  1. Skim through and remove off-topic / junk rows")
    print("  2. De-duplicate near-identical text if needed")
    print("  3. Fill in the 'label' column (manually or via your AI pre-labeling step)")


if __name__ == "__main__":
    main()
