"""
Network Intelligence Agent
Analyzes relationships between authors and hashtags to detect communities and influence patterns
"""

import asyncio
import json
import logging
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set
from itertools import combinations
import networkx as nx

logger = logging.getLogger(__name__)


class NetworkIntelligenceAgent:
    """
    Network Intelligence Agent for Social Media Analysis

    Analyzes:
    1. Hashtag co-occurrence clusters and relationships
    2. Author communities and influencer detection
    3. Cross-tag influence and connectivity patterns
    4. Network topology insights and community structures
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Network analysis parameters
        self.min_community_size = 3
        self.min_tag_frequency = 2
        self.connectivity_threshold = 0.3

    async def analyze_network_intelligence(self, posts: List[Dict], batch_id: str) -> Dict:
        """
        Run complete network intelligence analysis

        Args:
            posts: List of post dictionaries with author and tags data
            batch_id: Unique identifier for this analysis

        Returns:
            Dict with network analysis results and Discord-formatted report
        """
        try:
            self.logger.info(
                f"🌐 Starting network intelligence analysis for batch {batch_id}")

            # Step 1: Extract and validate network data
            network_data = self._extract_network_data(posts)

            if not network_data["authors"] or not network_data["hashtags"]:
                return self._generate_empty_response(batch_id, "Insufficient network data")

            self.logger.info(
                f"📊 Network data: {len(network_data['authors'])} authors, {len(network_data['hashtags'])} hashtags")

            # Step 2: Build hashtag co-occurrence clusters
            hashtag_clusters = await self._build_hashtag_clusters(network_data)

            # Step 3: Detect author communities and influencers
            author_communities = await self._detect_author_communities(network_data)

            # Step 4: Calculate tag connectivity and influence
            tag_connectivity = await self._analyze_tag_connectivity(network_data, hashtag_clusters)

            # Step 5: Identify cross-tag influence patterns
            cross_influence = await self._analyze_cross_tag_influence(network_data, hashtag_clusters)

            # Step 6: Generate Discord-formatted report
            discord_report = self._format_discord_report(
                hashtag_clusters, author_communities, tag_connectivity, cross_influence, batch_id
            )

            # Step 7: Compile final results
            results = {
                "batch_id": batch_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "network_summary": {
                    "total_authors": len(network_data["authors"]),
                    "total_hashtags": len(network_data["hashtags"]),
                    "total_posts": len(posts),
                    "unique_connections": len(network_data["author_tag_connections"])
                },
                "hashtag_clusters": hashtag_clusters,
                "author_communities": author_communities,
                "tag_connectivity": tag_connectivity,
                "cross_influence": cross_influence,
                "discord_message": discord_report,
                "raw_network_data": network_data
            }

            self.logger.info(
                f"✅ Network intelligence analysis completed successfully")
            return results

        except Exception as e:
            self.logger.error(f"❌ Network intelligence analysis failed: {e}")
            return self._generate_error_response(batch_id, str(e))

    def _extract_network_data(self, posts: List[Dict]) -> Dict:
        """Extract network relationship data from posts"""
        authors = set()
        hashtags = set()
        author_tag_connections = defaultdict(set)
        tag_cooccurrences = defaultdict(int)
        author_engagement = defaultdict(int)
        hashtag_engagement = defaultdict(int)
        author_posts = defaultdict(list)

        for post in posts:
            try:
                # Extract author information
                author_data = post.get("author", {})
                username = author_data.get("username", "").strip()
                if not username:
                    continue

                authors.add(username)

                # Extract hashtags
                post_tags = post.get("tags", [])
                if isinstance(post_tags, str):
                    post_tags = [post_tags]

                # Clean hashtags
                clean_tags = []
                for tag in post_tags:
                    if isinstance(tag, str):
                        clean_tag = tag.strip().lower()
                        if clean_tag and len(clean_tag) > 1:
                            if clean_tag.startswith('#'):
                                clean_tag = clean_tag[1:]
                            clean_tags.append(clean_tag)

                if not clean_tags:
                    continue

                hashtags.update(clean_tags)

                # Calculate engagement for this post
                engagement = (
                    post.get("like_count", 0) +
                    post.get("reply_count", 0) +
                    post.get("repost_count", 0)
                )

                # Build connections
                for tag in clean_tags:
                    author_tag_connections[username].add(tag)
                    hashtag_engagement[tag] += engagement

                author_engagement[username] += engagement
                author_posts[username].append(post)

                # Build tag co-occurrences
                for tag1, tag2 in combinations(clean_tags, 2):
                    pair = tuple(sorted([tag1, tag2]))
                    tag_cooccurrences[pair] += 1

            except Exception as e:
                self.logger.warning(
                    f"Failed to process post {post.get('id', 'unknown')}: {e}")
                continue

        return {
            "authors": list(authors),
            "hashtags": list(hashtags),
            "author_tag_connections": {k: list(v) for k, v in author_tag_connections.items()},
            "tag_cooccurrences": dict(tag_cooccurrences),
            "author_engagement": dict(author_engagement),
            "hashtag_engagement": dict(hashtag_engagement),
            "author_posts": dict(author_posts)
        }

    async def _build_hashtag_clusters(self, network_data: Dict) -> Dict:
        """Build hashtag co-occurrence clusters using graph analysis"""
        try:
            tag_cooccurrences = network_data["tag_cooccurrences"]
            hashtag_engagement = network_data["hashtag_engagement"]

            if not tag_cooccurrences:
                return {"clusters": [], "strongest_pair": None, "cluster_count": 0}

            # Create hashtag graph
            G = nx.Graph()

            # Add hashtags as nodes with engagement weights
            for hashtag, engagement in hashtag_engagement.items():
                G.add_node(hashtag, engagement=engagement)

            # Add co-occurrence edges with weights
            for (tag1, tag2), cooccurrence_count in tag_cooccurrences.items():
                if cooccurrence_count >= self.min_tag_frequency:
                    G.add_edge(tag1, tag2, weight=cooccurrence_count)

            # Find communities using modularity-based clustering
            try:
                communities = nx.community.greedy_modularity_communities(G)
                clusters = []

                for i, community in enumerate(communities):
                    if len(community) >= 2:  # Minimum cluster size
                        # Calculate cluster metrics
                        cluster_tags = list(community)
                        cluster_engagement = sum(hashtag_engagement.get(
                            tag, 0) for tag in cluster_tags)

                        # Find strongest internal connections
                        internal_connections = []
                        for tag1, tag2 in combinations(cluster_tags, 2):
                            pair = tuple(sorted([tag1, tag2]))
                            if pair in tag_cooccurrences:
                                internal_connections.append({
                                    "tags": [tag1, tag2],
                                    "strength": tag_cooccurrences[pair]
                                })

                        internal_connections.sort(
                            key=lambda x: x["strength"], reverse=True)

                        clusters.append({
                            "cluster_id": i + 1,
                            "tags": cluster_tags,
                            "size": len(cluster_tags),
                            "total_engagement": cluster_engagement,
                            "avg_engagement": cluster_engagement / len(cluster_tags),
                            # Top 3 connections
                            "internal_connections": internal_connections[:3],
                            "strongest_connection": internal_connections[0] if internal_connections else None
                        })

                # Sort clusters by engagement
                clusters.sort(
                    key=lambda x: x["total_engagement"], reverse=True)

                # Find strongest overall pair
                strongest_pair = None
                if tag_cooccurrences:
                    strongest_connection = max(
                        tag_cooccurrences.items(), key=lambda x: x[1])
                    strongest_pair = {
                        "tags": list(strongest_connection[0]),
                        "strength": strongest_connection[1]
                    }

                return {
                    "clusters": clusters,
                    "strongest_pair": strongest_pair,
                    "cluster_count": len(clusters),
                    "total_connections": len(tag_cooccurrences)
                }

            except Exception as e:
                self.logger.warning(
                    f"Community detection failed, using fallback method: {e}")
                return self._fallback_hashtag_clustering(tag_cooccurrences, hashtag_engagement)

        except Exception as e:
            self.logger.error(f"Hashtag clustering failed: {e}")
            return {"clusters": [], "strongest_pair": None, "cluster_count": 0}

    def _fallback_hashtag_clustering(self, tag_cooccurrences: Dict, hashtag_engagement: Dict) -> Dict:
        """Fallback hashtag clustering using simple threshold-based grouping"""
        # Find strongly connected tag pairs
        strong_pairs = [(pair, count) for pair, count in tag_cooccurrences.items()
                        if count >= self.min_tag_frequency]
        strong_pairs.sort(key=lambda x: x[1], reverse=True)

        # Build simple clusters from strongest pairs
        clusters = []
        used_tags = set()

        for i, (pair, strength) in enumerate(strong_pairs[:5]):  # Top 5 pairs
            tag1, tag2 = pair
            if tag1 not in used_tags and tag2 not in used_tags:
                cluster_engagement = hashtag_engagement.get(
                    tag1, 0) + hashtag_engagement.get(tag2, 0)
                clusters.append({
                    "cluster_id": i + 1,
                    "tags": [tag1, tag2],
                    "size": 2,
                    "total_engagement": cluster_engagement,
                    "avg_engagement": cluster_engagement / 2,
                    "strongest_connection": {"tags": [tag1, tag2], "strength": strength}
                })
                used_tags.update([tag1, tag2])

        strongest_pair = {"tags": list(
            strong_pairs[0][0]), "strength": strong_pairs[0][1]} if strong_pairs else None

        return {
            "clusters": clusters,
            "strongest_pair": strongest_pair,
            "cluster_count": len(clusters),
            "total_connections": len(tag_cooccurrences)
        }

    async def _detect_author_communities(self, network_data: Dict) -> Dict:
        """Detect author communities and identify influencers"""
        try:
            author_tag_connections = network_data["author_tag_connections"]
            author_engagement = network_data["author_engagement"]
            author_posts = network_data["author_posts"]

            if len(author_tag_connections) < 3:
                return {"communities": [], "influencers": [], "community_count": 0}

            # Create author similarity graph based on shared hashtags
            G = nx.Graph()

            # Add authors as nodes with engagement weights
            for author, engagement in author_engagement.items():
                post_count = len(author_posts.get(author, []))
                G.add_node(author, engagement=engagement, posts=post_count)

            # Calculate Jaccard similarity between authors based on hashtag usage
            authors = list(author_tag_connections.keys())
            for i, author1 in enumerate(authors):
                for author2 in authors[i+1:]:
                    tags1 = set(author_tag_connections[author1])
                    tags2 = set(author_tag_connections[author2])

                    if tags1 and tags2:
                        # Jaccard similarity
                        intersection = len(tags1.intersection(tags2))
                        union = len(tags1.union(tags2))
                        similarity = intersection / union if union > 0 else 0

                        if similarity > self.connectivity_threshold:
                            G.add_edge(author1, author2, weight=similarity)

            # Find communities
            try:
                communities = nx.community.greedy_modularity_communities(G)
                community_data = []

                for i, community in enumerate(communities):
                    if len(community) >= self.min_community_size:
                        community_authors = list(community)

                        # Calculate community metrics
                        total_engagement = sum(author_engagement.get(
                            author, 0) for author in community_authors)
                        total_posts = sum(len(author_posts.get(author, []))
                                          for author in community_authors)

                        # Find shared hashtags
                        all_tags = set()
                        for author in community_authors:
                            all_tags.update(
                                author_tag_connections.get(author, []))

                        # Find common hashtags (used by multiple community members)
                        tag_usage = defaultdict(int)
                        for author in community_authors:
                            for tag in author_tag_connections.get(author, []):
                                tag_usage[tag] += 1

                        common_tags = [tag for tag,
                                       count in tag_usage.items() if count > 1]

                        # Generate community name based on most common tags
                        if common_tags:
                            top_tags = sorted(
                                common_tags, key=lambda t: tag_usage[t], reverse=True)[:2]
                            community_name = f"#{' + #'.join(top_tags)} Community"
                        else:
                            community_name = f"Community {i + 1}"

                        community_data.append({
                            "community_id": i + 1,
                            "name": community_name,
                            "authors": community_authors,
                            "size": len(community_authors),
                            "total_engagement": total_engagement,
                            "total_posts": total_posts,
                            "avg_engagement_per_author": total_engagement / len(community_authors),
                            # Top 5 common hashtags
                            "common_hashtags": common_tags[:5],
                            "shared_tag_count": len(common_tags)
                        })

                # Sort by total engagement
                community_data.sort(
                    key=lambda x: x["total_engagement"], reverse=True)

            except Exception as e:
                self.logger.warning(f"Community detection failed: {e}")
                community_data = []

            # Identify influencers (top authors by engagement and connectivity)
            influencers = []
            if G.nodes():
                # Calculate centrality measures
                try:
                    degree_centrality = nx.degree_centrality(G)
                    betweenness_centrality = nx.betweenness_centrality(G)

                    # Combine centrality with engagement
                    author_scores = []
                    for author in G.nodes():
                        engagement = author_engagement.get(author, 0)
                        degree = degree_centrality.get(author, 0)
                        betweenness = betweenness_centrality.get(author, 0)
                        posts = len(author_posts.get(author, []))

                        # Composite influence score
                        influence_score = (
                            engagement * 0.4) + (degree * 0.3) + (betweenness * 0.2) + (posts * 0.1)

                        author_scores.append({
                            "username": author,
                            "engagement": engagement,
                            "posts": posts,
                            "network_connections": len(list(G.neighbors(author))),
                            "degree_centrality": round(degree, 3),
                            "betweenness_centrality": round(betweenness, 3),
                            "influence_score": round(influence_score, 2)
                        })

                    # Sort by influence score
                    author_scores.sort(
                        key=lambda x: x["influence_score"], reverse=True)
                    influencers = author_scores[:5]  # Top 5 influencers

                except Exception as e:
                    self.logger.warning(f"Centrality calculation failed: {e}")
                    # Fallback: sort by engagement only
                    influencers = [
                        {
                            "username": author,
                            "engagement": engagement,
                            "posts": len(author_posts.get(author, [])),
                            "influence_score": engagement
                        }
                        for author, engagement in sorted(author_engagement.items(), key=lambda x: x[1], reverse=True)[:5]
                    ]

            return {
                "communities": community_data,
                "influencers": influencers,
                "community_count": len(community_data),
                "total_authors_in_communities": sum(len(c["authors"]) for c in community_data)
            }

        except Exception as e:
            self.logger.error(f"Author community detection failed: {e}")
            return {"communities": [], "influencers": [], "community_count": 0}

    async def _analyze_tag_connectivity(self, network_data: Dict, hashtag_clusters: Dict) -> Dict:
        """Analyze hashtag connectivity and influence patterns"""
        try:
            tag_cooccurrences = network_data["tag_cooccurrences"]
            hashtag_engagement = network_data["hashtag_engagement"]
            hashtags = network_data["hashtags"]

            if not hashtags:
                return {"connectivity_index": 0, "most_connected_tags": [], "network_density": 0}

            # Calculate connectivity metrics
            total_possible_connections = len(
                hashtags) * (len(hashtags) - 1) / 2
            actual_connections = len(tag_cooccurrences)
            network_density = actual_connections / \
                total_possible_connections if total_possible_connections > 0 else 0

            # Calculate connectivity index (0-1 scale)
            max_cooccurrence = max(
                tag_cooccurrences.values()) if tag_cooccurrences else 1
            weighted_connections = sum(
                count / max_cooccurrence for count in tag_cooccurrences.values())
            connectivity_index = min(
                1.0, weighted_connections / max(actual_connections, 1))

            # Find most connected hashtags
            tag_connection_counts = defaultdict(int)
            tag_connection_strength = defaultdict(int)

            for (tag1, tag2), strength in tag_cooccurrences.items():
                tag_connection_counts[tag1] += 1
                tag_connection_counts[tag2] += 1
                tag_connection_strength[tag1] += strength
                tag_connection_strength[tag2] += strength

            # Calculate connectivity scores
            most_connected = []
            for tag in hashtags:
                connections = tag_connection_counts.get(tag, 0)
                strength = tag_connection_strength.get(tag, 0)
                engagement = hashtag_engagement.get(tag, 0)

                # Composite connectivity score
                connectivity_score = connections * 0.4 + strength * 0.3 + engagement * 0.3

                most_connected.append({
                    "hashtag": tag,
                    "connections": connections,
                    "connection_strength": strength,
                    "engagement": engagement,
                    "connectivity_score": round(connectivity_score, 2)
                })

            # Sort by connectivity score
            most_connected.sort(
                key=lambda x: x["connectivity_score"], reverse=True)

            return {
                "connectivity_index": round(connectivity_index, 3),
                "network_density": round(network_density, 3),
                "most_connected_tags": most_connected[:5],
                "total_connections": actual_connections,
                "avg_connection_strength": round(sum(tag_cooccurrences.values()) / max(len(tag_cooccurrences), 1), 2)
            }

        except Exception as e:
            self.logger.error(f"Tag connectivity analysis failed: {e}")
            return {"connectivity_index": 0, "most_connected_tags": [], "network_density": 0}

    async def _analyze_cross_tag_influence(self, network_data: Dict, hashtag_clusters: Dict) -> Dict:
        """Analyze cross-tag influence and bridging patterns"""
        try:
            tag_cooccurrences = network_data["tag_cooccurrences"]
            hashtag_engagement = network_data["hashtag_engagement"]
            author_tag_connections = network_data["author_tag_connections"]

            if not tag_cooccurrences:
                return {"most_influential_tag": None, "bridge_tags": [], "influence_scores": {}}

            # Calculate tag influence based on:
            # 1. Number of different tags it co-occurs with
            # 2. Strength of those connections
            # 3. Engagement of posts using this tag
            # 4. Number of authors using this tag

            tag_influence_metrics = defaultdict(lambda: {
                "unique_connections": 0,
                "total_connection_strength": 0,
                "engagement": 0,
                "author_count": 0,
                "bridge_score": 0
            })

            # Count unique connections and strength
            for (tag1, tag2), strength in tag_cooccurrences.items():
                tag_influence_metrics[tag1]["unique_connections"] += 1
                tag_influence_metrics[tag2]["unique_connections"] += 1
                tag_influence_metrics[tag1]["total_connection_strength"] += strength
                tag_influence_metrics[tag2]["total_connection_strength"] += strength

            # Add engagement and author metrics
            for tag in hashtag_engagement:
                tag_influence_metrics[tag]["engagement"] = hashtag_engagement[tag]

            for author, tags in author_tag_connections.items():
                for tag in tags:
                    tag_influence_metrics[tag]["author_count"] += 1

            # Calculate bridge scores (tags that connect different clusters)
            clusters = hashtag_clusters.get("clusters", [])
            if len(clusters) > 1:
                cluster_tags = {tag: i for i, cluster in enumerate(
                    clusters) for tag in cluster["tags"]}

                for (tag1, tag2), strength in tag_cooccurrences.items():
                    if tag1 in cluster_tags and tag2 in cluster_tags:
                        if cluster_tags[tag1] != cluster_tags[tag2]:  # Different clusters
                            # Both tags are bridges between clusters
                            tag_influence_metrics[tag1]["bridge_score"] += strength
                            tag_influence_metrics[tag2]["bridge_score"] += strength

            # Calculate final influence scores
            influence_results = []
            for tag, metrics in tag_influence_metrics.items():
                # Normalize metrics
                connections = metrics["unique_connections"]
                strength = metrics["total_connection_strength"]
                engagement = metrics["engagement"]
                authors = metrics["author_count"]
                bridge = metrics["bridge_score"]

                # Composite influence score
                influence_score = (
                    connections * 0.25 +  # Network reach
                    strength * 0.2 +      # Connection strength
                    engagement * 0.2 +    # Content engagement
                    authors * 0.2 +       # Author adoption
                    bridge * 0.15         # Bridge connections
                )

                influence_results.append({
                    "hashtag": tag,
                    "influence_score": round(influence_score, 2),
                    "unique_connections": connections,
                    "connection_strength": strength,
                    "engagement": engagement,
                    "author_count": authors,
                    "bridge_score": bridge,
                    "is_bridge": bridge > 0
                })

            # Sort by influence score
            influence_results.sort(
                key=lambda x: x["influence_score"], reverse=True)

            # Identify top bridge tags
            bridge_tags = [
                tag for tag in influence_results if tag["is_bridge"]]
            bridge_tags.sort(key=lambda x: x["bridge_score"], reverse=True)

            most_influential = influence_results[0] if influence_results else None

            return {
                "most_influential_tag": most_influential,
                "bridge_tags": bridge_tags[:3],  # Top 3 bridge tags
                "influence_scores": {tag["hashtag"]: tag["influence_score"] for tag in influence_results[:10]},
                "total_analyzed_tags": len(influence_results)
            }

        except Exception as e:
            self.logger.error(f"Cross-tag influence analysis failed: {e}")
            return {"most_influential_tag": None, "bridge_tags": [], "influence_scores": {}}

    def _format_discord_report(self,
                               hashtag_clusters: Dict,
                               author_communities: Dict,
                               tag_connectivity: Dict,
                               cross_influence: Dict,
                               batch_id: str) -> str:
        """Format network analysis results as Discord message"""

        message_parts = ["🌐 **Network Intelligence Report**", ""]

        # Influencers section
        influencers = author_communities.get("influencers", [])
        if influencers:
            top_influencers = [
                f"@{inf['username']}" for inf in influencers[:3]]
            message_parts.append(
                f"• **Influencers:** {', '.join(top_influencers)}")
        else:
            message_parts.append("• **Influencers:** None detected")

        # Strongest tag cluster
        strongest_cluster = None
        clusters = hashtag_clusters.get("clusters", [])
        if clusters:
            # First cluster is strongest by engagement
            strongest_cluster = clusters[0]
            # Limit to 2 tags for readability
            cluster_tags = strongest_cluster["tags"][:2]
            message_parts.append(
                f"• **Strongest Tag Cluster:** #{' + #'.join(cluster_tags)}")
        else:
            strongest_pair = hashtag_clusters.get("strongest_pair")
            if strongest_pair:
                tags = strongest_pair["tags"]
                message_parts.append(
                    f"• **Strongest Tag Cluster:** #{' + #'.join(tags)}")
            else:
                message_parts.append(
                    "• **Strongest Tag Cluster:** None detected")

        # Detected groups/communities
        communities = author_communities.get("communities", [])
        if communities:
            main_community = communities[0]
            community_name = main_community["name"]
            community_size = main_community["size"]
            message_parts.append(
                f"• **Detected Groups:** \"{community_name}\" ({community_size} authors)")
        else:
            message_parts.append("• **Detected Groups:** No communities found")

        # Tag connectivity index
        connectivity_index = tag_connectivity.get("connectivity_index", 0)
        message_parts.append(
            f"• **Tag Connectivity Index:** {connectivity_index:.2f}")

        # Most cross-influential tag
        most_influential = cross_influence.get("most_influential_tag")
        if most_influential:
            tag_name = most_influential["hashtag"]
            message_parts.append(
                f"🧭 **Most Cross-Influential Tag:** #{tag_name}")
        else:
            message_parts.append(
                "🧭 **Most Cross-Influential Tag:** None detected")

        # Additional insights
        message_parts.append("")

        # Network insights
        insights = []

        total_connections = tag_connectivity.get("total_connections", 0)
        if total_connections > 0:
            insights.append(f"📊 {total_connections} tag connections detected")

        if len(communities) > 1:
            insights.append(
                f"👥 {len(communities)} distinct author communities")

        bridge_tags = cross_influence.get("bridge_tags", [])
        if bridge_tags:
            bridge_tag = bridge_tags[0]["hashtag"]
            insights.append(f"🌉 #{bridge_tag} bridges communities")

        network_density = tag_connectivity.get("network_density", 0)
        if network_density > 0.5:
            insights.append("🔗 Highly connected network")
        elif network_density > 0.2:
            insights.append("🔗 Moderately connected network")
        else:
            insights.append("🔗 Sparse network connections")

        # Add insights to message
        for insight in insights[:3]:  # Limit to 3 insights
            message_parts.append(f"• {insight}")

        # Footer
        message_parts.append(f"")
        message_parts.append(f"📅 *Network Analysis: {batch_id}*")

        # Join and ensure Discord character limit
        full_message = "\n".join(message_parts)

        if len(full_message) > 1900:  # Discord limit with buffer
            full_message = full_message[:1897] + "..."

        return full_message

    def _generate_empty_response(self, batch_id: str, reason: str) -> Dict:
        """Generate response when insufficient data for analysis"""
        return {
            "batch_id": batch_id,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "network_summary": {
                "total_authors": 0,
                "total_hashtags": 0,
                "total_posts": 0,
                "unique_connections": 0
            },
            "hashtag_clusters": {"clusters": [], "strongest_pair": None, "cluster_count": 0},
            "author_communities": {"communities": [], "influencers": [], "community_count": 0},
            "tag_connectivity": {"connectivity_index": 0, "most_connected_tags": [], "network_density": 0},
            "cross_influence": {"most_influential_tag": None, "bridge_tags": [], "influence_scores": {}},
            "discord_message": f"🌐 **Network Intelligence Report**\n\n⚠️ **Analysis Skipped**\nReason: {reason}\n\n📅 *{batch_id}*",
            "error": True,
            "error_message": reason
        }

    def _generate_error_response(self, batch_id: str, error_message: str) -> Dict:
        """Generate error response"""
        return {
            "batch_id": batch_id,
            "error": True,
            "error_message": error_message,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "discord_message": f"❌ **Network Intelligence Error**\n\nBatch: {batch_id}\nError: {error_message[:200]}\n\n📅 *{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
        }


# Utility function for standalone usage
async def analyze_network_intelligence(posts: List[Dict], batch_id: str = None) -> Dict:
    """
    Standalone function to analyze network intelligence from posts

    Args:
        posts: List of post dictionaries with author and tags data
        batch_id: Optional batch identifier

    Returns:
        Dict with complete network intelligence analysis and Discord report
    """
    if not batch_id:
        batch_id = f"network_{int(datetime.now().timestamp())}"

    agent = NetworkIntelligenceAgent()
    return await agent.analyze_network_intelligence(posts, batch_id)
