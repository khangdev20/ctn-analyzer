#!/usr/bin/env python3
"""
Dynamic Scheduler API Test
Demonstrates how to configure scheduler intervals via API

Usage:
1. Start the application: python run.py
2. Run this test: python test_scheduler_api.py
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"


def test_scheduler_api():
    """Test dynamic scheduler API endpoints"""

    print("🔧 DYNAMIC SCHEDULER API TEST")
    print("=" * 60)

    # Test 1: Get current intervals
    print("📊 1. Getting current scheduler intervals...")
    try:
        response = requests.get(f"{BASE_URL}/scheduler/intervals")
        if response.status_code == 200:
            data = response.json()
            print("✅ Current intervals:")
            intervals = data.get('intervals', {})
            for key, value in intervals.items():
                if key.endswith(('_minutes', '_hours')):
                    print(f"   • {key}: {value}")
        else:
            print(f"❌ Failed to get intervals: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error getting intervals: {e}")

    print()

    # Test 2: Update leaderboard interval to 30 minutes
    print("⚡ 2. Updating leaderboard interval to 30 minutes...")
    try:
        update_data = {
            "value": 30,
            "unit": "minutes",
            "updated_by": "test_script"
        }
        response = requests.put(
            f"{BASE_URL}/scheduler/intervals/leaderboard",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully updated leaderboard interval:")
            print(
                f"   • New value: {data.get('new_value')} {data.get('unit')}")
            print(f"   • Updated by: {data.get('updated_by')}")
            print(f"   • Note: {data.get('note')}")
        else:
            print(f"❌ Failed to update interval: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error updating interval: {e}")

    print()

    # Test 3: Update content analysis to 5 minutes
    print("📈 3. Updating content analysis interval to 5 minutes...")
    try:
        update_data = {
            "value": 5,
            "unit": "minutes",
            "updated_by": "test_script"
        }
        response = requests.put(
            f"{BASE_URL}/scheduler/intervals/content_analysis",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully updated content analysis interval:")
            print(
                f"   • New value: {data.get('new_value')} {data.get('unit')}")
        else:
            print(f"❌ Failed to update interval: {response.status_code}")
    except Exception as e:
        print(f"❌ Error updating interval: {e}")

    print()

    # Test 4: Get updated intervals
    print("📊 4. Getting updated intervals...")
    try:
        response = requests.get(f"{BASE_URL}/scheduler/intervals")
        if response.status_code == 200:
            data = response.json()
            print("✅ Updated intervals:")
            intervals = data.get('intervals', {})
            for key, value in intervals.items():
                if key.endswith(('_minutes', '_hours')):
                    print(f"   • {key}: {value}")
            print(f"   • Last updated: {intervals.get('last_updated')}")
            print(f"   • Updated by: {intervals.get('updated_by')}")
        else:
            print(f"❌ Failed to get intervals: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting intervals: {e}")

    print()

    # Test 5: Test scheduler restart (optional)
    print("🔄 5. Testing scheduler restart...")
    try:
        response = requests.post(f"{BASE_URL}/scheduler/restart")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message')}")
        else:
            data = response.json()
            if data.get('status') == 'not_supported':
                print(f"ℹ️ {data.get('message')}")
                print(f"   Note: {data.get('note')}")
            else:
                print(f"❌ Failed to restart scheduler: {response.status_code}")
    except Exception as e:
        print(f"❌ Error restarting scheduler: {e}")

    print()

    # Test 6: Reset to defaults
    print("🔄 6. Resetting intervals to defaults...")
    try:
        reset_data = {
            "updated_by": "test_script_reset"
        }
        response = requests.post(
            f"{BASE_URL}/scheduler/intervals/reset",
            json=reset_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully reset to defaults:")
            print(f"   • Message: {data.get('message')}")
            print(f"   • Updated by: {data.get('updated_by')}")
        else:
            print(f"❌ Failed to reset intervals: {response.status_code}")
    except Exception as e:
        print(f"❌ Error resetting intervals: {e}")

    print()

    # Test 7: Final verification
    print("✅ 7. Final verification - getting reset intervals...")
    try:
        response = requests.get(f"{BASE_URL}/scheduler/intervals")
        if response.status_code == 200:
            data = response.json()
            print("✅ Final intervals after reset:")
            intervals = data.get('intervals', {})
            for key, value in intervals.items():
                if key.endswith(('_minutes', '_hours')):
                    print(f"   • {key}: {value}")
        else:
            print(f"❌ Failed to get final intervals: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting final intervals: {e}")

    print()
    print("=" * 60)
    print("🎉 DYNAMIC SCHEDULER API TEST COMPLETED!")
    print("")
    print("📋 API ENDPOINTS TESTED:")
    print("   ✅ GET  /scheduler/intervals - Get current intervals")
    print("   ✅ PUT  /scheduler/intervals/<job> - Update specific interval")
    print("   ✅ POST /scheduler/intervals/reset - Reset to defaults")
    print("   ✅ POST /scheduler/restart - Restart scheduler")
    print("")
    print("🔧 USAGE EXAMPLES:")
    print('   curl -X PUT http://localhost:5000/scheduler/intervals/leaderboard \\')
    print('        -H "Content-Type: application/json" \\')
    print(
        '        -d \'{"value": 30, "unit": "minutes", "updated_by": "admin"}\'')
    print("")
    print('   curl -X POST http://localhost:5000/scheduler/intervals/reset \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"updated_by": "admin"}\'')
    print("=" * 60)


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("🟢 Server is running, starting API test...")
            test_scheduler_api()
        else:
            print(
                f"🔴 Server returned {response.status_code}, but continuing test...")
            test_scheduler_api()
    except requests.exceptions.ConnectionError:
        print("🔴 ERROR: Cannot connect to server!")
        print("Please start the application first:")
        print("   python run.py")
        print("Then run this test again.")
    except Exception as e:
        print(f"🔴 ERROR: {e}")
        print("Please ensure the application is running on http://localhost:5000")
