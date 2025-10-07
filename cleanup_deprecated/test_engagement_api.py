"""
Test Engagement Intelligence Flask API
Tests the complete engagement intelligence system via Flask endpoints
"""

import asyncio
import json
import logging
import requests
import time
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

def test_flask_app_status():
    """Test if Flask app is running and responsive"""
    print("🔍 Testing Flask app status...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Flask app is running")
            print(f"   Service: {data.get('service')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Worker Status: {data.get('worker_status')}")
            print(f"   Active Tasks: {data.get('active_tasks')}")
            
            return True
        else:
            print(f"❌ Flask app returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure the app is running with:")
        print("   python run.py")
        return False
    except Exception as e:
        print(f"❌ Error testing Flask app: {e}")
        return False

def test_engagement_analysis_endpoint():
    """Test the engagement analysis endpoint"""
    print("\n🧠 Testing engagement analysis endpoint...")
    
    try:
        # First get endpoint info
        print("📋 Getting endpoint information...")
        info_response = requests.get(f"{BASE_URL}/trigger-engagement-analysis")
        
        if info_response.status_code == 200:
            info_data = info_response.json()
            print(f"✅ Endpoint info retrieved")
            print(f"   Features: {len(info_data.get('features', []))} features")
            print(f"   Analysis Outputs: {len(info_data.get('analysis_outputs', {}))} output types")
        
        # Now trigger the analysis
        print("\n🚀 Triggering engagement analysis...")
        
        payload = {
            "send_discord": False,  # Don't spam Discord during testing
            "save_results": True
        }
        
        trigger_response = requests.post(
            f"{BASE_URL}/trigger-engagement-analysis",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if trigger_response.status_code == 200:
            trigger_data = trigger_response.json()
            print(f"✅ Analysis triggered successfully")
            print(f"   Status: {trigger_data.get('status')}")
            print(f"   Message: {trigger_data.get('message')}")
            print(f"   Estimated Duration: {trigger_data.get('task_info', {}).get('estimated_duration')}")
            
            # Wait a moment for processing
            print(f"⏳ Waiting for analysis to complete...")
            time.sleep(10)
            
            return True
        else:
            print(f"❌ Failed to trigger analysis: {trigger_response.status_code}")
            print(f"   Response: {trigger_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing engagement analysis: {e}")
        return False

def test_quick_engagement_check():
    """Test the quick engagement check endpoint"""
    print("\n⚡ Testing quick engagement check...")
    
    try:
        response = requests.get(f"{BASE_URL}/engagement-quick-check")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quick check completed")
            print(f"   Status: {data.get('status')}")
            
            quick_result = data.get('quick_check_result', '')
            if quick_result:
                print(f"   Result:")
                for line in quick_result.split('\n'):
                    if line.strip():
                        print(f"     {line}")
            
            return True
        else:
            print(f"❌ Quick check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in quick engagement check: {e}")
        return False

def test_metrics_endpoint():
    """Test the metrics endpoint to see pipeline status"""
    print("\n📊 Testing metrics endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metrics retrieved")
            
            pipeline_metrics = data.get('pipeline_metrics', {})
            worker_status = data.get('worker_status', {})
            
            print(f"   Pipeline Success Rate: {pipeline_metrics.get('success_rate', 0):.1%}")
            print(f"   Total Runs: {pipeline_metrics.get('total_runs', 0)}")
            print(f"   Worker Running: {worker_status.get('is_running', False)}")
            print(f"   Active Tasks: {len(worker_status.get('active_tasks', []))}")
            
            return True
        else:
            print(f"❌ Metrics failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting metrics: {e}")
        return False

def demonstrate_engagement_api_usage():
    """Demonstrate how to use the engagement intelligence API"""
    print("\n🎯 Demonstrating Engagement Intelligence API Usage")
    print("=" * 60)
    
    # Example API calls
    api_examples = [
        {
            "name": "Get Endpoint Information",
            "method": "GET",
            "url": "/trigger-engagement-analysis",
            "description": "Get details about the engagement analysis endpoint"
        },
        {
            "name": "Trigger Full Analysis", 
            "method": "POST",
            "url": "/trigger-engagement-analysis",
            "payload": {"send_discord": True, "save_results": True},
            "description": "Run complete engagement analysis with Discord notification"
        },
        {
            "name": "Quick Engagement Check",
            "method": "GET", 
            "url": "/engagement-quick-check",
            "description": "Get real-time engagement metrics snapshot"
        },
        {
            "name": "Analysis Without Discord",
            "method": "POST",
            "url": "/trigger-engagement-analysis", 
            "payload": {"send_discord": False, "save_results": True},
            "description": "Run analysis and save results but skip Discord notification"
        }
    ]
    
    print("\n📋 Available API Endpoints:")
    for i, example in enumerate(api_examples, 1):
        print(f"\n{i}. {example['name']}")
        print(f"   {example['method']} {BASE_URL}{example['url']}")
        print(f"   {example['description']}")
        
        if example.get('payload'):
            print(f"   Payload: {json.dumps(example['payload'])}")
        
        # Show curl example
        if example['method'] == 'GET':
            curl_cmd = f"curl -X GET {BASE_URL}{example['url']}"
        else:
            if example.get('payload'):
                payload_str = json.dumps(example['payload'])
                curl_cmd = f"curl -X POST {BASE_URL}{example['url']} -H \"Content-Type: application/json\" -d '{payload_str}'"
            else:
                curl_cmd = f"curl -X POST {BASE_URL}{example['url']}"
        
        print(f"   Curl: {curl_cmd}")

def show_sample_engagement_report():
    """Show sample Discord-formatted engagement report"""
    print("\n📢 Sample Discord-Formatted Engagement Report")
    print("-" * 50)
    
    sample_report = """📊 **Engagement Growth Report**

• **Avg Growth Velocity:** +0.73 /min
• **Posts Analyzed:** 25 | **Growing:** 18

🚀 **Top 5 Fastest Posts:**
   1️⃣ **@techinfluencer** — +2.1/min (+112 likes, +45 replies)
   2️⃣ **@cryptoexpert** — +1.8/min (+98 likes, +60 reposts)
   3️⃣ **@socialmediago** — +1.5/min (+87 likes, +23 replies, +15 reposts)
   4️⃣ **@viralcontent** — +1.2/min (+65 likes, +38 replies)
   5️⃣ **@trendingnow** — +1.0/min (+55 likes, +28 reposts)

📈 **Engagement Composition:**
   ❤️ Likes 62% | 💬 Replies 25% | 🔁 Reposts 13%

⚡ **12 posts showing acceleration**
📅 *Analysis: engagement_20251006_234500*"""
    
    print(sample_report)

def main():
    """Run comprehensive Flask API tests"""
    print("🧪 Testing Engagement Intelligence Flask API")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Flask app status
    status_ok = test_flask_app_status()
    test_results.append(("Flask App Status", status_ok))
    
    if not status_ok:
        print("\n❌ Cannot proceed with tests - Flask app is not running")
        print("\nTo start the Flask app:")
        print("1. Open a terminal")
        print("2. Navigate to the analyzer directory")
        print("3. Run: python run.py")
        print("4. Wait for 'Worker started successfully' message")
        print("5. Run this test again")
        return
    
    # Test 2: Metrics endpoint
    metrics_ok = test_metrics_endpoint()
    test_results.append(("Metrics Endpoint", metrics_ok))
    
    # Test 3: Quick engagement check
    quick_check_ok = test_quick_engagement_check()
    test_results.append(("Quick Engagement Check", quick_check_ok))
    
    # Test 4: Full engagement analysis
    analysis_ok = test_engagement_analysis_endpoint()
    test_results.append(("Engagement Analysis", analysis_ok))
    
    # Show API usage examples
    demonstrate_engagement_api_usage()
    
    # Show sample report
    show_sample_engagement_report()
    
    # Test results summary
    print(f"\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Engagement Intelligence API is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()