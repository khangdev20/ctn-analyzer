from typing import Literal
import twooter.sdk
from .data_collector import collect_trending_data


def feeds_collector(key: Literal['trending', 'latest', 'home', 'explore'] = 'latest', cursor: str = None, num_pages: int = 5):
    """
    Collect feed data using twooter SDK and save to file.

    Args:
        key: Feed type to collect ('trending', 'latest', 'home', 'explore')
        cursor: Optional cursor for pagination
        num_pages: Number of pages to collect (default: 5)

    Returns:
        str: Path to saved file, or None if failed
    """
    data = collect_trending_data(num_pages=num_pages, key=key)
    print(data)
    return data
