"""
Content Analysis Task
Specialized task for running comprehensive content analysis with Discord reporting
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from worker.features.content_analyzer import ContentAnalyzer
from worker.features.content_analysis_prompts import ContentAnalysisPromptHandler
from worker.features.data_collector import collect_trending_data
from notifiers.discord_webhook_sender import send_discord_message_webhook
from mock_data_provider import generate_mock_trending_data

logger = logging.getLogger(__name__)


class ContentAnalysisTask:
    """Specialized task for content analysis with Discord integration"""
    
    def __init__(self):
        self.content_analyzer = ContentAnalyzer()
        self.prompt_handler = ContentAnalysisPromptHandler()
        self.batch_id = None
        
    def generate_batch_id(self) -> str:
        """Generate unique batch ID for this analysis"""
        now = datetime.now(timezone.utc)
        return f"content_analysis_{now.strftime('%Y%m%dT%H%MZ')}"
    
    async def run_content_analysis_workflow(self, data_source: str = "api", num_posts: int = 25) -> Dict:
        """
        Run complete content analysis workflow with Discord reporting
        
        Args:
            data_source: "api" for real data, "mock" for test data
            num_posts: Number of posts to analyze (default 25)
            
        Returns:
            Dictionary with analysis results and Discord message status
        """
        self.batch_id = self.generate_batch_id()
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"[CONTENT_ANALYSIS] Starting workflow - Batch: {self.batch_id}")
        logger.info(f"[SETTINGS] Data source: {data_source}, Posts: {num_posts}")
        
        try:
            # Step 1: Collect Data
            logger.info("[STEP1] Collecting social media data...")
            posts_data = await self._collect_posts_data(data_source, num_posts)
            
            if not posts_data:
                logger.error("[ERROR] No data collected for analysis")
                return {
                    "status": "failed",
                    "error": "No data available for analysis",
                    "batch_id": self.batch_id
                }
            
            logger.info(f"[SUCCESS] Collected {len(posts_data)} posts for analysis")
            
            # Step 2: Run Content Analysis
            logger.info("[STEP2] Running comprehensive content analysis...")
            analysis_results = await self.content_analyzer.analyze_content_batch(posts_data)
            
            if not analysis_results.get("analyzed_posts"):
                logger.error("[ERROR] Content analysis failed")
                return {
                    "status": "failed", 
                    "error": "Content analysis produced no results",
                    "batch_id": self.batch_id
                }
            
            # Step 3: Generate Discord Report
            logger.info("[STEP3] Generating Discord-ready content report...")
            discord_report = await self.prompt_handler.generate_content_analysis_discord_report(posts_data)
            
            # Step 4: Send to Discord
            logger.info("[STEP4] Sending report to Discord...")
            discord_success = await self._send_discord_report(discord_report)
            
            # Step 5: Save Results
            await self._save_analysis_results(analysis_results, posts_data)
            
            # Calculate final metrics
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            analyzed_count = len(analysis_results.get("analyzed_posts", []))
            
            result = {
                "status": "success",
                "batch_id": self.batch_id,
                "processing_time_seconds": processing_time,
                "total_posts_collected": len(posts_data),
                "posts_analyzed": analyzed_count,
                "discord_sent": discord_success,
                "analysis_summary": {
                    "avg_readability": analysis_results.get("aggregate_metrics", {}).get("avg_readability", 0),
                    "avg_content_quality": analysis_results.get("aggregate_metrics", {}).get("avg_content_quality", 0),
                    "dominant_sentiment": analysis_results.get("aggregate_metrics", {}).get("dominant_sentiment", "unknown"),
                    "top_emotions": analysis_results.get("aggregate_metrics", {}).get("top_emotions", [])
                }
            }
            
            logger.info(f"[SUCCESS] Content analysis workflow completed in {processing_time:.1f}s")
            return result
            
        except Exception as e:
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"[ERROR] Content analysis workflow failed after {processing_time:.1f}s: {e}")
            
            return {
                "status": "error",
                "batch_id": self.batch_id,
                "error": str(e),
                "processing_time_seconds": processing_time
            }
    
    async def _collect_posts_data(self, data_source: str, num_posts: int) -> List[Dict]:
        """Collect posts data from specified source"""
        try:
            if data_source == "mock":
                logger.info("[MOCK] Using mock data for content analysis")
                mock_data = generate_mock_trending_data(num_posts)
                return mock_data.get("data", [])
            else:
                logger.info("[API] Collecting real data from API")
                # Try to collect real data
                def collect_data():
                    return collect_trending_data(num_pages=max(1, num_posts // 10), key='trending')
                
                loop = asyncio.get_event_loop()
                filename = await loop.run_in_executor(None, collect_data)
                
                if filename and os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    posts = data.get('data', [])
                    if posts:
                        logger.info(f"[SUCCESS] Collected {len(posts)} posts from API")
                        return posts[:num_posts]  # Limit to requested number
                
                # Fallback to mock data if API fails
                logger.warning("[FALLBACK] API failed, using mock data")
                mock_data = generate_mock_trending_data(num_posts)
                return mock_data.get("data", [])
                
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            # Final fallback to mock data
            try:
                mock_data = generate_mock_trending_data(num_posts)
                return mock_data.get("data", [])
            except:
                return []
    
    async def _send_discord_report(self, discord_report: str) -> bool:
        """Send content analysis report to Discord"""
        try:
            if not discord_report:
                logger.warning("[DISCORD] No report content to send")
                return False
            
            # Truncate report if too long for Discord (2000 char limit)
            if len(discord_report) > 1800:  # Leave room for header
                discord_report = discord_report[:1800] + "...\n*[Report truncated]*"
            
            # Add header to identify this as a content analysis report
            enhanced_report = f"""🤖 **AI Content Analysis Report**

{discord_report}

*Report ID: {self.batch_id}*"""
            
            # Send to Discord
            def send_message():
                return send_discord_message_webhook(enhanced_report)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, send_message)
            
            if result:
                logger.info("[DISCORD] Content analysis report sent successfully")
                return True
            else:
                logger.error("[DISCORD] Failed to send content analysis report")
                return False
                
        except Exception as e:
            logger.error(f"Discord sending failed: {e}")
            return False
    
    async def _save_analysis_results(self, analysis_results: Dict, posts_data: List[Dict]):
        """Save analysis results to file system"""
        try:
            now = datetime.now(timezone.utc)
            dir_path = f"data/reports/content_analysis/{now.year:04d}/{now.month:02d}/{now.day:02d}"
            os.makedirs(dir_path, exist_ok=True)
            
            # Prepare comprehensive report
            report_data = {
                "batch_id": self.batch_id,
                "analysis_type": "content_analysis",
                "timestamp": now.isoformat(),
                "metadata": {
                    "total_posts": len(posts_data),
                    "analyzed_posts": len(analysis_results.get("analyzed_posts", [])),
                    "analysis_success_rate": len(analysis_results.get("analyzed_posts", [])) / max(1, len(posts_data))
                },
                "analysis_results": analysis_results,
                "raw_posts_sample": posts_data[:5]  # Save sample for reference
            }
            
            # Save main report
            report_file = f"{dir_path}/{self.batch_id}_content_analysis.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[SAVED] Analysis results saved to: {report_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save analysis results: {e}")
    
    async def run_sentiment_analysis_only(self, posts_data: List[Dict]) -> Dict:
        """Run only sentiment analysis for quick insights"""
        try:
            logger.info(f"[SENTIMENT] Running sentiment analysis on {len(posts_data)} posts")
            
            # Use the content analyzer for sentiment analysis
            analysis_results = await self.content_analyzer.analyze_content_batch(posts_data)
            
            # Extract sentiment-specific insights
            sentiment_summary = {
                "total_posts": len(posts_data),
                "sentiment_distribution": analysis_results.get("aggregate_metrics", {}).get("sentiment_distribution", {}),
                "dominant_sentiment": analysis_results.get("aggregate_metrics", {}).get("dominant_sentiment", "unknown"),
                "top_emotions": analysis_results.get("aggregate_metrics", {}).get("top_emotions", []),
                "avg_emotional_impact": analysis_results.get("aggregate_metrics", {}).get("avg_emotional_impact", 0)
            }
            
            # Generate specialized sentiment report
            sentiment_report = await self.prompt_handler.generate_sentiment_analysis_prompt(posts_data)
            
            return {
                "status": "success",
                "sentiment_summary": sentiment_summary,
                "llm_sentiment_analysis": sentiment_report,
                "batch_id": self.batch_id
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"status": "error", "error": str(e)}


# Task runner function for scheduler integration
async def run_content_analysis_task(worker):
    """Main content analysis task runner for scheduler"""
    task_id = f"content_analysis_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)
    
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info(f"[START] CONTENT ANALYSIS TASK STARTED")
    logger.info(f"[TASK] Task ID: {task_id}")
    logger.info(f"[TIME] Start time: {start_time.isoformat()}")
    logger.info("=" * 60)
    
    try:
        task = ContentAnalysisTask()
        
        # Run content analysis workflow with real data
        result = await task.run_content_analysis_workflow(data_source="api", num_posts=20)
        
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        if result["status"] == "success":
            logger.info("[SUCCESS]" * 6)
            logger.info(f"[SUCCESS] CONTENT ANALYSIS COMPLETED")
            logger.info(f"[TIME] Total execution time: {execution_time:.2f}s")
            logger.info(f"[ANALYZED] Posts analyzed: {result.get('posts_analyzed', 0)}")
            logger.info(f"[DISCORD] Discord sent: {result.get('discord_sent', False)}")
            logger.info("[SUCCESS]" * 6)
        else:
            logger.error(f"[FAILED] Content analysis failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.error("[ERROR]" * 6)
        logger.error(f"[FAILED] CONTENT ANALYSIS TASK FAILED")
        logger.error(f"[TIME] Failed after: {execution_time:.2f}s")
        logger.error(f"[ERROR] Error: {str(e)}")
        logger.error("[ERROR]" * 6)
        
        return {"status": "error", "error": str(e), "task_id": task_id}
        
    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)
            logger.info(f"[REMOVED] Removed {task_id} from active tasks")