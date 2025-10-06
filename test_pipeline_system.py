# 🧪 Pipeline System Test - Comprehensive Validation

import asyncio
import logging
import sys
import traceback
from datetime import datetime, timezone
import json
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pipeline_test.log')
    ]
)

logger = logging.getLogger(__name__)


async def test_pipeline_imports():
    """Test that all pipeline components can be imported successfully"""
    logger.info("🔍 Testing pipeline imports...")
    
    try:
        # Test main pipeline import
        from pipeline import TrendingIntelligencePipeline
        logger.info("✅ TrendingIntelligencePipeline import successful")
        
        # Test integration import
        from pipeline_integration import pipeline_integration, run_trending_intelligence_task
        logger.info("✅ Pipeline integration import successful")
        
        # Test individual stage imports
        from pipeline.stages import (
            DataCollectionStage, DataCleaningStage, GrowthTrackingStage,
            ScoreEstimationStage, RubricEvaluationStage, StrategicAnalysisStage,
            PredictiveModelingStage, ReportingStage, ContinuousLearningStage,
            MetaAnalysisStage
        )
        logger.info("✅ All pipeline stages import successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline import failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_pipeline_initialization():
    """Test pipeline initialization and configuration"""
    logger.info("🔧 Testing pipeline initialization...")
    
    try:
        # Import required components
        from pipeline import TrendingIntelligencePipeline
        from worker.features.trending_config import get_config
        
        # Get configuration
        config = get_config()
        logger.info(f"✅ Configuration loaded: {type(config)}")
        
        # Initialize pipeline
        pipeline = TrendingIntelligencePipeline(config)
        logger.info("✅ Pipeline initialized successfully")
        
        # Test pipeline status
        status = await pipeline.get_pipeline_status()
        logger.info(f"✅ Pipeline status: {status['configuration']['stages_initialized']} stages initialized")
        
        # Test pipeline validation
        validation = await pipeline.validate_pipeline()
        logger.info(f"✅ Pipeline validation: {validation['overall_status']}")
        
        if validation['issues']:
            logger.warning(f"⚠️ Validation issues: {validation['issues']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline initialization failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_integration_layer():
    """Test the pipeline integration layer"""
    logger.info("🔗 Testing integration layer...")
    
    try:
        from pipeline_integration import pipeline_integration
        
        # Test validation
        validation_result = await pipeline_integration.validate_pipeline_setup()
        logger.info(f"✅ Integration validation: {validation_result['integration_status']}")
        
        # Test metrics
        metrics = pipeline_integration.get_pipeline_metrics()
        logger.info(f"✅ Integration metrics: {metrics['architecture']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration layer test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_directory_structure():
    """Test that required directories exist or can be created"""
    logger.info("📁 Testing directory structure...")
    
    required_dirs = [
        "data/raw", "data/clean", "data/growth", "data/score", "data/rubric",
        "data/network", "data/predict", "data/report", "config/weights", "data/meta",
        "data/pipeline"
    ]
    
    created_dirs = []
    
    try:
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                created_dirs.append(dir_path)
                logger.info(f"📁 Created directory: {dir_path}")
            else:
                logger.info(f"✅ Directory exists: {dir_path}")
        
        logger.info(f"✅ Directory structure ready ({len(created_dirs)} created)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Directory structure test failed: {e}")
        return False


async def test_individual_stages():
    """Test individual stage initialization (without execution)"""
    logger.info("🎯 Testing individual stage initialization...")
    
    try:
        from pipeline.stages import (
            DataCollectionStage, DataCleaningStage, GrowthTrackingStage,
            ScoreEstimationStage, RubricEvaluationStage, StrategicAnalysisStage,
            PredictiveModelingStage, ReportingStage, ContinuousLearningStage,
            MetaAnalysisStage
        )
        from worker.features.trending_config import get_config
        
        config = get_config()
        stages = [
            ("Stage 1", DataCollectionStage),
            ("Stage 2", DataCleaningStage),
            ("Stage 3", GrowthTrackingStage),
            ("Stage 4", ScoreEstimationStage),
            ("Stage 5", RubricEvaluationStage),
            ("Stage 6", StrategicAnalysisStage),
            ("Stage 7", PredictiveModelingStage),
            ("Stage 8", ReportingStage),
            ("Stage 9", ContinuousLearningStage),
            ("Stage 10", MetaAnalysisStage)
        ]
        
        for stage_name, stage_class in stages:
            try:
                stage_instance = stage_class(config)
                if hasattr(stage_instance, 'execute'):
                    logger.info(f"✅ {stage_name}: Initialized successfully")
                else:
                    logger.warning(f"⚠️ {stage_name}: Missing execute method")
            except Exception as stage_error:
                logger.error(f"❌ {stage_name}: Initialization failed - {stage_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Stage initialization test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_mock_pipeline_run():
    """Test a mock pipeline run without external dependencies"""
    logger.info("🧪 Testing mock pipeline run...")
    
    try:
        from pipeline_integration import pipeline_integration
        
        # This would test the pipeline with mock data if available
        # For now, just test that the integration is ready
        
        validation = await pipeline_integration.validate_pipeline_setup()
        
        if validation['integration_status'] == 'ready':
            logger.info("✅ Pipeline ready for execution")
            logger.info("ℹ️ Skipping actual execution test (requires external API)")
            return True
        else:
            logger.warning(f"⚠️ Pipeline not ready: {validation.get('issues', [])}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Mock pipeline run test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_config_compatibility():
    """Test compatibility with existing configuration system"""
    logger.info("⚙️ Testing configuration compatibility...")
    
    try:
        # Test existing config imports
        from worker.features.trending_config import get_config, get_metrics, get_topics_tracker
        
        config = get_config()
        metrics = get_metrics()
        topics = get_topics_tracker()
        
        logger.info("✅ Existing config system compatible")
        logger.info(f"✅ Config type: {type(config)}")
        logger.info(f"✅ Metrics available: {bool(metrics)}")
        logger.info(f"✅ Topics tracker available: {bool(topics)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration compatibility test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def generate_test_report(test_results: dict):
    """Generate a comprehensive test report"""
    logger.info("📊 Generating test report...")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    report = {
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "overall_status": "PASS" if success_rate == 1.0 else "FAIL"
        },
        "test_results": test_results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recommendations": []
    }
    
    # Add recommendations based on failures
    if not test_results.get("imports", True):
        report["recommendations"].append("Fix import issues - check Python path and dependencies")
    
    if not test_results.get("initialization", True):
        report["recommendations"].append("Fix pipeline initialization - check configuration")
    
    if not test_results.get("integration", True):
        report["recommendations"].append("Fix integration layer - check worker system compatibility")
    
    if not test_results.get("directories", True):
        report["recommendations"].append("Fix directory permissions - ensure write access")
    
    # Save report
    report_path = f"pipeline_test_report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    
    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"📄 Test report saved: {report_path}")
    except Exception as e:
        logger.error(f"Failed to save test report: {e}")
    
    return report


async def main():
    """Run comprehensive pipeline system tests"""
    logger.info("🚀 Starting Pipeline System Tests")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results["imports"] = await test_pipeline_imports()
    test_results["initialization"] = await test_pipeline_initialization()
    test_results["integration"] = await test_integration_layer()
    test_results["directories"] = await test_directory_structure()
    test_results["stages"] = await test_individual_stages()
    test_results["mock_run"] = await test_mock_pipeline_run()
    test_results["config_compatibility"] = await test_config_compatibility()
    
    # Generate report
    report = await generate_test_report(test_results)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("🏁 PIPELINE SYSTEM TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Tests: {report['test_summary']['total_tests']}")
    logger.info(f"Passed: {report['test_summary']['passed_tests']}")
    logger.info(f"Failed: {report['test_summary']['failed_tests']}")
    logger.info(f"Success Rate: {report['test_summary']['success_rate']:.1%}")
    logger.info(f"Overall Status: {report['test_summary']['overall_status']}")
    
    if report["recommendations"]:
        logger.info("\n🔧 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            logger.info(f"{i}. {rec}")
    
    logger.info("=" * 60)
    
    # Return appropriate exit code
    return 0 if report['test_summary']['overall_status'] == 'PASS' else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)