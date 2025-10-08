# Trending Intelligence System - AI Agent Instructions

## Architecture Overview

This is a **trending intelligence system** that analyzes social media data using LLMs and provides insights via Discord. The system consists of:

- **Flask API** (`app.py`) - REST endpoints for monitoring and control
- **Async Worker System** (`worker/base.py`) - Background processing with APScheduler
- **Intelligence Pipeline** (`worker/features/intelligence_pipeline.py`) - Multi-stage data processing (1454 lines)
- **LLM Integration** (`llms/llm_models.py`) - Unified interface for OpenAI, Anthropic, Google
- **Discord Notifications** (`notifiers/`) - Rich embed messaging system

## Key Components & Data Flow

```
External API → Data Collector → Intelligence Pipeline → Discord Formatter → Notifications
                                      ↓
                               Enhanced LLM Analysis (5 strategies)
```

### Core Pipeline Stages

1. **Data Collection** - Fetch from `social.legitreal.com/api/feeds/trending`
2. **Cleaning** - Preprocessing and validation
3. **Scoring** - Engagement metrics and viral potential
4. **Analysis** - LLM-powered strategic insights (5 different approaches)
5. **Discord Formatting** - Rich embeds with LLM-generated content

## Worker Architecture Pattern

The system uses a **threaded async worker** pattern:

- Main thread runs Flask app
- Separate daemon thread runs `asyncio` event loop
- APScheduler manages 3 jobs:
  - `trending_intelligence_main`: Every 2 hours
  - `sample_task_test`: Every 2 minutes (debugging)
  - `cleanup_stuck_jobs`: Every 30 minutes

### Task Creation Pattern

```python
async def run(worker):
    task_id = f"task_name_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)
    try:
        # Task logic here
    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)
```

## LLM Integration Patterns

**Unified LLM Interface** - All LLM calls use `llms/llm_models.py`:

```python
from llms.llm_models import LLMModels
llm = LLMModels()
response = llm.call_openai(prompt, system_prompt, model="gpt-5-mini")
```

**5 Strategic Analysis Types** in intelligence pipeline:

- `_analyze_content_strategies()` - Content optimization
- `_analyze_engagement_strategies()` - Engagement patterns
- `_analyze_competitive_strategies()` - Market positioning
- `_generate_trend_predictions()` - Future forecasting
- `_generate_content_suggestions()` - Creative recommendations

## Critical Development Workflows

### Quick Start

```bash
python run.py  # Starts Flask + Worker system
```

### Testing & Debugging

```bash
python test_worker_system.py    # Full system test
python mock_data_provider.py    # Generate mock data when API down
python validate_system.py       # Import/dependency validation
```

### API Monitoring

- `GET /status` - Comprehensive system status
- `GET /metrics` - Pipeline performance metrics
- `GET /topics` - Trending topics analysis
- `GET /health` - Health check with success rates

## Configuration Patterns

**Environment Variables**: Use `.env` file with these critical keys:

- `DISCORD_WEBHOOK` - Discord notifications
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` - LLM providers
- `LOG_LEVEL=INFO`, `LOG_FILE=bot.log` - Logging

**Config System**: `worker/features/trending_config.py` provides:

- `get_config()` - Pipeline configuration
- `get_metrics()` - Performance tracking
- `get_topics_tracker()` - Trending topics state

## Error Handling & Recovery

**Timeout Protection**: 30-minute overall timeout with stage-specific limits
**Cleanup System**: Automatic cleanup of stuck processes every 30 minutes
**Graceful Degradation**: System continues running when external API fails (503 errors)

## Discord Integration

**Rich Embeds**: Use `discord_formatter.py` for LLM-powered embed generation
**Webhook Pattern**: `notifiers/discord_webhook_sender.py` handles both text and rich embeds
**Status Updates**: Automatic notifications with metrics and insights

## Data Storage Patterns

**Structured Paths**:

- Raw data: `data/raw/YYYY/MM/DD/`
- Processed: `data/processed/YYYY/MM/DD/scored/`
- Reports: `data/reports/`

**Batch Processing**: All operations use timestamped batch IDs (`20251005T0613Z`)

## External Dependencies

**Social Media API**: `https://social.legitreal.com/api/feeds/trending`

- **Known Issue**: API frequently returns 503 errors
- **Fallback**: Use `mock_data_provider.py` for offline development

**LLM Providers**: OpenAI (primary), Anthropic, Google (backup options)
**Discord**: Webhook-based notifications (no bot permissions required)
