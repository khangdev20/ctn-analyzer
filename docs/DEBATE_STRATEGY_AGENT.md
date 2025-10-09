# Debate Strategy AI Agent - Integration Guide

## Overview

The Debate Strategy AI Agent is a competition-focused social media monitoring system that automatically:

1. **Fetches posts** from kingstondaily activity feed
2. **Filters debate content** using strategic keywords
3. **Analyzes stance and claims** with LLM intelligence
4. **Generates strategic replies** with data-driven counterpoints
5. **Sends Discord notifications** with formatted debate strategies

## Architecture Integration

### 🏗️ System Components

```
External API → Debate Strategy Agent → LLM Analysis → Discord Notifications
     ↓                ↓                    ↓              ↓
kingstondaily → Content Filter → Strategic Reply → Rich Embed Messages
```

### 📂 File Structure

```
worker/tasks/debate_strategy_task.py    # Main AI agent implementation
config/debate_discord_config.py         # Discord channel configuration
test_debate_strategy.py                 # Standalone test runner
worker/scheduler.py                     # Task scheduling (every 30 min)
worker/base.py                         # Worker integration
```

## Key Features

### 🎯 Strategic Analysis Pipeline

1. **Data Fetcher**

   - Endpoint: `https://social.legitreal.com/api/users/@kingstondaily/activity`
   - Keywords: `debate`, `slogan`, `argument`, `policy`, `Castillo2025`
   - Extracts: content, engagement metrics, links, hashtags

2. **Debate Analyzer**

   - **Stance Detection**: supportive, critical, or neutral
   - **Claim Analysis**: core arguments and evidence types
   - **Engagement Scoring**: prioritizes high-interaction posts (>30 threshold)
   - **Trending Tags**: identifies viral debate content

3. **Reply Generator**
   - **Strategic Structure**: data-driven counterpoints + measurable framing
   - **Character Limit**: Under 240 characters for social media
   - **Hashtag Integration**: `#DebateDay`, `#PolicyOverPosters`, `#Accountability`
   - **Civil Tone**: factual, non-inflammatory responses

### 🤖 LLM Integration

**Analysis Prompt Pattern:**

```
Analyze this social media post for debate strategy:
POST CONTENT: "{content}"

Provide analysis in JSON format:
{
  "stance": "supportive|critical|neutral",
  "core_claim": "main argument",
  "topic": "debate topic",
  "has_evidence": true/false,
  "evidence_type": "data|anecdotal|none",
  "reply_worthy": true/false,
  "reply_strategy": "counterpoint approach"
}
```

**Reply Generation Prompt:**

```
Generate a strategic debate reply:
- Provides data-driven counterpoint
- Uses measurable framing
- Remains civil and factual
- Under 240 characters
- Emphasizes clarity and accountability
```

### 💬 Discord Integration

**Rich Embed Format:**

```
🎯 Debate Reply Ready
🔗 Post: {embed_link}
⚡ Engagement: {score}
💬 Reply: "{generated_reply}"
```

**Summary Reports:**

- Total replies generated
- Average engagement scores
- Strategy focus areas
- Batch tracking with timestamps

## Installation & Setup

### 1. Environment Configuration

Add to your `.env` file:

```bash
# Required - Main Discord webhook
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_MAIN_WEBHOOK

# Optional - Dedicated debate strategy channel
DEBATE_STRATEGY_WEBHOOK=https://discord.com/api/webhooks/YOUR_DEBATE_WEBHOOK

# Required - LLM API keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  # Optional backup
GEMINI_API_KEY=your_google_key       # Optional backup
```

### 2. Discord Server Setup

1. Create `#debate-strategy` channel
2. Add webhook integration
3. Copy webhook URL to environment variables
4. Test connectivity with `python test_debate_strategy.py`

### 3. Scheduler Integration

The agent runs automatically every 30 minutes via the enhanced scheduler:

```python
# Already integrated in worker/scheduler.py
scheduler.add_job(
    worker._run_debate_strategy_task,
    'interval',
    minutes=30,
    id='debate_strategy_monitor',
    max_instances=1,
    name='Debate Strategy Monitor (Competition AI Agent)'
)
```

## Usage Examples

### Manual Testing

```bash
# Test the agent without Discord notifications
python test_debate_strategy.py

# Run with custom batch ID
python -c "
import asyncio
from worker.tasks.debate_strategy_task import run_debate_strategy_task
result = asyncio.run(run_debate_strategy_task('manual_test_001', False))
print(result)
"
```

### Production Monitoring

```bash
# Start the full system (includes debate agent)
python run.py

# Check system status
curl http://localhost:5000/status

# View recent logs
tail -f bot.log | grep "🎯"
```

## API Response Handling

### Successful Response Example

```json
{
	"status": "success",
	"batch_id": "debate_strategy_20251009T1030Z",
	"timestamp": "2025-10-09T10:30:00Z",
	"statistics": {
		"total_posts_fetched": 45,
		"debate_posts_found": 8,
		"posts_selected": 3,
		"replies_generated": 3
	},
	"replies": [
		{
			"post_id": "12345",
			"original_content": "Castillo2025 will save our economy!",
			"generated_reply": "Economic policies need measurable outcomes. What specific metrics define 'saving'? #PolicyOverPosters #Accountability",
			"engagement_score": 42,
			"analysis": {
				"stance": "supportive",
				"core_claim": "economic salvation",
				"has_evidence": false
			}
		}
	],
	"discord_sent": true
}
```

### Error Handling

```json
{
	"status": "error",
	"batch_id": "debate_strategy_20251009T1030Z",
	"error": "API request failed with status 503",
	"timestamp": "2025-10-09T10:30:00Z"
}
```

## Performance Metrics

### Monitoring KPIs

- **Fetch Success Rate**: API connectivity health
- **Debate Detection Rate**: Content filtering accuracy
- **Reply Generation Rate**: LLM processing success
- **Discord Delivery Rate**: Notification reliability
- **Average Processing Time**: End-to-end latency

### Expected Performance

- **Execution Time**: 30-60 seconds per run
- **Posts Processed**: 20-50 per batch
- **Debate Posts Found**: 5-15% of total posts
- **Reply Generation**: 80-90% success rate
- **Memory Usage**: ~50-100MB during execution

## Troubleshooting

### Common Issues

1. **API Connection Failures**

   ```
   Error: API request failed with status 503
   Solution: API may be down, agent will retry on next cycle
   ```

2. **No Debate Posts Found**

   ```
   Status: no_debate_posts
   Solution: Normal - indicates low debate activity period
   ```

3. **LLM Generation Errors**

   ```
   Error: OpenAI API key not configured
   Solution: Set OPENAI_API_KEY in environment variables
   ```

4. **Discord Notification Failures**
   ```
   Discord sent: false
   Solution: Check DISCORD_WEBHOOK URL validity
   ```

### Debug Mode

```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG

# Run standalone test
python test_debate_strategy.py

# Check specific error patterns
grep -i "debate.*error" bot.log
```

## Integration with Existing System

### Scheduler Coordination

- Runs alongside main intelligence flow (every 2 hours)
- Independent of leaderboard tasks (every 12 hours)
- Minimal resource overlap with other engines
- Automatic cleanup via maintenance scheduler

### Data Storage

- Results saved to `data/reports/debate_strategy/`
- Follows existing batch ID naming convention
- JSON format compatible with other analysis engines
- S3 integration available via existing data_access layer

### Discord Channel Organization

```
#general-intelligence     # Main flow reports (every 2h)
#leaderboard-updates      # Competition standings (every 12h)
#debate-strategy          # AI-generated replies (every 2 hours)
#system-maintenance       # Cleanup and health (every 30min)
```

## Security & Compliance

### Content Safety

- Civil tone enforcement via LLM prompts
- Character limits prevent spam-like content
- No personal attacks or inflammatory language
- Factual focus with measurable claims emphasis

### API Security

- Rate limiting via 30-minute intervals
- Timeout protection (30 seconds per request)
- Graceful fallback when API unavailable
- No sensitive data storage or caching

### Discord Security

- Webhook-only integration (no bot permissions)
- Message content appropriate for public channels
- No direct user targeting or mentions
- Batch processing prevents notification spam

## Future Enhancements

### Planned Features

1. **Sentiment Analysis**: Track debate tone over time
2. **Competitor Monitoring**: Analyze opposition strategy patterns
3. **Engagement Prediction**: Forecast reply interaction rates
4. **A/B Testing**: Compare different reply strategies
5. **Multi-Platform Support**: Expand beyond kingstondaily

### Integration Opportunities

- **Main Flow Engine**: Include debate metrics in comprehensive reports
- **Network Intelligence**: Map debate influence networks
- **Temporal Analytics**: Identify optimal reply timing
- **Strategic Intelligence**: Measure campaign messaging effectiveness

---

**Last Updated**: October 9, 2025  
**Version**: 1.0.0  
**Author**: AI Assistant  
**Status**: Production Ready
