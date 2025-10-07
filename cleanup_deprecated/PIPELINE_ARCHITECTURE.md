# 🎯 Trending Intelligence Pipeline - Architecture Documentation

## Overview

The Trending Intelligence Pipeline is a comprehensive 10-stage modular system for analyzing social media trends and generating strategic insights. This document provides a complete guide to the refactored architecture, replacing the previous monolithic approach with a scalable, maintainable pipeline design.

## 📁 Project Structure

```
analyzer/
├── pipeline/                          # 🎯 New modular pipeline system
│   ├── __init__.py                    # Pipeline package initialization
│   ├── trending_intelligence_pipeline.py  # Main orchestrator
│   └── stages/                        # Individual pipeline stages
│       ├── __init__.py               # Stages package
│       ├── stage_01_data_collection.py    # 🟢 Data Collection
│       ├── stage_02_data_cleaning.py      # 🟡 Data Cleaning
│       ├── stage_03_growth_tracking.py    # 🟠 Growth Tracking
│       ├── stage_04_score_estimation.py   # 🔵 Score Estimation
│       ├── stage_05_rubric_evaluation.py  # 🟣 Rubric Evaluation
│       ├── stage_06_strategic_analysis.py # 🔴 Strategic Analysis
│       ├── stage_07_predictive_modeling.py # 🟤 Predictive Modeling
│       ├── stage_08_reporting.py          # 🟢 Reporting
│       ├── stage_09_continuous_learning.py # 🟩 Continuous Learning
│       └── stage_10_meta_analysis.py      # 🟪 Meta Analysis
├── pipeline_integration.py           # 🔄 Integration with existing worker
├── test_pipeline_system.py          # 🧪 Comprehensive test suite
├── worker/                           # 🔧 Existing worker system (unchanged)
├── llms/                            # 🤖 LLM integration (unchanged)
├── notifiers/                       # 📢 Discord notifications (unchanged)
└── data/                            # 📊 Structured data storage
    ├── raw/YYYY/MM/DD/              # Stage 1 outputs
    ├── clean/YYYY/MM/DD/            # Stage 2 outputs
    ├── growth/YYYY/MM/DD/           # Stage 3 outputs
    ├── score/YYYY/MM/DD/            # Stage 4 outputs
    ├── rubric/YYYY/MM/DD/           # Stage 5 outputs
    ├── network/YYYY/MM/DD/          # Stage 6 outputs
    ├── predict/YYYY/MM/DD/          # Stage 7 outputs
    ├── report/YYYY/MM/DD/           # Stage 8 outputs
    ├── meta/YYYY/MM/DD/             # Stage 10 outputs
    ├── pipeline/YYYY/MM/DD/         # Pipeline summaries
    └── config/weights/YYYY/MM/DD/   # Stage 9 outputs
```

## 🎯 10-Stage Pipeline Architecture

### Data Flow Overview

```
External API → Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5
     ↓          ↓         ↓         ↓         ↓         ↓
   Raw Data → Clean → Growth → Scores → Rubric → Network
                                                    ↓
Discord ← Stage 8 ← Stage 7 ← Stage 6 ← Stage 5 ← Stage 6
  ↓         ↓         ↓         ↓
Reports  Predict  Analysis  Rubric
    ↓
Stage 9 → Stage 10
    ↓         ↓
Learning → Meta Analysis
```

### Stage Details

#### 🟢 Stage 1: Data Collection

- **Purpose**: Fetch trending posts from external APIs
- **Input**: API endpoints, batch configuration
- **Output**: Raw post data with metadata
- **Key Features**: Duplicate detection, hashtag extraction, structured storage

#### 🟡 Stage 2: Data Cleaning

- **Purpose**: Normalize and validate collected data
- **Input**: Raw post data from Stage 1
- **Output**: Clean, standardized post data
- **Key Features**: Data validation, derived metrics, content normalization

#### 🟠 Stage 3: Growth Tracking

- **Purpose**: Calculate engagement velocity and growth metrics
- **Input**: Clean data from Stage 2
- **Output**: Posts with growth and velocity metrics
- **Key Features**: Historical comparison, velocity calculation, trend analysis

#### 🔵 Stage 4: Score Estimation

- **Purpose**: Apply multi-component scoring algorithms
- **Input**: Growth data from Stage 3
- **Output**: Posts with comprehensive scores
- **Key Features**: Story scoring, engagement scoring, weighted combinations

#### 🟣 Stage 5: Rubric Evaluation

- **Purpose**: Assess viral potential using weighted rubric
- **Input**: Scored data from Stage 4
- **Output**: Posts with viral potential assessment
- **Key Features**: 5-component rubric, tier classification, improvement suggestions

#### 🔴 Stage 6: Strategic Analysis

- **Purpose**: Perform network analysis and pattern detection
- **Input**: Rubric data from Stage 5
- **Output**: Posts with network and pattern insights
- **Key Features**: Hashtag networks, author clustering, strategy patterns

#### 🟤 Stage 7: Predictive Modeling

- **Purpose**: Generate trending probability predictions
- **Input**: Network data from Stage 6
- **Output**: Posts with trending predictions
- **Key Features**: Rule-based model, confidence scoring, tier classification

#### 🟢 Stage 8: Reporting

- **Purpose**: Create Discord embeds and comprehensive reports
- **Input**: Prediction data from Stage 7
- **Output**: Formatted reports and Discord embeds
- **Key Features**: LLM-powered analysis, rich embeds, strategic recommendations

#### 🟩 Stage 9: Continuous Learning

- **Purpose**: Refine model weights based on performance
- **Input**: Report data from Stage 8
- **Output**: Updated weight configurations
- **Key Features**: Accuracy analysis, weight adjustments, learning insights

#### 🟪 Stage 10: Meta Analysis

- **Purpose**: Generate weekly strategic insights and content calendar
- **Input**: Learning data from Stage 9
- **Output**: Weekly analysis and content recommendations
- **Key Features**: Pattern analysis, content calendar, competitive insights

## 🚀 Quick Start

### 1. Test System Setup

```bash
python test_pipeline_system.py
```

### 2. Run Full Pipeline

```python
from pipeline_integration import run_trending_intelligence_task

# Execute complete 10-stage pipeline
result = await run_trending_intelligence_task()
```

### 3. Run Partial Pipeline (Development)

```python
from pipeline_integration import run_partial_pipeline

# Test specific stages
result = await run_partial_pipeline(start_stage=1, end_stage=5)
```

### 4. Integration with Existing Worker

```python
# The pipeline integrates seamlessly with existing BackgroundWorker
# No changes needed to existing scheduler configuration
```

## 🔧 Configuration

### Environment Variables

```bash
# Required for full functionality
DISCORD_WEBHOOK=your_discord_webhook_url
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
GEMINI_API_KEY=your_gemini_api_key        # Optional

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

### Pipeline Configuration

The pipeline uses the existing `worker/features/trending_config.py` configuration system for backward compatibility.

## 🔄 Integration Points

### With Existing Worker System

- **BackgroundWorker**: Pipeline integrates through `pipeline_integration.py`
- **Scheduler**: Uses existing APScheduler setup
- **Task Management**: Maintains existing task tracking patterns

### With Discord Notifications

- **Rich Embeds**: Stage 8 generates Discord-compatible embeds
- **Strategic Analysis**: LLM-powered insights formatted for Discord
- **Webhook Integration**: Uses existing `notifiers/discord_webhook_sender.py`

### With LLM Systems

- **OpenAI Integration**: Primary LLM for strategic analysis (Stage 8)
- **Unified Interface**: Uses existing `llms/llm_models.py`
- **Fallback Models**: Supports Anthropic and Google models

## 📊 Data Storage

### Structured Directory Organization

```
data/[stage]/YYYY/MM/DD/batch_[id].[stage].json
```

### Example File Paths

```
data/raw/2024/10/05/batch_20241005T0613Z.raw.json
data/clean/2024/10/05/batch_20241005T0613Z.clean.json
data/score/2024/10/05/batch_20241005T0613Z.score.json
```

### Batch ID Format

```
batch_YYYYMMDDTHHMMSSz
Example: batch_20241005T061312Z
```

## 🧪 Testing & Validation

### Comprehensive Test Suite

```bash
python test_pipeline_system.py
```

### Test Coverage

- ✅ Import validation
- ✅ Pipeline initialization
- ✅ Stage configuration
- ✅ Directory structure
- ✅ Integration layer
- ✅ Configuration compatibility

### Manual Testing

```python
# Test individual stages
from pipeline.stages import DataCollectionStage
from worker.features.trending_config import get_config

config = get_config()
stage = DataCollectionStage(config)
result = await stage.execute("test_batch_001")
```

## 🚦 Error Handling & Recovery

### Timeout Protection

- **Pipeline Timeout**: 30 minutes total
- **Stage Timeout**: 5 minutes per stage
- **Graceful Degradation**: Pipeline continues if individual stages fail

### Error Recovery

- **Stage Failures**: Pipeline continues with previous stage data
- **Cleanup System**: Automatic cleanup of stuck processes
- **Comprehensive Logging**: Detailed error tracking and reporting

## 📈 Performance & Monitoring

### Metrics Tracking

- **Execution Time**: Per-stage and total pipeline timing
- **Success Rates**: Stage completion and overall pipeline success
- **Data Processing**: Posts processed, trending posts identified
- **Learning Performance**: Model accuracy and improvement tracking

### Monitoring Integration

- **Status Endpoints**: Compatible with existing Flask API endpoints
- **Health Checks**: Pipeline validation and readiness checks
- **Metrics Collection**: Structured metrics for monitoring systems

## 🔄 Migration from Legacy System

### Backward Compatibility

- **Existing API**: All existing Flask endpoints continue to work
- **Worker Integration**: No changes to existing worker configuration
- **Discord Notifications**: Maintains existing notification format
- **Configuration**: Uses existing config system

### Migration Steps

1. **Test**: Run `test_pipeline_system.py` to validate setup
2. **Validate**: Ensure all tests pass before switching
3. **Switch**: Update worker to use `pipeline_integration.run_trending_intelligence_task`
4. **Monitor**: Watch logs and metrics during initial runs
5. **Optimize**: Adjust timeouts and configuration as needed

## 🛠️ Development Guidelines

### Adding New Features

1. **Single Stage**: Add functionality to appropriate existing stage
2. **New Stage**: Create new stage following existing patterns
3. **Cross-Stage**: Use pipeline orchestrator for coordination
4. **Testing**: Add tests to `test_pipeline_system.py`

### Code Structure

```python
class NewStage:
    def __init__(self, config):
        self.config = config

    async def execute(self, batch_id: str, input_data: Dict) -> Optional[Dict]:
        # Stage implementation
        pass

    def _generate_summary(self, result: Dict, batch_id: str) -> Dict:
        # Summary generation
        pass
```

### Error Handling Pattern

```python
try:
    # Stage processing
    result = await self._process_data(input_data)
    return self._create_success_result(result, batch_id)
except Exception as e:
    logger.error(f"Stage failed: {e}")
    return None  # Pipeline will continue with previous data
```

## 📚 API Reference

### Main Pipeline Class

```python
class TrendingIntelligencePipeline:
    async def execute_full_pipeline(**kwargs) -> Dict[str, Any]
    async def execute_partial_pipeline(start_stage: int, end_stage: int) -> Dict[str, Any]
    async def get_pipeline_status() -> Dict[str, Any]
    async def validate_pipeline() -> Dict[str, Any]
```

### Integration Functions

```python
async def run_trending_intelligence_task(worker=None) -> Dict[str, Any]
async def validate_system_setup() -> Dict[str, Any]
async def run_partial_pipeline(start_stage: int, end_stage: int) -> Dict[str, Any]
```

## 🔍 Troubleshooting

### Common Issues

#### Import Errors

```python
# Ensure Python path includes project directory
sys.path.insert(0, '/path/to/analyzer')
```

#### Stage Timeouts

```python
# Adjust timeouts in pipeline configuration
pipeline.stage_timeout = 10 * 60  # 10 minutes
```

#### Missing Dependencies

```bash
pip install -r requirements.txt
```

#### Directory Permissions

```bash
# Ensure write permissions for data directories
chmod -R 755 data/
```

### Debug Mode

```python
# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)

# Run single stage for debugging
result = await stage.execute("debug_batch", test_data)
```

## 📋 Changelog

### Version 1.0.0 (Current)

- ✅ Complete 10-stage pipeline implementation
- ✅ Integration with existing worker system
- ✅ Comprehensive test suite
- ✅ Structured data storage
- ✅ Error handling and recovery
- ✅ LLM integration for strategic analysis
- ✅ Discord notification compatibility

### Future Enhancements

- 🔄 Real-time streaming processing
- 📊 Advanced analytics dashboard
- 🤖 Enhanced AI model integration
- 🔍 Advanced pattern detection
- 📈 Performance optimization

---

## 🎯 Architecture Benefits

### Modularity

- **Single Responsibility**: Each stage has a focused purpose
- **Easy Testing**: Individual stages can be tested in isolation
- **Maintainability**: Changes to one stage don't affect others
- **Scalability**: Stages can be optimized or replaced independently

### Reliability

- **Error Isolation**: Stage failures don't crash entire pipeline
- **Timeout Protection**: Prevents system hang-ups
- **Graceful Degradation**: Pipeline continues with partial failures
- **Comprehensive Logging**: Detailed error tracking and debugging

### Extensibility

- **Plugin Architecture**: New stages can be added easily
- **Configuration Driven**: Behavior controlled through configuration
- **API Compatible**: Maintains existing external interfaces
- **Future Ready**: Architecture supports advanced features

This refactored pipeline architecture provides a robust, scalable foundation for trending intelligence analysis while maintaining full backward compatibility with the existing system.
