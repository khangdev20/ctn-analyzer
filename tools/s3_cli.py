#!/usr/bin/env python3
"""
S3 CLI Tool for Trending Intelligence System
Provides command-line interface for S3 operations and inspections

Usage:
    python -m tools.s3_cli list prefix=leaderboard/2025/10/
    python -m tools.s3_cli inspect key=reports/trending_prediction/2025/10/batch_001/trending_analysis.json
    python -m tools.s3_cli health
    python -m tools.s3_cli cleanup --days 90
    python -m tools.s3_cli presign key=leaderboard/2025/10/2025-10-08.json

Author: AI Assistant
Date: October 8, 2025
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from data_access.s3_store import get_s3_store, S3Store
from data_access.leaderboard_store import health_check, cleanup_old_snapshots, get_available_snapshots

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def list_objects(prefix: str, max_keys: int = 100):
    """List S3 objects by prefix"""
    try:
        print(f"🔍 Listing S3 objects with prefix: {prefix}")
        print("=" * 80)
        
        s3_store = get_s3_store()
        keys = s3_store.s3_list_prefix(prefix, max_keys=max_keys)
        
        if not keys:
            print(f"📂 No objects found with prefix: {prefix}")
            return
        
        print(f"📂 Found {len(keys)} objects:")
        print()
        
        # Group by type/date for better readability
        grouped = {}
        for key in keys:
            parts = key.split('/')
            if len(parts) >= 2:
                category = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(key)
        
        for category, category_keys in sorted(grouped.items()):
            print(f"📁 {category}/ ({len(category_keys)} objects)")
            for key in sorted(category_keys):
                size_info = ""
                try:
                    # Get object metadata for size
                    client = s3_store.get_s3_client()
                    response = client.head_object(Bucket=s3_store.bucket, Key=key)
                    size = response.get('ContentLength', 0)
                    if size > 1024 * 1024:
                        size_info = f" ({size / (1024 * 1024):.1f} MB)"
                    elif size > 1024:
                        size_info = f" ({size / 1024:.1f} KB)"
                    else:
                        size_info = f" ({size} B)"
                except:
                    pass
                
                print(f"  📄 {key}{size_info}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing objects: {e}")
        sys.exit(1)


def inspect_object(key: str):
    """Inspect S3 object details"""
    try:
        print(f"🔍 Inspecting S3 object: {key}")
        print("=" * 80)
        
        s3_store = get_s3_store()
        
        # Get object metadata
        client = s3_store.get_s3_client()
        
        try:
            response = client.head_object(Bucket=s3_store.bucket, Key=key)
            
            print("📊 Object Metadata:")
            print(f"  Size: {response.get('ContentLength', 0):,} bytes")
            print(f"  Last Modified: {response.get('LastModified', 'Unknown')}")
            print(f"  ETag: {response.get('ETag', 'Unknown').strip('\"')}")
            print(f"  Content Type: {response.get('ContentType', 'Unknown')}")
            print(f"  Server Side Encryption: {response.get('ServerSideEncryption', 'None')}")
            
            # Show custom metadata if present
            metadata = response.get('Metadata', {})
            if metadata:
                print("  Custom Metadata:")
                for k, v in metadata.items():
                    print(f"    {k}: {v}")
            
            print()
            
        except client.exceptions.NoSuchKey:
            print(f"❌ Object not found: {key}")
            return
        
        # Try to read and preview content if it's JSON
        if key.endswith('.json'):
            print("📄 Content Preview:")
            data = s3_store.s3_read_json(key)
            
            if data:
                if isinstance(data, dict):
                    # Show structure for dictionaries
                    print("  Structure:")
                    for k, v in data.items():
                        if isinstance(v, (list, dict)):
                            count = len(v) if isinstance(v, (list, dict)) else 0
                            print(f"    {k}: {type(v).__name__} ({count} items)")
                        else:
                            print(f"    {k}: {type(v).__name__} = {str(v)[:50]}")
                
                elif isinstance(data, list):
                    print(f"  Array with {len(data)} items")
                    if data and isinstance(data[0], dict):
                        print("  First item structure:")
                        for k, v in data[0].items():
                            print(f"    {k}: {type(v).__name__}")
                
                # Show first few lines of JSON
                print("\n  Raw Content (first 500 chars):")
                content_str = json.dumps(data, indent=2)[:500]
                print(f"    {content_str}...")
            else:
                print("  ❌ Could not read JSON content")
        
    except Exception as e:
        print(f"❌ Error inspecting object: {e}")
        sys.exit(1)


def show_health():
    """Show S3 storage health"""
    try:
        print("🏥 S3 Storage Health Check")
        print("=" * 80)
        
        health = health_check()
        
        status_emoji = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'degraded' else "❌"
        print(f"{status_emoji} Overall Status: {health['status'].upper()}")
        print()
        
        # Storage info
        storage = health.get('storage', {})
        print("💾 Storage Configuration:")
        print(f"  S3 Available: {'✅' if storage.get('s3_available') else '❌'}")
        print(f"  Bucket: {storage.get('s3_bucket', 'Not configured')}")
        print(f"  Prefix: {storage.get('s3_prefix', 'Not configured')}")
        if storage.get('s3_error'):
            print(f"  Error: {storage.get('s3_error')}")
        print()
        
        # Locking info
        locking = health.get('locking', {})
        print("🔒 Locking System:")
        print(f"  Redis Available: {'✅' if locking.get('redis_available') else '❌'}")
        print(f"  Fallback: {locking.get('fallback', 'Unknown')}")
        print()
        
        # Data info
        data = health.get('data', {})
        print("📊 Data Summary:")
        print(f"  Snapshot Count: {data.get('snapshot_count', 0):,}")
        print(f"  Oldest Snapshot: {data.get('oldest_snapshot', 'None')}")
        print(f"  Newest Snapshot: {data.get('newest_snapshot', 'None')}")
        
        latest = data.get('latest_snapshot')
        if latest:
            print(f"  Latest Snapshot: {latest.get('date', 'Unknown')} ({latest.get('source', 'unknown source')})")
        
        print(f"\n🕐 Check Time: {health.get('timestamp', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        sys.exit(1)


def cleanup_old_data(days: int):
    """Clean up old snapshots and data"""
    try:
        print(f"🧹 Cleaning up data older than {days} days")
        print("=" * 80)
        
        removed_count = cleanup_old_snapshots(keep_days=days)
        
        if removed_count > 0:
            print(f"✅ Cleaned up {removed_count} old objects")
        else:
            print("✅ No old objects found to clean up")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)


def generate_presigned_url(key: str, expires_in: int = 3600):
    """Generate presigned URL for S3 object"""
    try:
        print(f"🔗 Generating presigned URL for: {key}")
        print(f"⏱️  Expires in: {expires_in} seconds ({expires_in // 3600}h {(expires_in % 3600) // 60}m)")
        print("=" * 80)
        
        s3_store = get_s3_store()
        url = s3_store.get_presigned_url(key, expires_in=expires_in)
        
        if url:
            print("✅ Presigned URL generated successfully:")
            print()
            print(f"🔗 {url}")
            print()
            print("💡 You can use this URL to download the object directly from your browser")
            print(f"   (Valid until: {datetime.now() + timedelta(seconds=expires_in)})")
        else:
            print("❌ Failed to generate presigned URL")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error generating presigned URL: {e}")
        sys.exit(1)


def show_snapshots():
    """Show available leaderboard snapshots"""
    try:
        print("📸 Available Leaderboard Snapshots")
        print("=" * 80)
        
        snapshots = get_available_snapshots()
        
        if not snapshots:
            print("📂 No snapshots found")
            return
        
        print(f"📊 Found {len(snapshots)} snapshots:")
        print()
        
        # Group by month for better readability
        grouped = {}
        for snapshot in snapshots:
            month_key = snapshot[:7]  # YYYY-MM
            if month_key not in grouped:
                grouped[month_key] = []
            grouped[month_key].append(snapshot)
        
        for month, month_snapshots in sorted(grouped.items()):
            print(f"📅 {month} ({len(month_snapshots)} snapshots)")
            for snapshot in month_snapshots:
                print(f"  📄 {snapshot}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing snapshots: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="S3 CLI Tool for Trending Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List objects:
    python -m tools.s3_cli list prefix=leaderboard/2025/10/
    python -m tools.s3_cli list prefix=reports/trending_prediction/ --max-keys 50
    
  Inspect object:
    python -m tools.s3_cli inspect key=leaderboard/2025/10/2025-10-08.json
    
  Health check:
    python -m tools.s3_cli health
    
  Cleanup old data:
    python -m tools.s3_cli cleanup --days 90
    
  Generate presigned URL:
    python -m tools.s3_cli presign key=leaderboard/2025/10/2025-10-08.json --expires 7200
    
  Show snapshots:
    python -m tools.s3_cli snapshots
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List S3 objects by prefix')
    list_parser.add_argument('prefix', help='S3 prefix to list (e.g., prefix=leaderboard/2025/10/)')
    list_parser.add_argument('--max-keys', type=int, default=100, help='Maximum number of keys to return')
    
    # Inspect command
    inspect_parser = subparsers.add_parser('inspect', help='Inspect S3 object details')
    inspect_parser.add_argument('key', help='S3 key to inspect (e.g., key=leaderboard/2025/10/2025-10-08.json)')
    
    # Health command
    subparsers.add_parser('health', help='Show S3 storage health')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, default=90, help='Keep data newer than this many days')
    
    # Presign command
    presign_parser = subparsers.add_parser('presign', help='Generate presigned URL')
    presign_parser.add_argument('key', help='S3 key for presigned URL (e.g., key=leaderboard/2025/10/2025-10-08.json)')
    presign_parser.add_argument('--expires', type=int, default=3600, help='URL expiration time in seconds')
    
    # Snapshots command
    subparsers.add_parser('snapshots', help='Show available leaderboard snapshots')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print("S3 CLI Tool for Trending Intelligence System")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        if args.command == 'list':
            # Parse prefix from "prefix=value" format
            prefix = args.prefix
            if prefix.startswith('prefix='):
                prefix = prefix[7:]  # Remove 'prefix=' part
            list_objects(prefix, args.max_keys)
            
        elif args.command == 'inspect':
            # Parse key from "key=value" format
            key = args.key
            if key.startswith('key='):
                key = key[4:]  # Remove 'key=' part
            inspect_object(key)
            
        elif args.command == 'health':
            show_health()
            
        elif args.command == 'cleanup':
            cleanup_old_data(args.days)
            
        elif args.command == 'presign':
            # Parse key from "key=value" format
            key = args.key
            if key.startswith('key='):
                key = key[4:]  # Remove 'key=' part
            generate_presigned_url(key, args.expires)
            
        elif args.command == 'snapshots':
            show_snapshots()
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()