#!/usr/bin/env python3
"""
Test script for the manual trigger endpoint
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"


def test_trigger_info():
    """Test the GET endpoint for trigger information"""
    print("🔍 Testing trigger info endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/trigger-intelligence")

        if response.status_code == 200:
            data = response.json()
            print("✅ GET /trigger-intelligence successful")
            print(
                f"   Worker running: {data['current_status']['worker_running']}")
            print(f"   Active tasks: {data['current_status']['active_tasks']}")
            print(f"   Can trigger: {data['current_status']['can_trigger']}")
            return True
        else:
            print(f"❌ GET request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing trigger info: {e}")
        return False


def test_trigger_task():
    """Test the POST endpoint to trigger the task"""
    print("\n🚀 Testing trigger task endpoint...")

    try:
        response = requests.post(f"{BASE_URL}/trigger-intelligence")

        if response.status_code == 200:
            data = response.json()
            print("✅ POST /trigger-intelligence successful")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Message: {data.get('message', 'no message')}")
            print(f"   Task ID: {data.get('task_id', 'no task id')}")
            print(
                f"   Triggered at: {data.get('triggered_at', 'no timestamp')}")

            if 'worker_status' in data:
                worker = data['worker_status']
                print(
                    f"   Worker active tasks: {worker.get('active_tasks', 0)}")
                print(f"   Worker total tasks: {worker.get('total_tasks', 0)}")

            return True
        else:
            print(f"❌ POST request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing trigger task: {e}")
        return False


def test_status_after_trigger():
    """Test the status endpoint after triggering"""
    print("\n📊 Testing status after trigger...")

    try:
        response = requests.get(f"{BASE_URL}/status")

        if response.status_code == 200:
            data = response.json()
            print("✅ GET /status successful")

            if 'system_status' in data:
                system = data['system_status']
                print(
                    f"   Worker running: {system.get('worker_running', False)}")
                print(f"   Active tasks: {system.get('active_tasks', 0)}")
                print(f"   Total runs: {system.get('total_runs', 0)}")
                print(f"   Success rate: {system.get('success_rate', 0):.1%}")

            return True
        else:
            print(f"❌ Status request failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error testing status: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Manual Trigger Endpoint")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print()

    # Test sequence
    tests = [
        ("Trigger Info", test_trigger_info),
        ("Trigger Task", test_trigger_task),
        ("Status Check", test_status_after_trigger)
    ]

    results = []

    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

        if test_name == "Trigger Task" and result:
            print("⏳ Waiting 5 seconds for task to start...")
            time.sleep(5)

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    print(
        f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests:.1%}")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! The trigger endpoint is working correctly.")
    else:
        print(
            f"\n⚠️ {total_tests - passed_tests} test(s) failed. Check the output above.")


if __name__ == "__main__":
    main()
