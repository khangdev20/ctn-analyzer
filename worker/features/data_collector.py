import json
import os
import time
from datetime import datetime, timezone
import twooter.sdk
import pandas as pd


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


def clean_post(post):
    """Clean and extract relevant fields from a post."""
    keep = {
        "id": post.get("id"),
        "author": {
            "id": post["author"].get("id"),
            "display_name": post["author"]["display_name"],
            "username": post["author"]["username"],
            "follower_count": post["author"]["follower_count"],
            "verified": post["author"]["verified"]
        },
        "content": post["content"],
        "created_at": post["created_at"],
        "like_count": post["like_count"],
        "reply_count": post["reply_count"],
        "repost_count": post["repost_count"],
        "tags": [t["name"] for t in post.get("tags", [])],
        "embed": post.get("embed")
    }
    return keep


def _print_sdk_error(prefix: str, err: Exception):
    """Print a helpful message for any SDK error."""
    print(f"{prefix}: {type(err).__name__}: {err}")
    # Print additional SDK error details if available
    if hasattr(err, 'details'):
        print(f"  -> SDK Error Details: {err.details}")
    elif hasattr(err, 'message'):
        print(f"  -> SDK Error Message: {err.message}")


def _safe_get_feed(key: str = 'trending', cursor: str = None):
    """
    Use twooter SDK to get feed data and return parsed dict, or None on any error.
    Errors are printed but not raised.
    """
    try:
        t = twooter.sdk.new()

        # Set cursor if provided
        if cursor:
            result = t.feed(key=key, cursor=cursor)
        else:
            result = t.feed(key=key)

        # The SDK should return a dict-like object with data and paging info
        return result

    except Exception as e:
        # Catch-all to prevent the loop from crashing on unexpected issues
        _print_sdk_error("SDK feed request failed", e)
        return None


def fetch_pages(num_pages, key='trending'):
    """Fetch specified number of pages using twooter SDK. Returns list (possibly empty)."""
    combined = []
    next_cursor = None

    for page_num in range(1, num_pages + 1):
        print(f"Stage {page_num}: Fetching page {page_num}...")

        # Make SDK request
        page_data = _safe_get_feed(key=key, cursor=next_cursor)
        if not page_data:
            print(
                f"Stage {page_num}: Failed to fetch page {page_num}. Stopping here.")
            break

        # Add data to combined list
        page_items = page_data.get("data", [])
        combined.extend(page_items)
        print(
            f"Stage {page_num}: Got {len(page_items)} items from page {page_num}")

        # Get next cursor for next iteration
        next_cursor = (page_data.get("paging") or {}).get("next_cursor")
        if not next_cursor:
            print(
                f"Stage {page_num}: No next_cursor found, reached end of data.")
            break

    print(
        f"Final: Collected {len(combined)} total items from {min(page_num, num_pages)} pages.")
    return combined


def generate_filename(key="trending"):
    """Generate filename with current timestamp."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return f"{key}_data_{timestamp}.json"


def save_data_to_file(filename, items):
    """Save items to specified file after cleaning the data."""
    # Clean the data before saving
    cleaned_items = []
    for item in items:
        try:
            cleaned_item = clean_post(item)
            cleaned_items.append(cleaned_item)
        except (KeyError, TypeError) as e:
            print(f"Warning: Failed to clean item, skipping: {e}")
            continue

    payload = {
        "data": cleaned_items,
        "total_items": len(cleaned_items),
        "collected_at": _iso_now(),
        "pages_fetched": "multiple",
        "original_items_count": len(items),
        "cleaned_items_count": len(cleaned_items)
    }

    print(f"Cleaned {len(cleaned_items)} out of {len(items)} items")

    try:
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(
            f"SUCCESS: Saved {len(cleaned_items)} cleaned items to {filename}")
        return True
    except OSError as e:
        print(f"ERROR: Failed to save data to {filename}: {e}")
        return False


def collect_trending_data(num_pages, key='trending'):
    """Main function to collect trending data using twooter SDK."""
    print("=" * 60)
    print(
        f"Starting data collection for {num_pages} pages using feed key '{key}'...")

    # Fetch data
    items = fetch_pages(num_pages, key=key)

    if not items:
        print("No data collected. Exiting.")
        return None

    # Generate filename with current timestamp
    filename = generate_filename(key=key)

    # Save data
    if save_data_to_file(filename, items):
        return filename
    else:
        return None
