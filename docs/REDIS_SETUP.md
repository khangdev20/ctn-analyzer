# Redis Installation and Setup Guide

## Why Redis for Trending Intelligence System?

Redis is perfect for your trending intelligence system because:

- **[FAST] Fast Caching**: Cache LLM analysis results to avoid re-processing same content
- **[REFRESH] Real-time Updates**: Pub/Sub for live pipeline notifications
- **[ANALYTICS] Data Expiration**: Automatic cleanup of old cache entries
- **[LAUNCH] Performance**: Reduce API calls and processing time
- **[SAVE] Memory Efficiency**: In-memory storage with persistence options

## Installation Options

### Option 1: Windows (Recommended for Development)

1. **Download Redis for Windows**:

   ```powershell
   # Using Chocolatey
   choco install redis-64

   # Or download from: https://github.com/microsoftarchive/redis/releases
   ```

2. **Start Redis**:

   ```powershell
   redis-server
   ```

3. **Test Connection**:
   ```powershell
   redis-cli ping
   # Should return: PONG
   ```

### Option 2: Docker (Recommended for Production)

1. **Run Redis Container**:

   ```powershell
   docker run --name trending-redis -d -p 6379:6379 redis:7-alpine
   ```

2. **Test Connection**:
   ```powershell
   docker exec -it trending-redis redis-cli ping
   ```

### Option 3: Cloud Redis (Production)

- **AWS ElastiCache**: Managed Redis service
- **Google Cloud Memorystore**: Google's Redis service
- **Redis Cloud**: Official Redis cloud service

## Python Dependencies

Add to your `requirements.txt`:

```txt
redis[hiredis]==5.0.1
redis-py-cluster==2.1.3
```

Install:

```powershell
pip install redis[hiredis]==5.0.1
```

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Redis Cloud Configuration (Production Ready)
REDIS_HOST=redis-11099.c296.ap-southeast-2-1.ec2.redns.redis-cloud.com
REDIS_PORT=11099
REDIS_DB=0
REDIS_USERNAME=default
REDIS_PASSWORD=btkL8Cbz19z3aTcOve2S1v6CW9bnlBTw
REDIS_MAX_CONNECTIONS=20

# Cache Settings
REDIS_DEFAULT_TTL=3600
REDIS_TRENDING_TTL=900
REDIS_ANALYSIS_TTL=1800
```

### Redis Configuration (`redis.conf`)

For production, optimize Redis:

```conf
# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence (optional)
save 900 1
save 300 10
save 60 10000

# Networking
tcp-keepalive 300
timeout 0

# Logging
loglevel notice
```

## Integration with Your System

### 1. Automatic Integration

Your system will automatically detect Redis and enable caching:

```python
# Redis will be used automatically if available
from database.redis_helper import get_redis_helper

redis_helper = await get_redis_helper()
# Will work with or without Redis
```

### 2. LLM Analysis Caching

Your LLM calls will be automatically cached:

```python
# Before: Direct LLM call (expensive)
result = llm.call_openai(prompt, system_prompt)

# After: Cached LLM call (fast on repeat)
redis_helper = await get_redis_helper()
result = await redis_helper.get_or_analyze(
    "content_strategies",
    content,
    lambda: llm.call_openai(prompt, system_prompt)
)
```

### 3. Pipeline Notifications

Get real-time pipeline updates:

```python
# Subscribe to pipeline events
async def handle_notification(channel, data):
    print(f"Pipeline update: {data}")

redis_helper = await get_redis_helper()
await redis_helper.redis_manager.subscribe_to_notifications(
    ["trending_pipeline", "pipeline_stages"],
    handle_notification
)
```

## Performance Benefits

### Without Redis:

- LLM analysis: ~2-5 seconds per call
- Repeated content: Still takes 2-5 seconds
- No real-time updates
- No pipeline coordination

### With Redis:

- First analysis: ~2-5 seconds (cache miss)
- Repeated content: ~10ms (cache hit)
- Real-time pipeline notifications
- Coordinated processing across engines

## Testing Redis Integration

1. **Start Redis** (see installation options above)

2. **Test Basic Connection**:

```powershell
cd /path/to/analyzer
python -c "
import asyncio
from database.redis_manager import RedisManager

async def test():
    redis_mgr = RedisManager()
    connected = await redis_mgr.connect()
    if connected:
        print('[OK] Redis connected successfully!')
        health = await redis_mgr.health_check()
        print(f'Health: {health}')
    else:
        print('[ERROR] Redis connection failed')
    await redis_mgr.disconnect()

asyncio.run(test())
"
```

3. **Test with Your System**:

```powershell
python run.py
# Check logs for: "[OK] Redis helper initialized successfully"
```

## Monitoring Redis

### Redis CLI Commands:

```bash
# Check memory usage
redis-cli info memory

# See all keys
redis-cli keys "*"

# Monitor commands in real-time
redis-cli monitor

# Check cache hit ratio
redis-cli info stats | grep keyspace
```

### Your System's Redis Stats:

```python
# Get cache statistics
redis_helper = await get_redis_helper()
stats = await redis_helper.redis_manager.get_cache_stats()
print(f"Cache stats: {stats}")
```

## Production Deployment

### Docker Compose Integration

Add Redis to your `docker/docker-compose.yml`:

```yaml
services:
  trending-app:
    # ... your app config
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis

  redis:
    image: redis:7-alpine
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  redis_data:
```

### AWS Deployment with ElastiCache

Update your deployment scripts to include ElastiCache:

```bash
# In your aws-ec2-setup.sh
aws elasticache create-cache-cluster \
    --cache-cluster-id trending-redis \
    --engine redis \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1
```

## Troubleshooting

### Redis Not Starting:

```powershell
# Check if port is in use
netstat -an | findstr :6379

# Kill existing Redis
taskkill /f /im redis-server.exe
```

### Connection Issues:

```python
# Test with different settings
redis_mgr = RedisManager({
    "host": "localhost",
    "port": 6379,
    "socket_timeout": 10,
    "socket_connect_timeout": 10
})
```

### Performance Issues:

```bash
# Check Redis performance
redis-cli --latency-history -i 1

# Monitor slow queries
redis-cli config set slowlog-log-slower-than 1000
redis-cli slowlog get 10
```

## Cache Strategy

Your system uses intelligent caching:

1. **LLM Analysis Results**: 30 minutes TTL
2. **Trending Data**: 15 minutes TTL
3. **System Metrics**: 5 minutes TTL
4. **Rate Limiting**: Configurable windows

## Benefits for Your System

### Immediate Benefits:

- [OK] **50-90% faster** repeated analysis
- [OK] **Reduced API costs** (fewer LLM calls)
- [OK] **Real-time notifications** via pub/sub
- [OK] **Better coordination** between engines

### Advanced Benefits:

- [OK] **Rate limiting** for API protection
- [OK] **Session management** for user tracking
- [OK] **Pipeline coordination** across workers
- [OK] **Performance metrics** and monitoring

## Next Steps

1. **Install Redis** using any method above
2. **Add Redis dependencies** to requirements.txt
3. **Start your system** - Redis integration is automatic
4. **Monitor performance** improvement in logs
5. **Scale to production** with cloud Redis when ready

Redis will make your trending intelligence system significantly faster and more efficient! [LAUNCH]
