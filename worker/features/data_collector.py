import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import twooter.sdk
import pandas as pd

# Import S3 storage for cloud persistence
from data_access.s3_store import S3Store


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


def _safe_get_feed(key: str = 'latest', cursor: str = None):
    """
    Use twooter SDK to get feed data and return parsed dict, or None on any error.
    Supports both 'trending' and 'latest' feed keys for different data collection strategies.
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


def fetch_pages(num_pages, key='latest'):
    """Fetch specified number of pages using twooter SDK. 
    Default to 'latest' posts for fresh content analysis.
    Also supports 'trending' for existing trending posts.
    Returns list (possibly empty)."""
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


def generate_filename(key="latest"):
    """Generate filename with current timestamp. Default to 'latest' for fresh posts."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return f"{key}_data_{timestamp}.json"


def save_data_to_file(filename, items):
    """Save items to both local file and S3 storage after cleaning the data."""
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

    # Save directly to S3 storage (cloud-only approach)
    s3_success = False
    try:
        s3_store = S3Store()

        # Create S3 key with timestamp structure: raw/YYYY/MM/DD/filename
        now = datetime.now(timezone.utc)
        s3_key = s3_store.build_key(
            "raw",
            f"{now.year}",
            f"{now.month:02d}",
            f"{now.day:02d}",
            filename
        )

        print(f"Uploading to S3: s3://{s3_store.bucket}/{s3_key}")

        # Upload to S3 with compression for efficiency
        result = s3_store.s3_write_json(
            key=s3_key,
            data=payload,
            compress=True,
            content_type="application/json"
        )

        if result.get('success'):
            print(f"SUCCESS: Uploaded to S3 - {result['s3_url']}")
            print(
                f"S3 Details: Size={result['size_bytes']} bytes, Compressed={result['compressed']}")
            s3_success = True
        else:
            print(
                f"ERROR: S3 upload failed - {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"ERROR: S3 upload exception - {e}")

    # Return success based on S3 upload only (cloud-only approach)
    if s3_success:
        return {'success': True, 's3': True, 's3_key': s3_key, 'storage': 'cloud_only'}
    else:
        return {'success': False, 's3': False, 'error': 'S3 upload failed', 'storage': 'failed'}


def load_data_from_s3(s3_key):
    """Load trending data from S3 storage."""
    try:
        s3_store = S3Store()
        print(f"Loading data from S3: s3://{s3_store.bucket}/{s3_key}")

        data = s3_store.s3_read_json(s3_key)

        if data:
            print(f"✅ Successfully loaded data from S3")
            print(f"📊 Items: {data.get('total_items', 'Unknown')}")
            return data
        else:
            print(f"❌ No data found at S3 key: {s3_key}")
            return None

    except Exception as e:
        print(f"ERROR: Failed to load from S3 - {e}")
        return None


def get_recent_data_from_s3(days_back=7, key='latest'):
    """Get list of recent data files from S3 within specified days. 
    Default to 'latest' posts for fresh content analysis."""
    try:
        s3_store = S3Store()

        # Build list of possible S3 keys for recent days
        recent_keys = []
        now = datetime.now(timezone.utc)

        for days_ago in range(days_back):
            target_date = now - pd.Timedelta(days=days_ago)
            date_prefix = s3_store.build_key(
                "raw",
                f"{target_date.year}",
                f"{target_date.month:02d}",
                f"{target_date.day:02d}"
            )

            # List objects with this prefix
            try:
                client = s3_store.get_s3_client()
                response = client.list_objects_v2(
                    Bucket=s3_store.bucket,
                    Prefix=date_prefix
                )

                if 'Contents' in response:
                    for obj in response['Contents']:
                        if obj['Key'].endswith('.json') and key in obj['Key']:
                            recent_keys.append({
                                'key': obj['Key'],
                                'last_modified': obj['LastModified'],
                                'size': obj['Size']
                            })
            except Exception as e:
                print(
                    f"Warning: Failed to list S3 objects for {date_prefix}: {e}")
                continue

        # Sort by last modified (most recent first)
        recent_keys.sort(key=lambda x: x['last_modified'], reverse=True)

        print(f"Found {len(recent_keys)} recent data files in S3")
        return recent_keys

    except Exception as e:
        print(f"ERROR: Failed to get recent S3 data - {e}")
        return []


def collect_trending_data(num_pages, key='latest'):
    """Main function to collect social media data using twooter SDK with S3 storage.
    Default to 'latest' posts for fresh content. Also supports 'trending' for existing trending posts."""
    print("=" * 60)
    print(
        f"Starting data collection for {num_pages} pages using feed key '{key}'...")
    print(
        f"Target: {'Fresh Latest Posts' if key == 'latest' else 'Existing Trending Posts'}")
    print(f"Storage: S3 cloud storage only (cloud-first architecture)")

    # Fetch data
    items = fetch_pages(num_pages, key=key)

    if not items:
        print("No data collected. Exiting.")
        return None

    # Generate filename with current timestamp
    filename = generate_filename(key=key)

    # Save data directly to S3 cloud storage
    save_result = save_data_to_file(filename, items)

    if isinstance(save_result, dict):
        if save_result.get('success'):
            print(f"✅ Data collection completed successfully!")
            print(
                f"☁️  S3 storage: {save_result.get('s3_key', 'Unknown key')}")
            return {
                's3_key': save_result.get('s3_key'),
                'storage': 'cloud_only',
                'items_count': len(items),
                'filename': filename  # Keep for reference but not saved locally
            }
        else:
            print("❌ S3 cloud storage failed")
            print(f"Error: {save_result.get('error', 'Unknown error')}")
            return None
    else:
        # Legacy fallback
        print("❌ Data save failed - cloud storage unavailable")
        return None


def collect_latest_posts(num_pages=3):
    """Convenience function to collect latest posts specifically for trending prediction."""
    print("🚀 [LATEST POSTS] Collecting fresh posts for trending prediction...")
    return collect_trending_data(num_pages=num_pages, key='latest')


def collect_existing_trending(num_pages=5):
    """Convenience function to collect existing trending posts for analysis."""
    print("📊 [TRENDING] Collecting existing trending posts for analysis...")
    return collect_trending_data(num_pages=num_pages, key='trending')
