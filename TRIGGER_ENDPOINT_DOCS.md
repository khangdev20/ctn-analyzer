# 🚀 Manual Trigger Endpoint Documentation

## Overview

The Trending Intelligence system now has a manual trigger endpoint that allows you to run the intelligence task on-demand for testing or immediate analysis.

## Available Endpoints

### 1. GET `/trigger-intelligence` - Get Trigger Information

**Purpose:** Check if the trigger is available and get usage information

**Example:**

```bash
curl http://localhost:5000/trigger-intelligence
```

**Response:**

```json
{
	"endpoint": "/trigger-intelligence",
	"method": "POST",
	"description": "Manually trigger the trending intelligence task",
	"current_status": {
		"worker_running": true,
		"active_tasks": 0,
		"can_trigger": true
	},
	"usage": {
		"curl_example": "curl -X POST http://localhost:5000/trigger-intelligence"
	}
}
```

### 2. POST `/trigger-intelligence` - Trigger the Task

**Purpose:** Manually start the trending intelligence analysis

**Example:**

```bash
curl -X POST http://localhost:5000/trigger-intelligence
```

**Response (Success):**

```json
{
	"status": "success",
	"message": "Trending intelligence task triggered successfully",
	"triggered_at": "2025-10-06T14:30:00.000Z",
	"task_id": "manual_trigger_20251006T1430Z",
	"task_scheduled": true,
	"worker_status": {
		"active_tasks": 1,
		"total_tasks": 15,
		"worker_running": true
	},
	"monitoring": {
		"logs": "Monitor bot.log for detailed execution progress",
		"status_endpoint": "/status",
		"metrics_endpoint": "/metrics"
	}
}
```

**Response (Error):**

```json
{
	"error": "Worker not running",
	"worker_status": "inactive",
	"help": "Make sure the worker service is started"
}
```

### 3. POST `/trigger` - Alias Endpoint

**Purpose:** Shorter alias for the trigger endpoint

**Example:**

```bash
curl -X POST http://localhost:5000/trigger
```

## PowerShell Examples

### Check if trigger is available:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/trigger-intelligence" -Method GET
```

### Trigger the task:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/trigger-intelligence" -Method POST
```

### Check status after triggering:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/status" -Method GET
```

## Monitoring Task Execution

After triggering the task, you can monitor its progress through:

### 1. Log File

Monitor the detailed execution logs:

```bash
tail -f bot.log
```

### 2. Status Endpoint

Check overall system status:

```bash
curl http://localhost:5000/status
```

### 3. Metrics Endpoint

Get detailed pipeline metrics:

```bash
curl http://localhost:5000/metrics
```

### 4. Heartbeat Endpoint

Check real-time worker activity:

```bash
curl http://localhost:5000/heartbeat
```

## Task Execution Flow

When you trigger the task, here's what happens:

1. **🔍 Pre-task Cleanup** - Clears any stuck previous tasks
2. **📊 Data Collection** - Fetches trending posts from social media API
3. **🧹 Data Cleaning** - Preprocesses and validates the data
4. **📈 Scoring** - Calculates engagement metrics and viral potential
5. **🧠 LLM Analysis** - Runs 5 strategic analysis types using AI
6. **🔔 Discord Notification** - Sends rich embed with insights
7. **✅ Cleanup** - Finalizes and saves results

**Expected Duration:** 5-15 minutes depending on data volume and LLM response times.

## Error Handling

The endpoint includes comprehensive error handling:

- **503 Service Unavailable:** Worker is not running
- **500 Internal Server Error:** Task execution failed
- **Timeout Protection:** Tasks are cancelled after 30 minutes
- **Stuck Task Cleanup:** Automatic cleanup of hung processes

## Testing

Use the provided test script:

```bash
python test_trigger_endpoint.py
```

Or run the PowerShell test:

```powershell
.\test_trigger.ps1
```

## Integration with Scheduled Tasks

The manual trigger uses the same task implementation as the scheduled 15-minute runs, ensuring consistency between manual and automatic execution.

---

**🔥 Pro Tip:** The task runs with enhanced logging when triggered manually, providing detailed progress information in the logs for debugging and monitoring.
