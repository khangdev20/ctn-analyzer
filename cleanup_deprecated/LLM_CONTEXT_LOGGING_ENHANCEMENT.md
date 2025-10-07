# LLM Context Logging Enhancement

## Overview

Enhanced the LLM integration system to provide detailed context logging for better tracking of AI requests and their purposes.

## Changes Made

### 1. LLM Models Core (`llms/llm_models.py`)

**Enhanced Methods:**

- `call_openai()` - Added `context` parameter for request tracking
- `call_anthropic()` - Added `context` parameter for request tracking
- `call_google()` - Added `context` parameter for request tracking
- `generate_response()` - Updated to pass context through to provider methods

**New Logging Format:**

```
[LLM_REQUEST] OpenAI gpt-4o-mini - Context: content_strategy_analysis - Tokens: 1500
[LLM_SUCCESS] OpenAI gpt-4o-mini - Context: content_strategy_analysis - Response length: 1234 chars
[LLM_ERROR] OpenAI gpt-4o-mini - Context: content_strategy_analysis - Error: Rate limit exceeded
```

### 2. Intelligence Pipeline (`worker/features/intelligence_pipeline.py`)

**Updated LLM Calls with Specific Contexts:**

- Content Strategy Analysis: `context="content_strategy_analysis"`
- Engagement Strategy Analysis: `context="engagement_strategy_analysis"`
- Competitive Analysis: `context="competitive_analysis"`
- Trend Prediction: `context="trend_prediction"`
- Content Suggestions: `context="content_suggestions"`

### 3. Discord Formatter (`worker/features/discord_formatter.py`)

**Updated Context:**

- Discord embed generation: `context="discord_embed_formatting"`

### 4. Prompt Suggestions (`worker/features/prompt_suggestions.py`)

**Updated Context:**

- Content generation: `context="content_generation"`

## Context Categories

| Context                        | Purpose                                    | Expected Usage                 |
| ------------------------------ | ------------------------------------------ | ------------------------------ |
| `content_strategy_analysis`    | Analyzing top-performing content patterns  | High frequency during analysis |
| `engagement_strategy_analysis` | Optimizing engagement tactics              | Medium frequency               |
| `competitive_analysis`         | Market positioning and competitor analysis | Medium frequency               |
| `trend_prediction`             | Forecasting future trends                  | Medium frequency               |
| `content_suggestions`          | Generating specific content ideas          | High frequency                 |
| `discord_embed_formatting`     | Creating Discord message embeds            | Low frequency                  |
| `content_generation`           | General content creation                   | Variable frequency             |

## Benefits

1. **Request Tracking**: Easy identification of which LLM requests serve which business purposes
2. **Performance Monitoring**: Track response times and success rates by use case
3. **Cost Analysis**: Monitor token usage across different features
4. **Error Debugging**: Quickly identify which features are experiencing LLM issues
5. **Optimization**: Identify high-usage contexts for optimization opportunities

## Example Log Output

```
2025-10-06 15:25:02,860 - llms.llm_models - INFO - [LLM_REQUEST] OpenAI gpt-4o-mini - Context: content_strategy_analysis - Tokens: 1500
2025-10-06 15:25:02,860 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-10-06 15:25:05,123 - llms.llm_models - INFO - [LLM_SUCCESS] OpenAI gpt-4o-mini - Context: content_strategy_analysis - Response length: 1456 chars

2025-10-06 15:25:37,984 - llms.llm_models - INFO - [LLM_REQUEST] OpenAI gpt-4o-mini - Context: engagement_strategy_analysis - Tokens: 1500
2025-10-06 15:25:37,984 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-10-06 15:25:40,211 - llms.llm_models - INFO - [LLM_SUCCESS] OpenAI gpt-4o-mini - Context: engagement_strategy_analysis - Response length: 1298 chars
```

## Usage

All existing code will continue to work. The `context` parameter is optional and defaults to `"general"` for backward compatibility.

**New Usage:**

```python
# With context tracking
response = llm.call_openai(
    prompt="Analyze this content",
    context="content_strategy_analysis"
)

# Also works with generate_response
response = llm.generate_response(
    prompt="Generate suggestions",
    context="content_suggestions"
)
```

## Monitoring

You can now filter logs to track specific LLM usage:

- `grep "LLM_REQUEST.*content_strategy" bot.log` - Track content strategy requests
- `grep "LLM_SUCCESS.*discord" bot.log` - Track Discord formatting success
- `grep "LLM_ERROR" bot.log` - Track all LLM errors

This enhancement provides complete visibility into LLM usage patterns across the trending intelligence system.
