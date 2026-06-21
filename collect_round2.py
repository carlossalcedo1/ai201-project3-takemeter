"""
TakeMeter data collection — ROUND 2.

Bumps results-per-term from 15 to 20, and swaps in additional / different
search terms to widen coverage beyond the original 8 (more breadth instead
of digging deeper into the same searches, which tends to pull in lower
quality / off-topic matches).

Writes to a SEPARATE CSV (goat_debate_round2.csv) so you can review it on
its own before merging with your existing cleaned file. Includes retry
logic since pullpush.io has been flaky on some comment searches.

Usage:
    python collect_round2.py
"""

import csv
import os
import time
import requests

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

SUBREDDIT = "nba"

# Original 8 terms minus the ones we're swapping out, plus new ones.
# Kept: GOAT debate, MJ vs LeBron, Jordan vs LeBron, Kobe vs LeBron,
#       Jordan rings argument (these worked fine and are core to the topic)
# Swapped out: "is LeBron overrated" / "top 10 all time" / "Magic vs Bird"
#   already covered by the retry script — not repeating here to avoid dupes
# New terms added for breadth:
SEARCH_TERMS = [
    "GOAT debate",
    "MJ vs LeBron",
    "Jordan vs LeBron",
    "Kobe vs LeBron",
    "Jordan rings argument",
    "Bill Russell GOAT",
    "Wilt Chamberlain greatest",
    "LeBron stats vs rings",
    "Kareem vs LeBron",
    "Jordan vs Kobe",
    "LeBron legacy",
    "Jordan greatest ever",
]

RESULTS_PER_TERM = 20

OUTPUT_CSV = os.path.expanduser("~/goat_debate_round2.csv")

BASE_SUBMISSION_URL = "https://api.pullpush.io/reddit/search/submission/"
BASE_COMMENT_URL = "https://api.pullpush.io/reddit/search/comment/"

REQUEST_DELAY_SECONDS = 2
MAX_RETRIES_PER_REQUEST = 3
RETRY_BACKOFF_SECONDS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_with_retry(url, params, max_retries=MAX_RETRIES_PER_REQUEST):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get("data", [])
        except requests.RequestException as e:
            last_error = e
            print(f"    attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(RETRY_BACKOFF_SECONDS)
    print(f"    giving up after {max_retries} attempts: {last_error}")
    return []


def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split())


def build_url(permalink):
    if permalink and permalink.startswith("/"):
        return f"https://reddit.com{permalink}"
    return permalink or ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rows = []
    seen_text = set()
    failed_terms = []

    for term in SEARCH_TERMS:
        print(f"\nSearching submissions for: {term!r}")
        params = {
            "q": term, "subreddit": SUBREDDIT, "size": RESULTS_PER_TERM,
            "sort": "desc", "sort_type": "score",
        }
        submissions = fetch_with_retry(BASE_SUBMISSION_URL, params)
        if not submissions:
            failed_terms.append(f"{term} (submissions)")

        for sub in submissions:
            title = clean_text(sub.get("title", ""))
            selftext = clean_text(sub.get("selftext", ""))
            full_text = f"{title} {selftext}".strip()
            full_text = full_text.replace("[removed]", "").replace("[deleted]", "").strip()

            if not full_text or full_text.lower() in seen_text:
                continue
            seen_text.add(full_text.lower())

            rows.append({
                "text": full_text, "label": "", "source": "submission",
                "search_term": term, "score": sub.get("score", ""),
                "url": build_url(sub.get("permalink", "")),
            })

        time.sleep(REQUEST_DELAY_SECONDS)

        print(f"Searching comments for: {term!r}")
        params = {
            "q": term, "subreddit": SUBREDDIT, "size": RESULTS_PER_TERM,
            "sort": "desc", "sort_type": "score",
        }
        comments = fetch_with_retry(BASE_COMMENT_URL, params)
        if not comments:
            failed_terms.append(f"{term} (comments)")

        for com in comments:
            body = clean_text(com.get("body", ""))
            body = body.replace("[removed]", "").replace("[deleted]", "").strip()

            if not body or body.lower() in seen_text:
                continue
            seen_text.add(body.lower())

            rows.append({
                "text": body, "label": "", "source": "comment",
                "search_term": term, "score": com.get("score", ""),
                "url": build_url(com.get("permalink", "")),
            })

        time.sleep(REQUEST_DELAY_SECONDS)

    fieldnames = ["text", "label", "source", "search_term", "score", "url"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Wrote {len(rows)} rows to {OUTPUT_CSV}")
    if failed_terms:
        print(f"\nThese searches failed even after retries: {failed_terms}")
        print("That's fine — you got volume from the terms that worked. Don't bother re-retrying these.")
    print("\nNext step: review/clean this file like before, then merge with your existing cleaned CSV.")


if __name__ == "__main__":
    main()
