# Dynamic Scheduler API Documentation

## Overview

The Dynamic Scheduler API allows you to configure job intervals at runtime without restarting the application. This provides flexibility for testing, production tuning, and operational adjustments.

## Features

- ✅ **Runtime Configuration**: Change intervals without restart
- ✅ **Persistent Storage**: Intervals saved to JSON config file
- ✅ **API Endpoints**: RESTful interface for management
- ✅ **Validation**: Input validation and error handling
- ✅ **Audit Trail**: Track who made changes and when
- ✅ **Default Reset**: Easy reset to default intervals

## API Endpoints

### 1. Get Current Intervals

```http
GET /scheduler/intervals
```

**Response:**

```json
{
	"status": "success",
	"intervals": {
		"content_analysis_minutes": 12,
		"trending_prediction_minutes": 10,
		"leaderboard_hours": 1,
		"main_flow_hours": 2,
		"debate_strategy_hours": 2,
		"cleanup_minutes": 30,
		"disk_cleanup_hours": 6,
		"last_updated": "2025-10-09T14:30:00.123456",
		"updated_by": "api_user"
	},
	"timestamp": "2025-10-09T14:35:00.123456Z"
}
```

### 2. Update Specific Interval

```http
PUT /scheduler/intervals/{job_name}
Content-Type: application/json
```

**Request Body:**

```json
{
	"value": 30,
	"unit": "minutes",
	"updated_by": "admin_user"
}
```

**Response:**

```json
{
	"status": "success",
	"message": "Updated leaderboard interval to 30 minutes",
	"job_name": "leaderboard",
	"new_value": 30,
	"unit": "minutes",
	"updated_by": "admin_user",
	"timestamp": "2025-10-09T14:35:00.123456Z",
	"note": "Change will take effect on next scheduler restart"
}
```

### 3. Reset All Intervals to Defaults

```http
POST /scheduler/intervals/reset
Content-Type: application/json
```

**Request Body:**

```json
{
	"updated_by": "admin_user"
}
```

**Response:**

```json
{
	"status": "success",
	"message": "Reset all scheduler intervals to defaults",
	"updated_by": "admin_user",
	"timestamp": "2025-10-09T14:35:00.123456Z",
	"note": "Changes will take effect on next scheduler restart"
}
```

### 4. Restart Scheduler (Optional)

```http
POST /scheduler/restart
```

**Response:**

```json
{
	"status": "not_supported",
	"message": "Dynamic scheduler restart not implemented",
	"note": "Please restart the application to apply new intervals"
}
```

## Supported Job Names

| Job Name              | Default Interval | Unit    | Description                |
| --------------------- | ---------------- | ------- | -------------------------- |
| `content_analysis`    | 12               | minutes | Latest posts analysis      |
| `trending_prediction` | 10               | minutes | Trend prediction engine    |
| `leaderboard`         | 1                | hours   | Competition leaderboard    |
| `main_flow`           | 2                | hours   | Main intelligence pipeline |
| `debate_strategy`     | 2                | hours   | Debate strategy monitor    |
| `cleanup`             | 30               | minutes | System cleanup             |
| `disk_cleanup`        | 6                | hours   | Storage management         |

## Usage Examples

### Command Line (curl)

**Get current intervals:**

```bash
curl http://localhost:5000/scheduler/intervals
```

**Update leaderboard to run every 30 minutes:**

```bash
curl -X PUT http://localhost:5000/scheduler/intervals/leaderboard \
     -H "Content-Type: application/json" \
     -d '{"value": 30, "unit": "minutes", "updated_by": "admin"}'
```

**Update content analysis to run every 2 hours:**

```bash
curl -X PUT http://localhost:5000/scheduler/intervals/content_analysis \
     -H "Content-Type: application/json" \
     -d '{"value": 2, "unit": "hours", "updated_by": "admin"}'
```

**Reset all intervals to defaults:**

```bash
curl -X POST http://localhost:5000/scheduler/intervals/reset \
     -H "Content-Type: application/json" \
     -d '{"updated_by": "admin"}'
```

### Python Requests

```python
import requests

BASE_URL = "http://localhost:5000"

# Get current intervals
response = requests.get(f"{BASE_URL}/scheduler/intervals")
intervals = response.json()

# Update leaderboard interval
update_data = {
    "value": 15,
    "unit": "minutes",
    "updated_by": "python_script"
}
response = requests.put(
    f"{BASE_URL}/scheduler/intervals/leaderboard",
    json=update_data
)

# Reset to defaults
reset_data = {"updated_by": "python_script"}
response = requests.post(
    f"{BASE_URL}/scheduler/intervals/reset",
    json=reset_data
)
```

### JavaScript (fetch)

```javascript
// Get current intervals
const intervals = await fetch('/scheduler/intervals').then((r) => r.json());

// Update interval
const updateResponse = await fetch('/scheduler/intervals/leaderboard', {
	method: 'PUT',
	headers: { 'Content-Type': 'application/json' },
	body: JSON.stringify({
		value: 45,
		unit: 'minutes',
		updated_by: 'web_admin',
	}),
});

// Reset to defaults
const resetResponse = await fetch('/scheduler/intervals/reset', {
	method: 'POST',
	headers: { 'Content-Type': 'application/json' },
	body: JSON.stringify({ updated_by: 'web_admin' }),
});
```

## Configuration File

Intervals are stored in `config/scheduler_intervals.json`:

```json
{
	"content_analysis_minutes": 12,
	"trending_prediction_minutes": 10,
	"leaderboard_hours": 1,
	"main_flow_hours": 2,
	"debate_strategy_hours": 2,
	"cleanup_minutes": 30,
	"disk_cleanup_hours": 6,
	"last_updated": "2025-10-09T14:30:00.123456",
	"updated_by": "api_user"
}
```

## Error Handling

### Validation Errors

```json
{
	"error": "Value must be a positive integer",
	"status": "failed"
}
```

### Invalid Job Name

```json
{
	"error": "Failed to update interval",
	"status": "failed"
}
```

### Missing Data

```json
{
	"error": "Missing 'value' field",
	"status": "failed"
}
```

## Testing

Run the comprehensive API test:

```bash
python test_scheduler_api.py
```

This test will:

1. ✅ Get current intervals
2. ✅ Update leaderboard interval
3. ✅ Update content analysis interval
4. ✅ Verify changes
5. ✅ Test scheduler restart
6. ✅ Reset to defaults
7. ✅ Final verification

## Production Considerations

### Security

- Add authentication/authorization for production use
- Validate user permissions before allowing changes
- Log all configuration changes

### Monitoring

- Monitor job execution after interval changes
- Set reasonable min/max interval limits
- Alert on configuration changes

### Backup

- Backup configuration before changes
- Version control for configuration files
- Rollback mechanism for bad configurations

## Implementation Details

### Dynamic Loading

- Configuration loaded at scheduler startup
- File-based persistence with JSON format
- Fallback to defaults if config file missing

### Scheduler Integration

- Intervals read from config during scheduler setup
- Changes require scheduler restart to take effect
- Future enhancement: Hot reload capability

### Audit Trail

- Every change tracked with timestamp
- User identification for accountability
- Configuration history in JSON file

This dynamic scheduler API provides production-ready interval management with comprehensive validation, error handling, and audit capabilities.
