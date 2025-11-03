"""
Leaderboard Logger Worker - Daily Competition Leaderboard Analysis
Fetches, analyzes, and reports daily leaderboard changes with Discord integration

Author: AI Assistant
Date: October 8, 2025
"""

from notifiers.discord_webhook_sender import send_discord_message_webhook
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pytz

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


def fetch_all_pages(api_url: str, timeout: int = 15, max_retries: int = 5, max_pages: int = 2) -> Tuple[List[Dict], str]:
    """
    Fetch limited pages from leaderboard API using pagination with enhanced retry logic

    Args:
        api_url: Base API URL for leaderboard
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts (increased default)
        max_pages: Maximum number of pages to fetch (default: 2)

    Returns:
        Tuple of (all_rows, status) where status is "complete", "partial", or "failed"
    """
    all_rows = []
    next_cursor = None
    page_count = 0
    status = "complete"
    consecutive_failures = 0
    max_consecutive_failures = 3

    # Setup requests session with enhanced retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=2,  # Exponential backoff: 2, 4, 8, 16 seconds
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False  # Don't raise exception, let us handle it
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        while True:
            page_count += 1
            logger.debug(f"Fetching page {page_count}")

            try:
                # Build request parameters
                params = {}
                if next_cursor:
                    params['cursor'] = next_cursor

                # Make API request with retry logic
                response = None  # Initialize response variable
                for attempt in range(max_retries + 1):
                    try:
                        logger.debug(f"Page {page_count}, attempt {attempt + 1}")
                        response = session.get(
                            api_url, params=params, timeout=timeout)

                        if response.status_code == 200:
                            # Success - reset consecutive failures counter
                            consecutive_failures = 0
                            break
                        elif response.status_code in [503, 502, 504]:
                            # Server errors - retry with exponential backoff
                            if attempt < max_retries:
                                # 1, 2.5, 5, 10.5 seconds
                                wait_time = (2 ** attempt) + (attempt * 0.5)
                                logger.warning(
                                    f"[RETRY] Status {response.status_code}, waiting {wait_time:.1f}s before retry...")
                                time.sleep(wait_time)
                                continue
                            else:
                                logger.error(
                                    f"[EXHAUSTED] Max retries reached for page {page_count}")
                                consecutive_failures += 1
                                break
                        else:
                            # Other HTTP errors - don't retry
                            logger.error(
                                f"[ERROR] API returned status {response.status_code}: {response.text}")
                            consecutive_failures += 1
                            break

                    except requests.exceptions.Timeout:
                        if attempt < max_retries:
                            wait_time = (2 ** attempt)
                            logger.warning(
                                f"[TIMEOUT] Request timeout, waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"[TIMEOUT] Request timeout after {max_retries + 1} attempts")
                            consecutive_failures += 1
                            break
                    except requests.exceptions.RequestException as req_e:
                        if attempt < max_retries:
                            wait_time = (2 ** attempt)
                            logger.warning(
                                f"[NETWORK] Request error: {req_e}, waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"[NETWORK] Request failed after {max_retries + 1} attempts: {req_e}")
                            consecutive_failures += 1
                            break

                # Check if we got a successful response
                if not response or response.status_code != 200:
                    logger.error(
                        f"[FAILED] Page {page_count} failed after all retries")
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(
                            f"[ABORT] Too many consecutive failures ({consecutive_failures}), aborting pagination")
                        status = "failed" if not all_rows else "partial"
                        break
                    if all_rows:  # Have some data from previous pages
                        status = "partial"
                        break
                    else:  # No data at all
                        status = "failed"
                        break

                # Parse successful response
                try:
                    data = response.json()
                except json.JSONDecodeError as json_e:
                    logger.error(f"[JSON] Failed to parse response: {json_e}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        status = "failed" if not all_rows else "partial"
                        break
                    continue

                # Extract rows
                page_rows = data.get('data', [])
                if not page_rows:
                    logger.warning(
                        f"[WARNING] Page {page_count} returned no data")
                    break

                all_rows.extend(page_rows)
                logger.debug(f"Page {page_count}: {len(page_rows)} rows")

                # Check pagination
                paging = data.get('paging', {})
                has_next = paging.get('has_next', False)
                next_cursor = paging.get('next_cursor')

                # Check if we've reached the page limit
                if page_count >= max_pages:
                    logger.info(f"Retrieved {len(all_rows)} leaderboard entries")
                    status = "partial" if has_next and next_cursor else "complete"
                    break

                if not has_next or not next_cursor:
                    logger.info(f"Leaderboard fetch complete: {len(all_rows)} entries")
                    break

            except Exception as e:
                logger.error(
                    f"[FATAL] Unexpected error on page {page_count}: {e}")
                if all_rows:  # Have some data from previous pages
                    status = "partial"
                    break
                else:  # No data at all
                    status = "failed"
                    break
            except Exception as e:
                logger.error(f"💥 Unexpected error on page {page_count}: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(
                        f"[ABORT] Too many consecutive failures ({consecutive_failures}), aborting")
                    status = "failed" if not all_rows else "partial"
                    break
                if all_rows:
                    status = "partial"
                    break
                else:
                    status = "failed"
                    break

            # Safety check - prevent infinite loops
            if page_count > 100:
                logger.warning(
                    "[WARNING] Reached page limit (100), stopping pagination")
                status = "partial"
                break

    except Exception as e:
        logger.error(f"💥 Fatal error during pagination: {e}")
        status = "failed" if not all_rows else "partial"
    finally:
        session.close()

    logger.info(
        f"[REPORT] Fetch complete: {len(all_rows)} total rows, status: {status}")
    return all_rows, status


def normalize_and_rank(rows: List[Dict]) -> List[Dict]:
    """
    Normalize data and assign ranks

    Args:
        rows: Raw API response data

    Returns:
        List of normalized and ranked entries
    """
    if not rows:
        return []

    normalized = []

    for row in rows:
        try:
            # Extract and validate required fields
            entry = {
                'id': int(row.get('id', 0)),
                'name': str(row.get('name', 'Unknown')),
                'affiliation': str(row.get('affiliation', '')),
                'score': float(row.get('score', 0.0)),
                'created_at': row.get('created_at', ''),
            }

            # Validate essential fields
            if entry['id'] <= 0:
                logger.warning(f"[WARNING] Invalid ID in row: {row}")
                continue

            if not entry['name'] or entry['name'] == 'Unknown':
                logger.warning(f"[WARNING] Missing name in row: {row}")
                entry['name'] = f"User_{entry['id']}"

            normalized.append(entry)

        except (ValueError, TypeError) as e:
            logger.warning(f"[WARNING] Failed to normalize row {row}: {e}")
            continue

    if not normalized:
        logger.error("[ERROR] No valid rows after normalization")
        return []

    # Sort by: score DESC, created_at ASC, id ASC
    normalized.sort(key=lambda x: (-x['score'], x['created_at'], x['id']))

    # Assign ranks
    for i, entry in enumerate(normalized, 1):
        entry['rank'] = i

    logger.debug(f"Normalized {len(normalized)} entries")
    return normalized


def compare_snapshots(today: List[Dict], yesterday: Optional[List[Dict]]) -> Dict:
    """
    Compare today's snapshot with yesterday's

    Args:
        today: Today's leaderboard entries  
        yesterday: Yesterday's entries (None for first run)

    Returns:
        Comparison results with leaders, movers, new entries, dropouts
    """
    if not today:
        logger.warning("[WARNING] No entries for today")
        return _empty_comparison()

    # If no yesterday data, return first-run format
    if not yesterday:
        logger.info("🆕 No yesterday data - first run mode")
        return _first_run_comparison(today)

    # Build lookup dict for yesterday by ID
    yesterday_by_id = {entry['id']: entry for entry in yesterday}

    # Calculate deltas and categorize changes
    leaders_top10 = []
    movers_up = []
    movers_down = []
    new_entries = []

    for today_entry in today:
        entry_id = today_entry['id']

        if entry_id not in yesterday_by_id:
            # New entry
            new_entries.append({
                'id': entry_id,
                'name': today_entry['name'],
                'rank': today_entry['rank'],
                'score': today_entry['score'],
                'affiliation': today_entry.get('affiliation', '')
            })
        else:
            # Existing entry - calculate deltas
            yesterday_entry = yesterday_by_id[entry_id]

            score_delta = today_entry['score'] - yesterday_entry['score']
            rank_delta = yesterday_entry['rank'] - \
                today_entry['rank']  # Positive = moved up

            entry_with_deltas = {
                'id': entry_id,
                'name': today_entry['name'],
                'rank': today_entry['rank'],
                'score': today_entry['score'],
                'affiliation': today_entry.get('affiliation', ''),
                'score_delta': score_delta,
                'rank_delta': rank_delta,
                'previous_rank': yesterday_entry['rank'],
                'previous_score': yesterday_entry['score'],
                # Keep for backward compatibility
                'yesterday_rank': yesterday_entry['rank'],
                'yesterday_score': yesterday_entry['score']
            }

            # Categorize by movement
            if rank_delta > 0:
                movers_up.append(entry_with_deltas)
            elif rank_delta < 0:
                movers_down.append(entry_with_deltas)

            # Add to leaders if in top 10
            if today_entry['rank'] <= 10:
                leaders_top10.append(entry_with_deltas)

    # Find dropouts (in yesterday but not today)
    today_ids = {entry['id'] for entry in today}
    dropouts = []

    for yesterday_entry in yesterday:
        if yesterday_entry['id'] not in today_ids:
            dropouts.append({
                'id': yesterday_entry['id'],
                'name': yesterday_entry['name'],
                'previous_rank': yesterday_entry['rank'],
                'previous_score': yesterday_entry['score'],
                # Keep for backward compatibility
                'yesterday_rank': yesterday_entry['rank'],
                'yesterday_score': yesterday_entry['score'],
                'affiliation': yesterday_entry.get('affiliation', '')
            })

    # Sort and limit lists
    # Top movers up: by rank_delta desc, then score_delta desc
    movers_up.sort(key=lambda x: (-x['rank_delta'], -x['score_delta']))
    movers_up = movers_up[:5]

    # Top movers down: by rank_delta asc (most negative), then score_delta asc
    movers_down.sort(key=lambda x: (x['rank_delta'], x['score_delta']))
    movers_down = movers_down[:5]

    # New entries: by rank (best rank first)
    new_entries.sort(key=lambda x: x['rank'])
    new_entries = new_entries[:5]

    # Dropouts: by previous rank (best former rank first)
    dropouts.sort(key=lambda x: x['previous_rank'])
    dropouts = dropouts[:5]

    # Leaders already in rank order
    leaders_top10 = leaders_top10[:10]

    logger.info(f"[ANALYTICS] Comparison complete: {len(leaders_top10)} leaders, "
                f"{len(movers_up)} up, {len(movers_down)} down, "
                f"{len(new_entries)} new, {len(dropouts)} dropouts")

    return {
        'leaders_top10': leaders_top10,
        'movers_up': movers_up,
        'movers_down': movers_down,
        'new_entries': new_entries,
        'dropouts': dropouts,
        'total_today': len(today),
        'total_previous': len(yesterday),
        'is_first_run': False
    }


def _first_run_comparison(today: List[Dict]) -> Dict:
    """Generate comparison for first run (no yesterday data)"""
    # Just show top 10 as leaders, no deltas
    leaders_top10 = []

    for entry in today[:10]:
        leaders_top10.append({
            'id': entry['id'],
            'name': entry['name'],
            'rank': entry['rank'],
            'score': entry['score'],
            'affiliation': entry.get('affiliation', ''),
            'score_delta': 0,
            'rank_delta': 0,
            'yesterday_rank': None,
            'yesterday_score': None
        })

    return {
        'leaders_top10': leaders_top10,
        'movers_up': [],
        'movers_down': [],
        'new_entries': [],
        'dropouts': [],
        'total_today': len(today),
        'total_previous': 0,
        'is_first_run': True
    }


def _empty_comparison() -> Dict:
    """Generate empty comparison structure"""
    return {
        'leaders_top10': [],
        'movers_up': [],
        'movers_down': [],
        'new_entries': [],
        'dropouts': [],
        'total_today': 0,
        'total_previous': 0,
        'is_first_run': False
    }


def format_bidaily_discord_message(timestamp: str, comp: Dict, source_status: str, time_context: str) -> str:
    """
    Format comparison results into Discord message for bi-daily reporting

    Args:
        timestamp: Current timestamp string (YYYY-MM-DD_HH-MM)
        comp: Results from compare_snapshots  
        source_status: "complete", "partial", "failed"
        time_context: "Morning Report (09:00 AEST)" or "Evening Report (21:00 AEST)"

    Returns:
        Formatted Discord message string (<= 2000 chars)
    """
    # Get current Brisbane time
    brisbane_tz = pytz.timezone('Australia/Brisbane')
    current_time = datetime.now(brisbane_tz).strftime('%H:%M AEST')

    lines = []

    # Title with bi-daily context
    status_emoji = "[OK]" if source_status == "complete" else "[WARNING]"
    lines.append(f"🏁 **{time_context} — Competition Update**")
    lines.append("")

    # Handle first run case
    if comp.get('is_first_run', False):
        lines.append("🆕 **First Run — No Previous Data Available**")
        lines.append("")

    # 1. Top 10 Leaders
    leaders = comp.get('leaders_top10', [])
    if leaders:
        lines.append("[FIRST_PLACE] **Top 10**")
        for leader in leaders:
            line = _format_leader_line(leader, comp.get('is_first_run', False))
            lines.append(line)
        lines.append("")

    # Only show movement sections if not first run
    if not comp.get('is_first_run', False):
        # 2. Top Movers Up (since last report)
        movers_up = comp.get('movers_up', [])
        if movers_up:
            lines.append("[TRENDING_UP] **Top Movers ↑ (since last report)**")
            for mover in movers_up:
                line = _format_mover_up_line(mover)
                lines.append(line)
            lines.append("")

        # 3. Top Movers Down (since last report)
        movers_down = comp.get('movers_down', [])
        if movers_down:
            lines.append(
                "[TRENDING_DOWN] **Top Movers ↓ (since last report)**")
            for mover in movers_down:
                line = _format_mover_down_line(mover)
                lines.append(line)
            lines.append("")

        # 4. New Entries
        new_entries = comp.get('new_entries', [])
        if new_entries:
            lines.append("[SPARKLE] **New Entries (since last report)**")
            for entry in new_entries:
                line = _format_new_entry_line(entry)
                lines.append(line)
            lines.append("")

        # 5. Dropouts
        dropouts = comp.get('dropouts', [])
        if dropouts:
            lines.append("📴 **Dropouts (since last report)**")
            for dropout in dropouts:
                line = _format_dropout_line(dropout)
                lines.append(line)
            lines.append("")

    # 6. Footer with metadata
    total_current = comp.get('total_today', 0)
    total_previous = comp.get('total_previous', 0)

    if comp.get('is_first_run', False):
        lines.append(f"[ANALYTICS] **Total Entries:** {total_current:,}")
    else:
        change = total_current - total_previous
        change_str = f"({change:+,})" if change != 0 else ""
        lines.append(
            f"[ANALYTICS] **Total Entries:** {total_current:,} {change_str}")

    lines.append(
        f"⏱ **Generated:** {current_time} | **Source:** {status_emoji}")

    # Return full message - rich embeds support longer content
    message = "\n".join(lines)
    return message


def format_discord_message(date_local: str, comp: Dict, source_status: str) -> str:
    """
    Format comparison results into Discord message

    Args:
        date_local: Local date string (YYYY-MM-DD)
        comp: Results from compare_snapshots
        source_status: "complete", "partial", "failed"

    Returns:
        Formatted Discord message string (<= 2000 chars)
    """
    # Get current Brisbane time
    brisbane_tz = pytz.timezone('Australia/Brisbane')
    current_time = datetime.now(brisbane_tz).strftime('%H:%M AEST')

    lines = []

    # Title
    status_emoji = "[OK]" if source_status == "complete" else "[WARNING]"
    lines.append(f"🏁 **Daily Leaderboard — {date_local} (AEST)**")
    lines.append("")

    # Handle first run case
    if comp.get('is_first_run', False):
        lines.append("🆕 **First Run — No Comparisons Available**")
        lines.append("")

    # 1. Top 10 Leaders
    leaders = comp.get('leaders_top10', [])
    if leaders:
        lines.append("[FIRST_PLACE] **Top 10**")
        for leader in leaders:
            line = _format_leader_line(leader, comp.get('is_first_run', False))
            lines.append(line)
        lines.append("")

    # Only show movement sections if not first run
    if not comp.get('is_first_run', False):
        # 2. Top Movers Up (since last report)
        movers_up = comp.get('movers_up', [])
        if movers_up:
            lines.append("[TRENDING_UP] **Top Movers ↑ (since last report)**")
            for mover in movers_up:
                line = _format_mover_up_line(mover)
                lines.append(line)
            lines.append("")

        # 3. Top Movers Down (since last report)
        movers_down = comp.get('movers_down', [])
        if movers_down:
            lines.append(
                "[TRENDING_DOWN] **Top Movers ↓ (since last report)**")
            for mover in movers_down:
                line = _format_mover_down_line(mover)
                lines.append(line)
            lines.append("")

        # 4. New Entries (since last report)
        new_entries = comp.get('new_entries', [])
        if new_entries:
            lines.append("[SPARKLE] **New Entries (since last report)**")
            for entry in new_entries:
                line = _format_new_entry_line(entry)
                lines.append(line)
            lines.append("")

        # 5. Dropouts (since last report)
        dropouts = comp.get('dropouts', [])
        if dropouts:
            lines.append("📴 **Dropouts (since last report)**")
            for dropout in dropouts:
                line = _format_dropout_line(dropout)
                lines.append(line)
            lines.append("")

    # 6. Footer with metadata
    total_today = comp.get('total_today', 0)
    total_previous = comp.get('total_previous', 0)

    if comp.get('is_first_run', False):
        lines.append(f"[ANALYTICS] **Total Entries:** {total_today:,}")
    else:
        change = total_today - total_previous
        change_str = f"({change:+,})" if change != 0 else ""
        lines.append(
            f"[ANALYTICS] **Total Entries:** {total_today:,} {change_str}")

    lines.append(
        f"⏱ **Generated:** {current_time} | **Source:** {status_emoji}")

    # Join lines - no truncation needed with rich embeds
    message = "\n".join(lines)
    return message


def _format_leader_line(leader: Dict, is_first_run: bool) -> str:
    """Format a leader line"""
    name = _truncate_name(leader['name'])
    rank = leader['rank']
    score = leader['score']

    if is_first_run:
        # No deltas for first run
        return f"#{rank} {name} — {_format_score(score)}"
    else:
        # Include deltas
        rank_delta = leader.get('rank_delta', 0)
        score_delta = leader.get('score_delta', 0)

        rank_change = _format_rank_delta(rank_delta)
        score_change = _format_score_delta(score_delta)

        return f"#{rank} {name} — {_format_score(score)} ({rank_change}, {score_change})"


def _format_mover_up_line(mover: Dict) -> str:
    """Format a mover up line"""
    name = _truncate_name(mover['name'])
    rank = mover['rank']
    rank_delta = mover['rank_delta']
    score_delta = mover['score_delta']

    return f"{name} (#{rank}) ↑{rank_delta} ({_format_score_delta(score_delta)})"


def _format_mover_down_line(mover: Dict) -> str:
    """Format a mover down line"""
    name = _truncate_name(mover['name'])
    rank = mover['rank']
    rank_delta = abs(mover['rank_delta'])  # Make positive for display
    score_delta = mover['score_delta']

    return f"{name} (#{rank}) ↓{rank_delta} ({_format_score_delta(score_delta)})"


def _format_new_entry_line(entry: Dict) -> str:
    """Format a new entry line"""
    name = _truncate_name(entry['name'])
    rank = entry['rank']
    score = entry['score']

    return f"{name} (#{rank}) — {_format_score(score)}"


def _format_dropout_line(dropout: Dict) -> str:
    """Format a dropout line"""
    name = _truncate_name(dropout['name'])
    previous_rank = dropout.get(
        'yesterday_rank', dropout.get('previous_rank', 0))
    previous_score = dropout.get(
        'yesterday_score', dropout.get('previous_score', 0))

    return f"{name} (#{previous_rank}) — prev {_format_score(previous_score)}"


def _format_score(score: float) -> str:
    """Format score with proper number formatting"""
    if score == int(score):
        return f"{int(score):,}"
    else:
        return f"{score:,.1f}"


def _format_score_delta(delta: float) -> str:
    """Format score delta with sign and formatting"""
    if delta == 0:
        return "±0"
    elif delta > 0:
        return f"+{_format_score(delta)}"
    else:
        return f"−{_format_score(abs(delta))}"  # Use minus sign


def _format_rank_delta(delta: int) -> str:
    """Format rank delta with sign"""
    if delta == 0:
        return "±0"
    elif delta > 0:
        return f"+{delta}"
    else:
        return f"−{abs(delta)}"  # Use minus sign


def _truncate_name(name: str, max_length: int = 40) -> str:
    """Truncate name if too long"""
    if len(name) <= max_length:
        return name
    return name[:max_length-1] + "…"


def _truncate_message(lines: List[str]) -> str:
    """Legacy truncate function - now returns full message for rich embeds"""
    # Return full message since we now use rich embeds that support longer content
    return "\n".join(lines)
    # Try removing sections from bottom up
    sections_to_try = [
        ("📴 **Dropouts**", "dropouts"),
        ("[SPARKLE] **New Entries**", "new entries"),
        ("[TRENDING_DOWN] **Top Movers ↓ (rank)**", "movers down"),
        ("[TRENDING_UP] **Top Movers ↑ (rank)**", "movers up")
    ]

    current_lines = lines[:]

    for section_header, section_name in sections_to_try:
        # Find and remove section
        try:
            section_start = None
            for i, line in enumerate(current_lines):
                if line.startswith(section_header):
                    section_start = i
                    break

            if section_start is not None:
                # Find section end
                section_end = None
                for i in range(section_start + 1, len(current_lines)):
                    if (current_lines[i].startswith("[ANALYTICS]") or current_lines[i].startswith("⏱") or
                            current_lines[i].startswith(("[FIRST_PLACE]", "[TRENDING_UP]", "[TRENDING_DOWN]", "[SPARKLE]", "📴"))):
                        section_end = i
                        break

                if section_end is None:
                    # Remove to end (before footer)
                    for i in range(len(current_lines) - 1, -1, -1):
                        if current_lines[i].startswith(("[ANALYTICS]", "⏱")):
                            section_end = i
                            break

                if section_end is not None:
                    # Replace section with truncation notice
                    removed_count = section_end - section_start - 1
                    if removed_count > 0:
                        current_lines = (current_lines[:section_start] +
                                         [f"*(+{section_name} truncated for length)*", ""] +
                                         current_lines[section_end:])

                    # Check if we're now under the limit
                    test_message = "\n".join(current_lines)
                    if len(test_message) <= 2000:
                        return test_message

        except Exception as e:
            logger.warning(
                f"[WARNING] Error truncating section {section_name}: {e}")
            continue

    # If still too long, just hard truncate
    message = "\n".join(current_lines)
    if len(message) > 2000:
        truncate_pos = 2000 - 20
        message = message[:truncate_pos] + "\n*(truncated)*"

    return message


def _get_most_recent_file_snapshot(current_date: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get the most recent snapshot from file storage that's not the current date

    Args:
        current_date: Current date string (YYYY-MM-DD) to exclude from search

    Returns:
        Tuple of (snapshot_data, date) or (None, None) if no previous snapshot found
    """
    try:
        from data_access.leaderboard_store import get_available_snapshots, read_snapshot

        # Get all available snapshot dates
        available_dates = get_available_snapshots()

        if not available_dates:
            logger.info("[INFO] No previous snapshots found in file storage")
            return None, None

        # Filter out current date and sort in descending order
        previous_dates = [
            date for date in available_dates if date != current_date]

        if not previous_dates:
            logger.info(
                "[INFO] No previous snapshots found (only current date exists)")
            return None, None

        # Sort dates in descending order to get most recent first
        previous_dates.sort(reverse=True)
        most_recent_date = previous_dates[0]

        # Load the most recent snapshot
        snapshot_entries = read_snapshot(most_recent_date)

        if snapshot_entries:
            logger.info(
                f"[SUCCESS] Found most recent snapshot: {most_recent_date} with {len(snapshot_entries)} entries")
            return snapshot_entries, most_recent_date
        else:
            # Try next most recent if available
            if len(previous_dates) > 1:
                logger.info("[RETRY] Trying next most recent snapshot...")
                next_recent_date = previous_dates[1]
                next_snapshot = read_snapshot(next_recent_date)

                if next_snapshot:
                    logger.info(
                        f"[SUCCESS] Using next most recent snapshot: {next_recent_date} with {len(next_snapshot)} entries")
                    return next_snapshot, next_recent_date

        logger.info("[INFO] No valid previous snapshots found")
        return None, None

    except Exception as e:
        logger.error(f"[ERROR] Error getting most recent file snapshot: {e}")
        return None, None


def _get_most_recent_snapshot(redis_client, current_timestamp: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get the most recent snapshot from Redis that's not the current one

    Args:
        redis_client: Redis client instance
        current_timestamp: Current timestamp to exclude from search

    Returns:
        Tuple of (snapshot_data, timestamp) or (None, None) if no previous snapshot found
    """
    try:
        # Search for all leaderboard snapshots
        pattern = "leaderboard:snapshot:*"
        all_keys = redis_client.keys(pattern)

        if not all_keys:
            logger.info("[INFO] No previous snapshots found in Redis")
            return None, None

        # Convert keys to timestamps and filter out current timestamp
        snapshot_timestamps = []
        for key in all_keys:
            # Extract timestamp from key: "leaderboard:snapshot:2025-10-09_11-25"
            # Get part after "leaderboard:snapshot:"
            timestamp_part = key.split(":", 2)[-1]
            if timestamp_part != current_timestamp:  # Exclude current snapshot
                snapshot_timestamps.append(timestamp_part)

        if not snapshot_timestamps:
            logger.info(
                "[INFO] No previous snapshots found (only current timestamp exists)")
            return None, None

        # Sort timestamps in descending order to get most recent first
        snapshot_timestamps.sort(reverse=True)
        most_recent_timestamp = snapshot_timestamps[0]

        # Load the most recent snapshot
        most_recent_key = f"leaderboard:snapshot:{most_recent_timestamp}"
        snapshot_data = redis_client.get(most_recent_key)

        if snapshot_data:
            try:
                entries = json.loads(snapshot_data)
                logger.info(
                    f"[SUCCESS] Found most recent snapshot: {most_recent_timestamp} with {len(entries)} entries")
                return entries, most_recent_timestamp
            except json.JSONDecodeError as e:
                logger.warning(
                    f"[WARNING] Failed to decode snapshot {most_recent_timestamp}: {e}")

                # Try next most recent if available
                if len(snapshot_timestamps) > 1:
                    logger.info("[RETRY] Trying next most recent snapshot...")
                    next_recent_timestamp = snapshot_timestamps[1]
                    next_recent_key = f"leaderboard:snapshot:{next_recent_timestamp}"
                    next_snapshot_data = redis_client.get(next_recent_key)

                    if next_snapshot_data:
                        try:
                            entries = json.loads(next_snapshot_data)
                            logger.info(
                                f"[SUCCESS] Using next most recent snapshot: {next_recent_timestamp} with {len(entries)} entries")
                            return entries, next_recent_timestamp
                        except json.JSONDecodeError:
                            logger.warning(
                                f"[WARNING] Failed to decode next snapshot {next_recent_timestamp}")

        logger.info("[INFO] No valid previous snapshots found")
        return None, None

    except Exception as e:
        logger.error(f"[ERROR] Error getting most recent snapshot: {e}")
        return None, None


def send_discord(message: str, webhook_url: str) -> Dict:
    """
    Send full leaderboard message to Discord using rich embeds

    Args:
        message: Formatted message to send (can be longer than 2000 chars)
        webhook_url: Discord webhook URL

    Returns:
        Result dictionary with success status
    """
    try:
        if not webhook_url:
            logger.warning(
                "[WARNING] No Discord webhook URL provided, skipping Discord send")
            return {'success': False, 'error': 'No webhook URL configured'}

        # Log webhook type based on URL pattern
        if 'leaderboard' in webhook_url.lower() or '1425285300183109644' in webhook_url:
            logger.info(
                "[WEBHOOK] Sending leaderboard report via DEDICATED leaderboard webhook")
        else:
            logger.info(
                "[WEBHOOK] Sending leaderboard report via FALLBACK main webhook")

        # Try to send as rich embed for full content
        try:
            from notifiers.discord_webhook_sender import DiscordWebhook
            import asyncio
            
            # Extract title from message (first line)
            lines = message.split('\n')
            title = lines[0] if lines else "📊 Leaderboard Report"
            description = '\n'.join(lines[1:]) if len(lines) > 1 else message
            
            # Create webhook with rich embed
            webhook = DiscordWebhook(url=webhook_url)
            
            # Discord embed limits: description 4096 chars
            max_description_length = 4000
            
            if len(description) <= max_description_length:
                # Send as single embed
                from discord_webhook import DiscordEmbed
                embed = DiscordEmbed(
                    title=title[:250],  # Title limit 256 chars
                    description=description,
                    color='00ff88'  # Green color
                )
                embed.set_footer(text=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                webhook.add_embed(embed)
                
                response = webhook.execute()
                success = response.status_code == 200
            else:
                # Split into multiple embeds
                chunk_size = 3800  # Leave room for titles/footers
                chunks = [description[i:i+chunk_size] 
                         for i in range(0, len(description), chunk_size)]
                
                success = True
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        embed = DiscordEmbed(
                            title=f"{title} (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else title,
                            description=chunk,
                            color='00ff88'
                        )
                        embed.set_footer(text=f"Part {i+1}/{len(chunks)} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        webhook_part = DiscordWebhook(url=webhook_url)
                        webhook_part.add_embed(embed)
                        response = webhook_part.execute()
                        
                        if response.status_code != 200:
                            success = False
                            break
            
            if success:
                logger.info("Leaderboard report sent to Discord")
                return {'success': True, 'response': 'Rich embed sent'}
            else:
                # Fallback to regular message if embed fails
                logger.warning("[FALLBACK] Rich embed failed, using regular message")
                response = send_discord_message_webhook(message[:1900] + "\n*(truncated)*" if len(message) > 1900 else message, webhook_url)
                if response:
                    logger.info("Leaderboard report sent (fallback)")
                    return {'success': True, 'response': response}
                else:
                    logger.error("[ERROR] Both rich embed and fallback failed")
                    return {'success': False, 'error': 'Both embed and fallback failed'}
                    
        except ImportError:
            # Fallback if discord_webhook not available
            logger.warning("[FALLBACK] discord_webhook not available, using basic sender")
            response = send_discord_message_webhook(message[:1900] + "\n*(truncated)*" if len(message) > 1900 else message, webhook_url)
            if response:
                logger.info("Leaderboard report sent (basic)")
                return {'success': True, 'response': response}
            else:
                logger.error("[ERROR] Basic sender failed")
                return {'success': False, 'error': 'Basic send failed'}

    except Exception as e:
        logger.error(f"💥 Discord send error: {e}")
        return {'success': False, 'error': str(e)}


async def leaderboard_bidaily_task(force_post: bool = False) -> Dict:
    """
    Main bi-daily leaderboard task - runs every 12 hours (09:00 & 21:00 AEST)
    Uses Redis for storage instead of JSON files

    Args:
        force_post: If True, ignore idempotency lock and post anyway

    Returns:
        Task result dictionary
    """
    # Import here to avoid circular imports
    from database.redis_manager import get_redis_connection

    try:
        logger.info("🏁 Starting bi-daily leaderboard task")

        # 1. Get Redis connection
        redis_client = get_redis_connection()
        if not redis_client:
            logger.error("[ERROR] Redis connection not available")
            return {
                'status': 'failed',
                'error': 'Redis connection failed',
                'timestamp': datetime.now().isoformat()
            }

        # 2. Compute current timestamp in AEST
        brisbane_tz = pytz.timezone('Australia/Brisbane')
        local_now = datetime.now(brisbane_tz)
        current_timestamp = local_now.strftime("%Y-%m-%d_%H-%M")
        today_str = local_now.strftime("%Y-%m-%d")

        logger.info(
            f"[TIMER] Processing bi-daily leaderboard for {current_timestamp} (AEST)")

        # 3. Lock guard using Redis (unless forced)
        lock_key = f"leaderboard:lock:{current_timestamp}"
        if not force_post:
            if redis_client.exists(lock_key):
                logger.info(
                    f"[LOCKED] Already processed {current_timestamp} - skipping (use force_post=True to override)")
                return {
                    'status': 'skipped',
                    'reason': 'already_processed',
                    'timestamp': current_timestamp
                }
            # Set lock for 6 hours (longer than bi-daily interval)
            redis_client.setex(lock_key, 6 * 3600, "processed")

        # 4. Fetch current leaderboard data
        api_url = os.getenv(
            'LEADERBOARD_API_URL', 'https://social.legitreal.com/api/competition/leaderboard/')
        timeout = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '15'))
        max_retries = int(os.getenv('MAX_RETRIES', '3'))

        logger.info(
            "[ANALYTICS] Fetching current leaderboard data (first 2 pages only)...")
        raw_data, source_status = fetch_all_pages(
            api_url, timeout, max_retries, max_pages=2)

        if not raw_data and source_status == "failed":
            error_msg = "Failed to fetch any leaderboard data"
            logger.error(f"[ERROR] {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'timestamp': current_timestamp
            }

        # 5. Normalize and rank data
        logger.debug("Normalizing data...")
        current_entries = normalize_and_rank(raw_data)

        if not current_entries:
            error_msg = "No valid entries after normalization"
            logger.error(f"[ERROR] {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'timestamp': current_timestamp
            }

        # 6. Store current snapshot in Redis
        logger.debug("Saving snapshot...")
        current_key = f"leaderboard:snapshot:{current_timestamp}"
        redis_client.setex(current_key, 7 * 24 * 3600,
                           json.dumps(current_entries))  # Keep for 7 days

        # 7. Get most recent previous snapshot from Redis
        logger.info("📖 Loading most recent previous snapshot from Redis...")
        previous_entries, previous_timestamp_found = _get_most_recent_snapshot(
            redis_client, current_timestamp)

        if previous_entries:
            logger.info(
                f"[OK] Loaded most recent snapshot from {previous_timestamp_found}: {len(previous_entries)} entries")
        else:
            logger.info("🆕 No previous snapshot found - first run mode")

        if previous_entries is None:
            logger.info("🆕 No previous snapshot found - first run mode")

        # 8. Compare snapshots
        logger.debug("Comparing snapshots...")
        comparison = compare_snapshots(current_entries, previous_entries)

        # 9. Format Discord message with bi-daily context
        logger.debug("Formatting message...")
        hour = local_now.hour
        time_context = "Morning Report (09:00 AEST)" if hour < 15 else "Evening Report (21:00 AEST)"
        message = format_bidaily_discord_message(
            current_timestamp, comparison, source_status, time_context)

        logger.info(f"📏 Generated message ({len(message)} chars)")

        # 10. Send to Discord using dedicated leaderboard webhook
        webhook_url = os.getenv('LEADERBOARD_DISCORD_WEBHOOK', '')
        if not webhook_url:
            # Fallback to main webhook if leaderboard webhook not configured
            webhook_url = os.getenv('DISCORD_WEBHOOK', '')
            if webhook_url:
                logger.info(
                    "[FALLBACK] Using main Discord webhook for leaderboard")
            else:
                logger.warning(
                    "[WARNING] No Discord webhook URL configured (LEADERBOARD_DISCORD_WEBHOOK or DISCORD_WEBHOOK)")
        else:
            logger.info(
                "[WEBHOOK] Using dedicated leaderboard Discord webhook")
        discord_result = send_discord(message, webhook_url)

        # 11. Return summary
        result = {
            'status': 'success',
            'timestamp': current_timestamp,
            'time_context': time_context,
            'entries_current': len(current_entries),
            'entries_previous': len(previous_entries) if previous_entries else 0,
            'source_status': source_status,
            'discord_sent': discord_result.get('success', False),
            'message_length': len(message),
            'comparison': {
                'leaders': len(comparison.get('leaders_top10', [])),
                'movers_up': len(comparison.get('movers_up', [])),
                'movers_down': len(comparison.get('movers_down', [])),
                'new_entries': len(comparison.get('new_entries', [])),
                'dropouts': len(comparison.get('dropouts', [])),
                'is_first_run': comparison.get('is_first_run', False)
            }
        }

        logger.info(
            f"[OK] Bi-daily leaderboard task completed successfully for {current_timestamp}")
        return result

    except Exception as e:
        error_msg = f"Unexpected error in leaderboard bi-daily task: {e}"
        logger.error(f"💥 {error_msg}", exc_info=True)
        return {
            'status': 'failed',
            'error': error_msg,
            'timestamp': current_timestamp if 'current_timestamp' in locals() else 'unknown'
        }


async def leaderboard_daily_task(force_post: bool = False) -> Dict:
    """
    Main daily leaderboard task

    Args:
        force_post: If True, ignore idempotency lock and post anyway

    Returns:
        Task result dictionary
    """
    # Import here to avoid circular imports
    from data_access.leaderboard_store import (
        read_snapshot, write_snapshot, set_posted_lock
    )

    try:
        logger.info("🏁 Starting daily leaderboard task")

        # 1. Compute today/yesterday dates in AEST
        brisbane_tz = pytz.timezone('Australia/Brisbane')
        local_now = datetime.now(brisbane_tz)
        today_str = local_now.strftime("%Y-%m-%d")

        yesterday = local_now - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")

        logger.info(f"Processing leaderboard for {today_str}")

        # 2. Lock guard (unless forced)
        if not force_post:
            lock_acquired = set_posted_lock(today_str)
            if not lock_acquired:
                logger.info(
                    f"[LOCKED] Already processed {today_str} - skipping (use force_post=True to override)")
                return {
                    'status': 'skipped',
                    'reason': 'already_processed',
                    'date': today_str
                }

        # 3. Fetch current leaderboard data
        api_url = os.getenv(
            'LEADERBOARD_API_URL', 'https://social.legitreal.com/api/competition/leaderboard/')
        timeout = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '15'))
        max_retries = int(os.getenv('MAX_RETRIES', '3'))

        logger.info(
            "[ANALYTICS] Fetching current leaderboard data (first 2 pages only)...")
        raw_data, source_status = fetch_all_pages(
            api_url, timeout, max_retries, max_pages=2)

        if not raw_data and source_status == "failed":
            error_msg = "Failed to fetch any leaderboard data"
            logger.error(f"[ERROR] {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'date': today_str
            }

        # 4. Normalize and rank data
        logger.info("[REFRESH] Normalizing and ranking data...")
        today_entries = normalize_and_rank(raw_data)

        if not today_entries:
            error_msg = "No valid entries after normalization"
            logger.error(f"[ERROR] {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'date': today_str
            }

        # 5. Write today's snapshot
        logger.info("[SAVE] Saving today's snapshot...")
        write_snapshot(today_str, today_entries)

        # 6. Read most recent previous snapshot
        logger.info("📖 Loading most recent previous snapshot...")
        previous_entries, previous_date_found = _get_most_recent_file_snapshot(
            today_str)

        if previous_entries is None:
            logger.info("🆕 No previous snapshot found - first run mode")
        else:
            logger.info(
                f"[OK] Loaded most recent snapshot from {previous_date_found}: {len(previous_entries)} entries")

        # 7. Compare snapshots
        logger.info("[SEARCH] Comparing snapshots...")
        comparison = compare_snapshots(today_entries, previous_entries)

        # 8. Format Discord message
        logger.info("[NOTE] Formatting Discord message...")
        message = format_discord_message(today_str, comparison, source_status)

        logger.info(f"📏 Generated message ({len(message)} chars)")

        # 9. Send to Discord using dedicated leaderboard webhook
        webhook_url = os.getenv('LEADERBOARD_DISCORD_WEBHOOK', '')
        if not webhook_url:
            # Fallback to main webhook if leaderboard webhook not configured
            webhook_url = os.getenv('DISCORD_WEBHOOK', '')
            if webhook_url:
                logger.info(
                    "[FALLBACK] Using main Discord webhook for leaderboard")
            else:
                logger.warning(
                    "[WARNING] No Discord webhook URL configured (LEADERBOARD_DISCORD_WEBHOOK or DISCORD_WEBHOOK)")
        else:
            logger.info(
                "[WEBHOOK] Using dedicated leaderboard Discord webhook")
        discord_result = send_discord(message, webhook_url)

        # 10. Return summary
        result = {
            'status': 'success',
            'date': today_str,
            'entries_today': len(today_entries),
            'entries_previous': len(previous_entries) if previous_entries else 0,
            'previous_date': previous_date_found,
            'source_status': source_status,
            'discord_sent': discord_result.get('success', False),
            'message_length': len(message),
            'comparison': {
                'leaders': len(comparison.get('leaders_top10', [])),
                'movers_up': len(comparison.get('movers_up', [])),
                'movers_down': len(comparison.get('movers_down', [])),
                'new_entries': len(comparison.get('new_entries', [])),
                'dropouts': len(comparison.get('dropouts', [])),
                'is_first_run': comparison.get('is_first_run', False)
            }
        }

        logger.info(
            f"[OK] Daily leaderboard task completed successfully for {today_str}")
        return result

    except Exception as e:
        error_msg = f"Unexpected error in leaderboard task: {e}"
        logger.error(f"💥 {error_msg}", exc_info=True)
        return {
            'status': 'failed',
            'error': error_msg,
            'date': today_str if 'today_str' in locals() else 'unknown'
        }


# CLI support for manual runs
if __name__ == "__main__":
    import argparse

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Daily Leaderboard Logger")
    parser.add_argument('--run-once', action='store_true',
                        help='Run leaderboard task once immediately')
    parser.add_argument('--force', action='store_true',
                        help='Force run even if already processed today')

    args = parser.parse_args()

    if args.run_once:
        result = asyncio.run(leaderboard_daily_task(force_post=args.force))
        print(f"Task result: {result}")
        sys.exit(0 if result['status'] == 'success' else 1)
    else:
        print("Use --run-once to execute the task manually")
        sys.exit(1)
