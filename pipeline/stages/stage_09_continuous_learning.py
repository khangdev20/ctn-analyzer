# 🟩 Stage 9: Continuous Learning — Refine Rubric and Feature Weights

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import math

logger = logging.getLogger(__name__)


class ContinuousLearningStage:
    """
    Task: Adjust scoring model and rubric weights based on performance
    - Input: previous predictions vs actual trending outcomes
    - Output: updated weight config (config/weights/YYYY/MM/DD/rubric_weights.json)
    - Steps:
      1. Compare predicted vs actual trending
      2. Update feature importance (e.g., tone, velocity, tags)
      3. Save new weights with changelog
    - Return: new rubric weight dict and accuracy score
    """

    def __init__(self, config):
        self.config = config
        self.learning_rate = 0.1  # How quickly to adjust weights
        self.min_samples_for_learning = 10  # Minimum posts needed for learning

    async def execute(self, batch_id: str, report_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute continuous learning stage"""
        logger.info("🧠 Stage 9: Refining prediction model with continuous learning...")
        
        try:
            # Load historical data for comparison
            historical_data = await self._load_historical_data(batch_id)
            
            if not historical_data or len(historical_data) < self.min_samples_for_learning:
                logger.info("📊 Insufficient historical data for learning - returning baseline weights")
                return await self._create_baseline_weights(batch_id)
            
            # Evaluate prediction accuracy
            accuracy_analysis = await self._evaluate_prediction_accuracy(historical_data)
            
            # Update model weights based on performance
            updated_weights = await self._update_model_weights(accuracy_analysis)
            
            # Generate learning insights
            learning_insights = await self._generate_learning_insights(accuracy_analysis, updated_weights)
            
            # Create weight configuration
            weight_config = {
                "batch_id": batch_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "rubric_weights": updated_weights["rubric_weights"],
                "prediction_weights": updated_weights["prediction_weights"],
                "accuracy_metrics": accuracy_analysis,
                "learning_insights": learning_insights,
                "metadata": {
                    "learning_rate": self.learning_rate,
                    "samples_analyzed": len(historical_data),
                    "model_version": "adaptive_1.0"
                }
            }
            
            # Save updated weights
            output_path = await self._save_weight_config(weight_config, batch_id)
            
            # Generate summary
            summary = self._generate_summary(weight_config, batch_id)
            
            logger.info(f"✅ Stage 9 completed: Model weights updated based on {len(historical_data)} samples")
            logger.info(f"🎯 Prediction accuracy: {accuracy_analysis.get('overall_accuracy', 0):.1%}")
            
            return {
                **summary,
                "weight_config": weight_config,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"❌ Stage 9 error: {e}")
            return None

    async def _load_historical_data(self, current_batch_id: str) -> List[Dict]:
        """Load historical prediction data for comparison"""
        historical_posts = []
        
        try:
            # Look for prediction files from the last 7 days
            now = datetime.now(timezone.utc)
            
            for days_back in range(1, 8):  # Last 7 days
                search_date = now - timedelta(days=days_back)
                dir_path = f"data/predict/{search_date.year:04d}/{search_date.month:02d}/{search_date.day:02d}"
                
                if os.path.exists(dir_path):
                    # Find prediction files in this directory
                    prediction_files = [f for f in os.listdir(dir_path) if f.endswith('.predict.json')]
                    
                    for file in prediction_files:
                        file_path = os.path.join(dir_path, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            # Add posts with actual outcome simulation
                            posts = data.get("posts", [])
                            for post in posts:
                                # Simulate actual trending outcome based on current metrics
                                # In a real system, this would come from actual performance tracking
                                actual_outcome = await self._simulate_actual_outcome(post)
                                post["actual_trending"] = actual_outcome
                                post["prediction_date"] = search_date.isoformat()
                                historical_posts.append(post)
                                
                        except Exception as e:
                            logger.warning(f"Failed to load {file_path}: {e}")
                            continue
            
            logger.info(f"📊 Loaded {len(historical_posts)} historical predictions for learning")
            return historical_posts
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            return []

    async def _simulate_actual_outcome(self, post: Dict) -> Dict:
        """Simulate actual trending outcome based on post metrics"""
        # This simulates what would happen in a real system with actual tracking
        # In production, this would be replaced with real outcome data
        
        final_score = post.get("final_score", 0)
        trending_probability = post.get("trending_probability", 0)
        velocity = post.get("velocity_per_min", 0)
        engagement = post.get("total_engagement", 0)
        
        # Simulate actual trending based on weighted factors
        # Higher scores and velocity increase chance of actual trending
        trending_chance = (
            (final_score / 100) * 0.4 +
            trending_probability * 0.3 +
            min(1.0, velocity / 5) * 0.2 +
            min(1.0, engagement / 100) * 0.1
        )
        
        # Add some randomness to simulate real-world unpredictability
        import random
        random_factor = random.uniform(0.8, 1.2)
        trending_chance *= random_factor
        
        # Determine if post actually trended
        actually_trended = trending_chance > 0.6
        
        # Simulate engagement growth
        engagement_multiplier = random.uniform(1.0, 3.0) if actually_trended else random.uniform(0.5, 1.2)
        simulated_final_engagement = engagement * engagement_multiplier
        
        return {
            "actually_trended": actually_trended,
            "trending_score": min(1.0, trending_chance),
            "final_engagement": int(simulated_final_engagement),
            "engagement_growth": engagement_multiplier - 1.0
        }

    async def _evaluate_prediction_accuracy(self, historical_data: List[Dict]) -> Dict:
        """Evaluate how accurate previous predictions were"""
        
        correct_predictions = 0
        total_predictions = len(historical_data)
        
        # Detailed accuracy analysis
        high_prob_correct = 0
        high_prob_total = 0
        low_prob_correct = 0
        low_prob_total = 0
        
        feature_performance = {
            "final_score": {"correct": 0, "total": 0},
            "velocity": {"correct": 0, "total": 0},
            "engagement": {"correct": 0, "total": 0},
            "content_length": {"correct": 0, "total": 0},
            "tag_usage": {"correct": 0, "total": 0}
        }
        
        for post in historical_data:
            predicted_prob = post.get("trending_probability", 0)
            actual_outcome = post.get("actual_trending", {})
            actually_trended = actual_outcome.get("actually_trended", False)
            
            # Overall accuracy (>0.5 probability = predicted trending)
            predicted_trending = predicted_prob > 0.5
            if predicted_trending == actually_trended:
                correct_predictions += 1
            
            # High probability accuracy
            if predicted_prob >= 0.8:
                high_prob_total += 1
                if actually_trended:
                    high_prob_correct += 1
            
            # Low probability accuracy
            if predicted_prob <= 0.3:
                low_prob_total += 1
                if not actually_trended:
                    low_prob_correct += 1
            
            # Feature-specific performance analysis
            self._analyze_feature_performance(post, actually_trended, feature_performance)
        
        overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        high_prob_accuracy = high_prob_correct / high_prob_total if high_prob_total > 0 else 0
        low_prob_accuracy = low_prob_correct / low_prob_total if low_prob_total > 0 else 0
        
        return {
            "overall_accuracy": overall_accuracy,
            "high_probability_accuracy": high_prob_accuracy,
            "low_probability_accuracy": low_prob_accuracy,
            "total_samples": total_predictions,
            "correct_predictions": correct_predictions,
            "feature_performance": feature_performance,
            "accuracy_by_tier": self._calculate_accuracy_by_tier(historical_data)
        }

    def _analyze_feature_performance(self, post: Dict, actually_trended: bool, feature_performance: Dict):
        """Analyze performance of individual features"""
        
        # Final score performance
        final_score = post.get("final_score", 0)
        if final_score >= 70:
            feature_performance["final_score"]["total"] += 1
            if actually_trended:
                feature_performance["final_score"]["correct"] += 1
        
        # Velocity performance
        velocity = post.get("velocity_per_min", 0)
        if velocity > 2:
            feature_performance["velocity"]["total"] += 1
            if actually_trended:
                feature_performance["velocity"]["correct"] += 1
        
        # Engagement performance
        engagement = post.get("total_engagement", 0)
        if engagement > 20:
            feature_performance["engagement"]["total"] += 1
            if actually_trended:
                feature_performance["engagement"]["correct"] += 1
        
        # Content length performance
        content_length = post.get("content_length", 0)
        if 50 <= content_length <= 200:
            feature_performance["content_length"]["total"] += 1
            if actually_trended:
                feature_performance["content_length"]["correct"] += 1
        
        # Tag usage performance
        tag_count = post.get("tag_count", 0)
        if 1 <= tag_count <= 3:
            feature_performance["tag_usage"]["total"] += 1
            if actually_trended:
                feature_performance["tag_usage"]["correct"] += 1

    def _calculate_accuracy_by_tier(self, historical_data: List[Dict]) -> Dict:
        """Calculate accuracy for different prediction tiers"""
        tiers = {
            "Very High": {"correct": 0, "total": 0},
            "High": {"correct": 0, "total": 0},
            "Moderate": {"correct": 0, "total": 0},
            "Low": {"correct": 0, "total": 0}
        }
        
        for post in historical_data:
            tier = post.get("prediction_tier", "Unknown")
            if tier in tiers:
                tiers[tier]["total"] += 1
                
                actually_trended = post.get("actual_trending", {}).get("actually_trended", False)
                predicted_trending = post.get("trending_probability", 0) > 0.5
                
                if predicted_trending == actually_trended:
                    tiers[tier]["correct"] += 1
        
        # Calculate accuracy rates
        accuracy_by_tier = {}
        for tier, data in tiers.items():
            if data["total"] > 0:
                accuracy_by_tier[tier] = data["correct"] / data["total"]
            else:
                accuracy_by_tier[tier] = 0
        
        return accuracy_by_tier

    async def _update_model_weights(self, accuracy_analysis: Dict) -> Dict:
        """Update model weights based on accuracy analysis"""
        
        # Current weights (baseline)
        current_rubric_weights = {
            'content_quality': 0.30,
            'engagement': 0.25,
            'timing_trend': 0.20,
            'network_amplification': 0.15,
            'strategy_crafting': 0.10
        }
        
        current_prediction_weights = {
            'final_score': 0.25,
            'velocity': 0.20,
            'growth_rate': 0.15,
            'engagement_ratio': 0.15,
            'timing_factor': 0.10,
            'network_factor': 0.10,
            'content_factor': 0.05
        }
        
        # Adjust weights based on feature performance
        feature_performance = accuracy_analysis.get("feature_performance", {})
        
        # Calculate adjustment factors
        adjustments = {}
        for feature, performance in feature_performance.items():
            if performance["total"] > 0:
                accuracy_rate = performance["correct"] / performance["total"]
                # If accuracy is high, increase weight; if low, decrease weight
                adjustment_factor = 1 + (accuracy_rate - 0.5) * self.learning_rate
                adjustments[feature] = adjustment_factor
            else:
                adjustments[feature] = 1.0
        
        # Apply adjustments to prediction weights
        updated_prediction_weights = current_prediction_weights.copy()
        
        if "final_score" in adjustments:
            updated_prediction_weights["final_score"] *= adjustments["final_score"]
        
        if "velocity" in adjustments:
            updated_prediction_weights["velocity"] *= adjustments["velocity"]
        
        if "engagement" in adjustments:
            updated_prediction_weights["engagement_ratio"] *= adjustments["engagement"]
        
        # Normalize weights to sum to 1
        total_prediction_weight = sum(updated_prediction_weights.values())
        for key in updated_prediction_weights:
            updated_prediction_weights[key] /= total_prediction_weight
        
        # Adjust rubric weights based on overall accuracy
        overall_accuracy = accuracy_analysis.get("overall_accuracy", 0.5)
        
        # If overall accuracy is low, adjust rubric weights
        updated_rubric_weights = current_rubric_weights.copy()
        if overall_accuracy < 0.6:
            # Increase weight of better-performing components
            if "velocity" in adjustments and adjustments["velocity"] > 1.0:
                updated_rubric_weights["timing_trend"] *= 1.1
            if "engagement" in adjustments and adjustments["engagement"] > 1.0:
                updated_rubric_weights["engagement"] *= 1.1
        
        # Normalize rubric weights
        total_rubric_weight = sum(updated_rubric_weights.values())
        for key in updated_rubric_weights:
            updated_rubric_weights[key] /= total_rubric_weight
        
        return {
            "rubric_weights": updated_rubric_weights,
            "prediction_weights": updated_prediction_weights,
            "adjustments_applied": adjustments
        }

    async def _generate_learning_insights(self, accuracy_analysis: Dict, updated_weights: Dict) -> List[Dict]:
        """Generate insights from the learning process"""
        insights = []
        
        # Overall accuracy insight
        overall_accuracy = accuracy_analysis.get("overall_accuracy", 0)
        insights.append({
            "type": "accuracy_assessment",
            "insight": f"Model achieved {overall_accuracy:.1%} overall prediction accuracy",
            "recommendation": "Continue monitoring and adjusting" if overall_accuracy > 0.6 else "Consider additional feature engineering"
        })
        
        # Feature performance insights
        feature_performance = accuracy_analysis.get("feature_performance", {})
        best_features = []
        worst_features = []
        
        for feature, performance in feature_performance.items():
            if performance["total"] > 0:
                accuracy = performance["correct"] / performance["total"]
                if accuracy > 0.7:
                    best_features.append((feature, accuracy))
                elif accuracy < 0.4:
                    worst_features.append((feature, accuracy))
        
        if best_features:
            best_feature_names = [f[0] for f in sorted(best_features, key=lambda x: x[1], reverse=True)]
            insights.append({
                "type": "strong_features",
                "insight": f"Strongest predictive features: {', '.join(best_feature_names[:3])}",
                "recommendation": "Maintain focus on these high-performing indicators"
            })
        
        if worst_features:
            worst_feature_names = [f[0] for f in sorted(worst_features, key=lambda x: x[1])]
            insights.append({
                "type": "weak_features", 
                "insight": f"Underperforming features: {', '.join(worst_feature_names[:3])}",
                "recommendation": "Consider alternative metrics or feature engineering"
            })
        
        # Weight adjustment insights
        adjustments = updated_weights.get("adjustments_applied", {})
        significant_adjustments = {k: v for k, v in adjustments.items() if abs(v - 1.0) > 0.05}
        
        if significant_adjustments:
            insights.append({
                "type": "weight_adjustments",
                "insight": f"Significant weight changes made to: {', '.join(significant_adjustments.keys())}",
                "recommendation": "Monitor impact of these adjustments in future predictions"
            })
        
        return insights

    async def _create_baseline_weights(self, batch_id: str) -> Dict:
        """Create baseline weight configuration when insufficient data"""
        
        baseline_config = {
            "batch_id": batch_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "rubric_weights": {
                'content_quality': 0.30,
                'engagement': 0.25,
                'timing_trend': 0.20,
                'network_amplification': 0.15,
                'strategy_crafting': 0.10
            },
            "prediction_weights": {
                'final_score': 0.25,
                'velocity': 0.20,
                'growth_rate': 0.15,
                'engagement_ratio': 0.15,
                'timing_factor': 0.10,
                'network_factor': 0.10,
                'content_factor': 0.05
            },
            "accuracy_metrics": {
                "overall_accuracy": 0,
                "note": "Baseline weights - insufficient historical data for learning"
            },
            "learning_insights": [
                {
                    "type": "initialization",
                    "insight": "Using baseline weights due to insufficient historical data",
                    "recommendation": "Continue collecting data for future model improvements"
                }
            ],
            "metadata": {
                "learning_rate": self.learning_rate,
                "samples_analyzed": 0,
                "model_version": "baseline_1.0"
            }
        }
        
        # Save baseline weights
        output_path = await self._save_weight_config(baseline_config, batch_id)
        
        return {
            "batch_id": batch_id,
            "new_rubric_weights": baseline_config["rubric_weights"],
            "accuracy_score": 0,
            "learning_status": "baseline_initialization",
            "weight_config": baseline_config,
            "output_path": output_path
        }

    async def _save_weight_config(self, config: Dict, batch_id: str) -> str:
        """Save weight configuration to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"config/weights/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/rubric_weights_{batch_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, weight_config: Dict, batch_id: str) -> Dict:
        """Generate summary as specified in AI Agent Prompts"""
        accuracy_metrics = weight_config.get("accuracy_metrics", {})
        
        return {
            "batch_id": batch_id,
            "new_rubric_weights": weight_config.get("rubric_weights", {}),
            "accuracy_score": accuracy_metrics.get("overall_accuracy", 0),
            "learning_insights": weight_config.get("learning_insights", []),
            "samples_analyzed": weight_config.get("metadata", {}).get("samples_analyzed", 0),
            "learning_status": "weights_updated" if accuracy_metrics.get("overall_accuracy", 0) > 0 else "baseline_initialized",
            "performance_improvement": {
                "high_confidence_accuracy": accuracy_metrics.get("high_probability_accuracy", 0),
                "feature_improvements": len([i for i in weight_config.get("learning_insights", []) if i.get("type") == "strong_features"]),
                "weight_adjustments": len(weight_config.get("adjustments_applied", {}))
            }
        }