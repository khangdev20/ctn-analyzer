#!/bin/bash
# Manual trigger test script for Windows PowerShell

echo "🧪 Testing Trending Intelligence Manual Trigger"
echo "==============================================="

# Test 1: Get trigger info
echo "📋 Test 1: Getting trigger information..."
$response1 = Invoke-RestMethod -Uri "http://localhost:5000/trigger-intelligence" -Method GET -ErrorAction SilentlyContinue
if ($response1) {
    Write-Host "✅ GET /trigger-intelligence successful" -ForegroundColor Green
    Write-Host "   Worker running: $($response1.current_status.worker_running)" -ForegroundColor Yellow
    Write-Host "   Can trigger: $($response1.current_status.can_trigger)" -ForegroundColor Yellow
} else {
    Write-Host "❌ GET request failed" -ForegroundColor Red
}

echo ""

# Test 2: Trigger the task
echo "🚀 Test 2: Triggering intelligence task..."
try {
    $response2 = Invoke-RestMethod -Uri "http://localhost:5000/trigger-intelligence" -Method POST -ErrorAction Stop
    Write-Host "✅ POST /trigger-intelligence successful" -ForegroundColor Green
    Write-Host "   Status: $($response2.status)" -ForegroundColor Yellow
    Write-Host "   Message: $($response2.message)" -ForegroundColor Yellow
    Write-Host "   Task ID: $($response2.task_id)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ POST request failed: $_" -ForegroundColor Red
}

echo ""

# Test 3: Check status
echo "📊 Test 3: Checking system status..."
$response3 = Invoke-RestMethod -Uri "http://localhost:5000/status" -Method GET -ErrorAction SilentlyContinue
if ($response3) {
    Write-Host "✅ GET /status successful" -ForegroundColor Green
    Write-Host "   Worker running: $($response3.system_status.worker_running)" -ForegroundColor Yellow
    Write-Host "   Active tasks: $($response3.system_status.active_tasks)" -ForegroundColor Yellow
} else {
    Write-Host "❌ Status request failed" -ForegroundColor Red
}

echo ""
echo "✨ Test completed! Check bot.log for detailed task execution."