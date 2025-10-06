# 🟪 Stage 6: Strategic & Network Analysis — Detect Patterns and Clusters

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import math

logger = logging.getLogger(__name__)


class StrategicAnalysisStage:
    """
    Task: Identify strategy patterns, clusters, and narrative groups
    - Input: rubric results + tag and author data
    - Output: network JSON file (data/network/YYYY/MM/DD/batch_<timestamp>.network.json)
    - Steps:
      1. Build hashtag co-occurrence graph
      2. Detect author clusters using cosine similarity
      3. Find top tags driving engagement velocity
      4. Analyze post timing vs engagement correlation
    - Return: top_tags, tag_clusters, author_groups
    """

    def __init__(self, config):
        self.config = config

    async def execute(self, batch_id: str, rubric_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute strategic and network analysis stage"""
        logger.info("🧠 Stage 6: Analyzing content strategies and patterns...")
        
        try:
            posts = rubric_data.get("posts", [])
            
            # 1. Build hashtag co-occurrence graph
            hashtag_network = await self._build_hashtag_cooccurrence_graph(posts)
            
            # 2. Detect author clusters using similarity
            author_clusters = await self._detect_author_clusters(posts)
            
            # 3. Find top tags driving engagement velocity
            top_velocity_tags = await self._find_top_velocity_tags(posts)
            
            # 4. Analyze timing vs engagement correlation
            timing_analysis = await self._analyze_timing_engagement_correlation(posts)
            
            # 5. Identify content strategy patterns
            strategy_patterns = await self._identify_strategy_patterns(posts)
            
            # 6. Network influence analysis
            influence_network = await self._analyze_influence_network(posts)
            
            # Create network analysis data structure
            network_data = {
                "batch_id": batch_id,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "hashtag_network": hashtag_network,
                "author_clusters": author_clusters,
                "top_velocity_tags": top_velocity_tags,
                "timing_analysis": timing_analysis,
                "strategy_patterns": strategy_patterns,
                "influence_network": influence_network,
                "metadata": {
                    "total_posts": len(posts),
                    "unique_authors": len(set(p.get("author") for p in posts if p.get("author"))),
                    "unique_tags": len(set(tag for p in posts for tag in p.get("tags", []))),
                    "analysis_version": "1.0"
                }
            }
            
            # Save network data
            output_path = await self._save_network_data(network_data, batch_id)
            
            # Generate summary
            summary = self._generate_summary(network_data, batch_id)
            
            logger.info(f"✅ Stage 6 completed: Strategic analysis for {len(posts)} posts")
            logger.info(f"🏷️ Top tags: {[tag['tag'] for tag in summary['top_tags'][:3]]}")
            logger.info(f"👥 Author clusters: {len(summary['author_groups'])}")
            
            return {
                **summary,
                "network_data": network_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"❌ Stage 6 error: {e}")
            return None

    async def _build_hashtag_cooccurrence_graph(self, posts: List[Dict]) -> Dict:
        """Build hashtag co-occurrence graph to find related tags"""
        cooccurrence = defaultdict(Counter)
        tag_stats = Counter()
        
        # Count tag occurrences and co-occurrences
        for post in posts:
            tags = post.get("tags", [])
            if not tags:
                continue
                
            # Count individual tags
            for tag in tags:
                tag_stats[tag] += 1
            
            # Count co-occurrences
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    cooccurrence[tag1][tag2] += 1
                    cooccurrence[tag2][tag1] += 1
        
        # Build graph structure
        tag_pairs = []
        for tag1, related_tags in cooccurrence.items():
            for tag2, count in related_tags.most_common(5):  # Top 5 related tags
                if count > 1:  # Minimum co-occurrence threshold
                    tag_pairs.append({
                        "tag1": tag1,
                        "tag2": tag2,
                        "cooccurrence_count": count,
                        "strength": count / min(tag_stats[tag1], tag_stats[tag2])  # Normalized strength
                    })
        
        # Find tag clusters (simple community detection)
        tag_clusters = self._detect_tag_clusters(cooccurrence, tag_stats)
        
        return {
            "nodes": [{"tag": tag, "frequency": count, "centrality": self._calculate_tag_centrality(tag, cooccurrence)} 
                     for tag, count in tag_stats.most_common(20)],
            "edges": sorted(tag_pairs, key=lambda x: x["strength"], reverse=True)[:50],
            "clusters": tag_clusters
        }

    async def _detect_author_clusters(self, posts: List[Dict]) -> Dict:
        """Detect author clusters using content similarity and engagement patterns"""
        author_profiles = defaultdict(lambda: {
            "posts": [],
            "tags": Counter(),
            "avg_engagement": 0,
            "avg_final_score": 0,
            "content_themes": []
        })
        
        # Build author profiles
        for post in posts:
            author = post.get("author")
            if not author or author == "unknown":
                continue
                
            profile = author_profiles[author]
            profile["posts"].append(post)
            
            # Aggregate tags
            for tag in post.get("tags", []):
                profile["tags"][tag] += 1
            
            # Content themes (simplified)
            content = post.get("content", "").lower()
            themes = self._extract_content_themes(content)
            profile["content_themes"].extend(themes)
        
        # Calculate profile metrics
        for author, profile in author_profiles.items():
            posts_count = len(profile["posts"])
            if posts_count == 0:
                continue
                
            total_engagement = sum(p.get("total_engagement", 0) for p in profile["posts"])
            total_score = sum(p.get("final_score", 0) for p in profile["posts"])
            
            profile["avg_engagement"] = total_engagement / posts_count
            profile["avg_final_score"] = total_score / posts_count
            profile["posts_count"] = posts_count
            profile["top_tags"] = [tag for tag, count in profile["tags"].most_common(5)]
            profile["content_themes"] = list(set(profile["content_themes"]))
        
        # Cluster authors by similarity
        clusters = self._cluster_authors_by_similarity(author_profiles)
        
        return {
            "author_profiles": {author: {
                "posts_count": profile["posts_count"],
                "avg_engagement": round(profile["avg_engagement"], 2),
                "avg_final_score": round(profile["avg_final_score"], 2),
                "top_tags": profile["top_tags"],
                "content_themes": profile["content_themes"][:3]
            } for author, profile in author_profiles.items() if profile["posts_count"] > 0},
            "clusters": clusters
        }

    async def _find_top_velocity_tags(self, posts: List[Dict]) -> List[Dict]:
        """Find hashtags that drive the highest engagement velocity"""
        tag_metrics = defaultdict(lambda: {
            "total_velocity": 0,
            "post_count": 0,
            "total_engagement": 0,
            "total_score": 0
        })
        
        # Aggregate metrics by tag
        for post in posts:
            velocity = post.get("velocity_per_min", 0)
            engagement = post.get("total_engagement", 0)
            score = post.get("final_score", 0)
            
            for tag in post.get("tags", []):
                metrics = tag_metrics[tag]
                metrics["total_velocity"] += velocity
                metrics["total_engagement"] += engagement
                metrics["total_score"] += score
                metrics["post_count"] += 1
        
        # Calculate averages and rank
        top_tags = []
        for tag, metrics in tag_metrics.items():
            if metrics["post_count"] < 2:  # Minimum sample size
                continue
                
            avg_velocity = metrics["total_velocity"] / metrics["post_count"]
            avg_engagement = metrics["total_engagement"] / metrics["post_count"]
            avg_score = metrics["total_score"] / metrics["post_count"]
            
            top_tags.append({
                "tag": tag,
                "avg_velocity": round(avg_velocity, 2),
                "avg_engagement": round(avg_engagement, 2),
                "avg_score": round(avg_score, 2),
                "post_count": metrics["post_count"],
                "velocity_score": avg_velocity * math.log(metrics["post_count"])  # Weighted by frequency
            })
        
        # Sort by velocity score
        return sorted(top_tags, key=lambda x: x["velocity_score"], reverse=True)[:15]

    async def _analyze_timing_engagement_correlation(self, posts: List[Dict]) -> Dict:
        """Analyze correlation between posting time and engagement"""
        hourly_metrics = defaultdict(lambda: {
            "posts": [],
            "total_engagement": 0,
            "total_velocity": 0,
            "total_score": 0,
            "count": 0
        })
        
        # Group posts by hour
        for post in posts:
            created_at = post.get("created_at")
            if not created_at:
                continue
                
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                hour = dt.hour
                
                metrics = hourly_metrics[hour]
                metrics["posts"].append(post)
                metrics["total_engagement"] += post.get("total_engagement", 0)
                metrics["total_velocity"] += post.get("velocity_per_min", 0)
                metrics["total_score"] += post.get("final_score", 0)
                metrics["count"] += 1
                
            except:
                continue
        
        # Calculate hourly averages
        hourly_analysis = []
        for hour in range(24):
            metrics = hourly_metrics[hour]
            if metrics["count"] == 0:
                continue
                
            hourly_analysis.append({
                "hour": hour,
                "posts_count": metrics["count"],
                "avg_engagement": round(metrics["total_engagement"] / metrics["count"], 2),
                "avg_velocity": round(metrics["total_velocity"] / metrics["count"], 2),
                "avg_score": round(metrics["total_score"] / metrics["count"], 2)
            })
        
        # Find peak hours
        peak_engagement_hour = max(hourly_analysis, key=lambda x: x["avg_engagement"]) if hourly_analysis else None
        peak_velocity_hour = max(hourly_analysis, key=lambda x: x["avg_velocity"]) if hourly_analysis else None
        
        return {
            "hourly_breakdown": sorted(hourly_analysis, key=lambda x: x["hour"]),
            "peak_engagement_hour": peak_engagement_hour,
            "peak_velocity_hour": peak_velocity_hour,
            "optimal_posting_windows": self._find_optimal_posting_windows(hourly_analysis)
        }

    async def _identify_strategy_patterns(self, posts: List[Dict]) -> Dict:
        """Identify common content strategy patterns"""
        patterns = {
            "high_performers": {"posts": [], "common_traits": []},
            "viral_candidates": {"posts": [], "common_traits": []},
            "engagement_magnets": {"posts": [], "common_traits": []},
            "content_types": defaultdict(list)
        }
        
        # Categorize posts
        for post in posts:
            final_score = post.get("final_score", 0)
            classification = post.get("classification", "")
            
            # High performers (top 20%)
            if final_score >= 70:
                patterns["high_performers"]["posts"].append(post)
            
            # Viral candidates
            if classification == "Trending":
                patterns["viral_candidates"]["posts"].append(post)
            
            # Engagement magnets (high reply ratio)
            reply_count = post.get("reply_count", 0)
            total_engagement = post.get("total_engagement", 1)
            if reply_count / total_engagement > 0.2:
                patterns["engagement_magnets"]["posts"].append(post)
            
            # Content type analysis
            content_type = self._classify_content_type(post)
            patterns["content_types"][content_type].append(post)
        
        # Analyze common traits
        patterns["high_performers"]["common_traits"] = self._analyze_common_traits(patterns["high_performers"]["posts"])
        patterns["viral_candidates"]["common_traits"] = self._analyze_common_traits(patterns["viral_candidates"]["posts"])
        patterns["engagement_magnets"]["common_traits"] = self._analyze_common_traits(patterns["engagement_magnets"]["posts"])
        
        return {
            "high_performers": {
                "count": len(patterns["high_performers"]["posts"]),
                "common_traits": patterns["high_performers"]["common_traits"]
            },
            "viral_candidates": {
                "count": len(patterns["viral_candidates"]["posts"]),
                "common_traits": patterns["viral_candidates"]["common_traits"]
            },
            "engagement_magnets": {
                "count": len(patterns["engagement_magnets"]["posts"]),
                "common_traits": patterns["engagement_magnets"]["common_traits"]
            },
            "content_type_distribution": {content_type: len(posts) for content_type, posts in patterns["content_types"].items()}
        }

    async def _analyze_influence_network(self, posts: List[Dict]) -> Dict:
        """Analyze influence network based on mentions and interactions"""
        mention_network = defaultdict(Counter)
        author_influence = defaultdict(lambda: {
            "mentioned_by": set(),
            "mentions": set(),
            "total_engagement": 0,
            "influence_score": 0
        })
        
        # Build mention network
        for post in posts:
            author = post.get("author", "unknown")
            content = post.get("content", "")
            engagement = post.get("total_engagement", 0)
            
            # Extract mentions
            import re
            mentions = re.findall(r'@(\w+)', content.lower())
            
            for mentioned in mentions:
                mention_network[author][mentioned] += 1
                author_influence[author]["mentions"].add(mentioned)
                author_influence[mentioned]["mentioned_by"].add(author)
            
            author_influence[author]["total_engagement"] += engagement
        
        # Calculate influence scores
        for author, data in author_influence.items():
            mentions_received = len(data["mentioned_by"])
            mentions_given = len(data["mentions"])
            engagement = data["total_engagement"]
            
            # Simple influence score: engagement + network centrality
            data["influence_score"] = engagement + mentions_received * 10 - mentions_given * 2
        
        # Get top influencers
        top_influencers = sorted(
            [(author, data) for author, data in author_influence.items() if data["influence_score"] > 0],
            key=lambda x: x[1]["influence_score"],
            reverse=True
        )[:10]
        
        return {
            "mention_relationships": dict(mention_network),
            "top_influencers": [
                {
                    "author": author,
                    "influence_score": data["influence_score"],
                    "mentions_received": len(data["mentioned_by"]),
                    "total_engagement": data["total_engagement"]
                }
                for author, data in top_influencers
            ],
            "network_density": len(mention_network) / max(1, len(author_influence)),
            "total_mentions": sum(sum(mentions.values()) for mentions in mention_network.values())
        }

    def _detect_tag_clusters(self, cooccurrence: Dict, tag_stats: Counter) -> List[Dict]:
        """Simple tag clustering based on co-occurrence strength"""
        clusters = []
        processed_tags = set()
        
        for tag, related in cooccurrence.items():
            if tag in processed_tags:
                continue
                
            # Find strongly related tags
            cluster_tags = [tag]
            for related_tag, count in related.most_common(3):
                strength = count / min(tag_stats[tag], tag_stats[related_tag])
                if strength > 0.3 and related_tag not in processed_tags:
                    cluster_tags.append(related_tag)
            
            if len(cluster_tags) > 1:
                clusters.append({
                    "cluster_id": len(clusters),
                    "tags": cluster_tags,
                    "size": len(cluster_tags),
                    "total_frequency": sum(tag_stats[t] for t in cluster_tags)
                })
                processed_tags.update(cluster_tags)
        
        return sorted(clusters, key=lambda x: x["total_frequency"], reverse=True)

    def _calculate_tag_centrality(self, tag: str, cooccurrence: Dict) -> float:
        """Calculate centrality of a tag in the co-occurrence network"""
        if tag not in cooccurrence:
            return 0
        
        # Simple degree centrality (number of connections)
        return len(cooccurrence[tag])

    def _extract_content_themes(self, content: str) -> List[str]:
        """Extract content themes (simplified keyword analysis)"""
        themes = []
        
        # Business/tech themes
        if any(word in content for word in ['business', 'startup', 'tech', 'innovation']):
            themes.append('business_tech')
        
        # Personal/lifestyle themes
        if any(word in content for word in ['life', 'personal', 'experience', 'journey']):
            themes.append('personal_lifestyle')
        
        # News/current events
        if any(word in content for word in ['news', 'breaking', 'update', 'report']):
            themes.append('news_current_events')
        
        # Entertainment
        if any(word in content for word in ['funny', 'lol', 'entertainment', 'meme']):
            themes.append('entertainment')
        
        return themes

    def _cluster_authors_by_similarity(self, author_profiles: Dict) -> List[Dict]:
        """Cluster authors by content and engagement similarity"""
        # Simplified clustering based on common tags and themes
        clusters = []
        processed_authors = set()
        
        authors_list = list(author_profiles.keys())
        for i, author1 in enumerate(authors_list):
            if author1 in processed_authors:
                continue
                
            cluster = [author1]
            profile1 = author_profiles[author1]
            
            for author2 in authors_list[i+1:]:
                if author2 in processed_authors:
                    continue
                    
                profile2 = author_profiles[author2]
                similarity = self._calculate_author_similarity(profile1, profile2)
                
                if similarity > 0.3:  # Similarity threshold
                    cluster.append(author2)
            
            if len(cluster) > 1:
                clusters.append({
                    "cluster_id": len(clusters),
                    "authors": cluster,
                    "size": len(cluster),
                    "common_tags": self._find_common_tags([author_profiles[author]["tags"] for author in cluster])
                })
                processed_authors.update(cluster)
        
        return clusters

    def _calculate_author_similarity(self, profile1: Dict, profile2: Dict) -> float:
        """Calculate similarity between two author profiles"""
        # Tag similarity (Jaccard similarity)
        tags1 = set(profile1["tags"].keys())
        tags2 = set(profile2["tags"].keys())
        
        if not tags1 and not tags2:
            tag_similarity = 0
        else:
            tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
        
        # Theme similarity
        themes1 = set(profile1["content_themes"])
        themes2 = set(profile2["content_themes"])
        
        if not themes1 and not themes2:
            theme_similarity = 0
        else:
            theme_similarity = len(themes1.intersection(themes2)) / len(themes1.union(themes2))
        
        # Combined similarity
        return (tag_similarity * 0.7 + theme_similarity * 0.3)

    def _find_common_tags(self, tag_counters: List[Counter]) -> List[str]:
        """Find common tags across multiple authors"""
        if not tag_counters:
            return []
        
        # Find tags that appear in at least half of the profiles
        all_tags = set()
        for counter in tag_counters:
            all_tags.update(counter.keys())
        
        common_tags = []
        min_occurrence = max(1, len(tag_counters) // 2)
        
        for tag in all_tags:
            occurrence_count = sum(1 for counter in tag_counters if tag in counter)
            if occurrence_count >= min_occurrence:
                common_tags.append(tag)
        
        return common_tags[:5]  # Top 5 common tags

    def _find_optimal_posting_windows(self, hourly_analysis: List[Dict]) -> List[Dict]:
        """Find optimal posting time windows"""
        if not hourly_analysis:
            return []
        
        # Sort by combined score (engagement + velocity)
        scored_hours = []
        for hour_data in hourly_analysis:
            combined_score = hour_data["avg_engagement"] + hour_data["avg_velocity"] * 10
            scored_hours.append({
                "hour": hour_data["hour"],
                "score": combined_score,
                "avg_engagement": hour_data["avg_engagement"],
                "avg_velocity": hour_data["avg_velocity"]
            })
        
        # Get top windows
        scored_hours.sort(key=lambda x: x["score"], reverse=True)
        return scored_hours[:6]  # Top 6 hours

    def _classify_content_type(self, post: Dict) -> str:
        """Classify content type based on content analysis"""
        content = post.get("content", "").lower()
        
        if '?' in content:
            return "question"
        elif any(word in content for word in ['share', 'check', 'look']):
            return "call_to_action"
        elif any(word in content for word in ['story', 'experience', 'happened']):
            return "narrative"
        elif any(word in content for word in ['tip', 'how', 'guide']):
            return "educational"
        elif len(content) < 50:
            return "short_form"
        else:
            return "general"

    def _analyze_common_traits(self, posts: List[Dict]) -> List[str]:
        """Analyze common traits among a group of posts"""
        if not posts:
            return []
        
        traits = []
        
        # Content length analysis
        lengths = [post.get("content_length", 0) for post in posts]
        avg_length = sum(lengths) / len(lengths)
        if avg_length > 200:
            traits.append("longer_content")
        elif avg_length < 100:
            traits.append("shorter_content")
        
        # Tag usage analysis
        tag_usage = [len(post.get("tags", [])) for post in posts]
        avg_tags = sum(tag_usage) / len(tag_usage)
        if avg_tags > 2:
            traits.append("high_tag_usage")
        elif avg_tags < 1:
            traits.append("minimal_tag_usage")
        
        # Engagement pattern analysis
        reply_ratios = []
        for post in posts:
            total = post.get("total_engagement", 1)
            reply_ratio = post.get("reply_count", 0) / total
            reply_ratios.append(reply_ratio)
        
        avg_reply_ratio = sum(reply_ratios) / len(reply_ratios)
        if avg_reply_ratio > 0.2:
            traits.append("high_discussion_generation")
        
        # Content type analysis
        content_types = [self._classify_content_type(post) for post in posts]
        most_common_type = Counter(content_types).most_common(1)[0][0]
        traits.append(f"primarily_{most_common_type}")
        
        return traits[:5]  # Top 5 traits

    async def _save_network_data(self, data: Dict, batch_id: str) -> str:
        """Save network analysis data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/network/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/batch_{batch_id}.network.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, network_data: Dict, batch_id: str) -> Dict:
        """Generate summary with top tags, clusters, and author groups as specified in AI Agent Prompts"""
        top_tags = network_data.get("top_velocity_tags", [])[:10]
        hashtag_network = network_data.get("hashtag_network", {})
        author_clusters = network_data.get("author_clusters", {})
        
        return {
            "batch_id": batch_id,
            "top_tags": top_tags,
            "tag_clusters": hashtag_network.get("clusters", []),
            "author_groups": author_clusters.get("clusters", []),
            "network_insights": {
                "total_tag_relationships": len(hashtag_network.get("edges", [])),
                "most_connected_tags": hashtag_network.get("nodes", [])[:5],
                "author_cluster_count": len(author_clusters.get("clusters", [])),
                "influence_leaders": network_data.get("influence_network", {}).get("top_influencers", [])[:3]
            },
            "strategic_patterns": network_data.get("strategy_patterns", {}),
            "optimal_timing": network_data.get("timing_analysis", {}).get("optimal_posting_windows", [])[:3]
        }