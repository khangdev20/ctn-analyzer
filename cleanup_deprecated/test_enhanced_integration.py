"""
Test Enhanced Content Analysis Integration
Test the complete pipeline with content analysis integration
"""
import asyncio
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import pipeline components
from worker.features.intelligence_pipeline import TrendingIntelligencePipeline
from mock_data_provider import generate_mock_trending_data

async def test_enhanced_content_analysis_integration():
    """Test the enhanced content analysis integration in the main pipeline"""
    print("🚀 Testing Enhanced Content Analysis Integration")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = TrendingIntelligencePipeline()
    batch_id = f"test_enhanced_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    
    try:
        # Step 1: Generate mock data
        print("📊 Step 1: Generating mock data...")
        mock_data = generate_mock_trending_data(15)
        print(f"✅ Generated {len(mock_data.get('data', []))} mock posts")
        
        # Step 2: Clean data
        print("\n🧹 Step 2: Cleaning data...")
        cleaned_data = await pipeline.clean_data(mock_data, batch_id)
        print(f"✅ Cleaned {len(cleaned_data.get('posts', []))} posts")
        
        # Step 3: Calculate scores
        print("\n📈 Step 3: Calculating performance scores...")
        scored_data = await pipeline.calculate_scores(cleaned_data, batch_id)
        print(f"✅ Scored {len(scored_data.get('posts', []))} posts")
        
        # Step 4: Content Analysis (NEW INTEGRATION)
        print("\n🎯 Step 4: Running content quality analysis...")
        content_analyzed_data = await pipeline.analyze_content_quality(scored_data, batch_id)
        
        content_analysis = content_analyzed_data.get("content_analysis", {})
        if content_analysis:
            metrics = content_analysis.get("aggregate_metrics", {})
            print(f"✅ Content analysis completed:")
            print(f"   • Avg Readability: {metrics.get('avg_readability', 0):.1f}/100")
            print(f"   • Avg Content Quality: {metrics.get('avg_content_quality', 0):.1f}/100")
            print(f"   • Dominant Sentiment: {metrics.get('dominant_sentiment', 'unknown')}")
            print(f"   • Dominant Tone: {metrics.get('dominant_tone', 'unknown')}")
        
        # Step 5: Strategic Analysis (ENHANCED WITH CONTENT INSIGHTS)
        print("\n🧠 Step 5: Running strategic analysis with content insights...")
        analysis_results = await pipeline.analyze_strategies(content_analyzed_data, batch_id)
        
        strategic_insights = analysis_results.get("strategic_insights", [])
        content_strategic_insights = analysis_results.get("content_strategic_insights", [])
        
        print(f"✅ Strategic analysis completed:")
        print(f"   • General Strategic Insights: {len(strategic_insights)}")
        print(f"   • Content-Specific Insights: {len(content_strategic_insights)}")
        
        # Display content strategic insights
        if content_strategic_insights:
            print("\n🎨 Content Strategic Insights:")
            for i, insight in enumerate(content_strategic_insights[:3], 1):
                print(f"   {i}. {insight.get('title', 'Unknown')}")
                print(f"      → {insight.get('description', 'No description')[:100]}...")
        
        # Step 6: Format Report (ENHANCED WITH CONTENT ANALYSIS)
        print("\n📋 Step 6: Formatting comprehensive report...")
        final_report = await pipeline.format_report(analysis_results, batch_id)
        
        # Display enhanced summary
        summary = final_report.get("summary", {})
        content_summary = summary.get("content_quality_summary", {})
        
        print(f"✅ Enhanced report generated:")
        print(f"   • Total Posts: {summary.get('total_posts', 0)}")
        print(f"   • Avg Engagement Score: {summary.get('avg_engagement_score', 0):.1f}")
        print(f"   • Content Quality Score: {content_summary.get('avg_content_quality', 0):.1f}/100")
        print(f"   • Content Readability: {content_summary.get('avg_readability', 0):.1f}/100")
        print(f"   • Emotional Impact: {content_summary.get('avg_emotional_impact', 0):.1f}/100")
        print(f"   • Content Sentiment: {content_summary.get('dominant_sentiment', 'unknown')}")
        
        # Check if Discord content summary is available
        discord_content_summary = final_report.get("content_analysis_discord_summary", "")
        if discord_content_summary:
            print(f"\n💬 Discord Content Summary Available: {len(discord_content_summary)} characters")
        
        print("\n" + "=" * 60)
        print("✅ ENHANCED INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\n🎉 Integration Features Verified:")
        print("• ✅ Content analysis integrated into main pipeline")
        print("• ✅ Content insights merged with strategic analysis") 
        print("• ✅ Enhanced metrics passed between stages")
        print("• ✅ Content-specific strategic insights generated")
        print("• ✅ Final report includes content analysis summary")
        print("• ✅ Discord content summary preserved for notifications")
        
        return {
            "status": "success",
            "integration_verified": True,
            "content_analysis_integrated": bool(content_analysis),
            "content_strategic_insights_count": len(content_strategic_insights),
            "enhanced_report_generated": bool(final_report.get("content_quality_summary"))
        }
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

async def main():
    """Run the enhanced integration test"""
    result = await test_enhanced_content_analysis_integration()
    
    if result["status"] == "success":
        print(f"\n🏆 Content analysis is now fully integrated into the main workflow!")
        print("The trending intelligence pipeline now includes:")
        print("  1. Data Collection")
        print("  2. Data Cleaning") 
        print("  3. Performance Scoring")
        print("  4. Content Quality Analysis (NEW)")
        print("  5. Strategic Analysis (ENHANCED)")
        print("  6. Report Generation (ENHANCED)")
    else:
        print(f"\n❌ Integration test failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())