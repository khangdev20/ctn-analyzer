# [BOT] AI AGENT PROMPTS FOR FULL TRENDING ANALYSIS WORKFLOW

### (Optimized for GitHub Copilot Integration)

Each section describes a clear **coding intent** with a comment format Copilot understands.  
Use these as in-code prompts or docstring templates to generate full functions, Celery tasks, or scripts.

---

## 🟩 [1] Data Collection — Collect Trending and Latest Posts

```python
# Task: Collect latest and trending posts from the feed
# - Input: API endpoint or feed URL
# - Output: raw JSON file (data/raw/YYYY/MM/DD/batch_<timestamp>.json)
# - Steps:
#   1. Fetch posts using requests
#   2. Extract key fields: id, author, content, created_at, like_count, reply_count, repost_count, tags
#   3. Mark duplicate post_ids with "seen" flag
#   4. Log summary stats (count, top 5 tags)
# - Return: summary dict {batch_id, collected_count, trending_tags}
```

## 🟦 [2] Data Cleaning — Normalize and Prepare Data

# Task: Clean and normalize collected post data

# - Input: raw JSON batch file

# - Output: cleaned JSON file (data/clean/YYYY/MM/DD/batch\_<timestamp>.clean.json)

# - Steps:

# 1. Remove deleted or duplicate posts

# 2. Standardize field names and data types

# 3. Compute derived metrics: total_engagement, engagement_per_min

# 4. Log summary metrics (cleaned_count, avg_engagement)

# - Return: summary dict {batch_id, cleaned_count, duplicates_removed, avg_engagement}

## 🟧 [3] Growth Tracking — Compute Engagement Growth and Velocity

# Task: Compute engagement deltas and growth velocity between current and previous batches

# - Input: cleaned batch JSONs (current and previous)

# - Output: growth JSON file (data/growth/YYYY/MM/DD/batch\_<timestamp>.growth.json)

# - Steps:

# 1. Join datasets by post_id

# 2. Calculate Δlikes, Δreplies, Δreposts, Δtotal

# 3. Compute velocity = delta_total / delta_time

# 4. Save and log top 5 velocity posts

# - Return: summary dict {avg_velocity_per_min, top_velocity_posts}

## 🟨 [4] Score Estimation — Calculate Raw Story and Engagement Scores

# Task: Estimate raw Story Score and Engagement Score for each post

# - Input: cleaned post data

# - Output: score JSON file (data/score/YYYY/MM/DD/batch\_<timestamp>.score.json)

# - Steps:

# 1. Analyze text content for sentiment, clarity, and narrative tone

# 2. Compute numeric features (likes, replies, reposts, follower count)

# 3. Combine into story_score (0–100) and engagement_score (0–100)

# - Return: average story_score and engagement_score for batch

## 🟥 [5] Rubric Evaluation — Apply Viral Post Rubric

# Task: Evaluate each post using viral rubric weights

# - Input: story_score, engagement_score, growth metrics

# - Output: rubric JSON file (data/rubric/YYYY/MM/DD/batch\_<timestamp>.rubric.json)

# - Weights:

# Content Quality: 0.30

# Engagement: 0.25

# Timing & Trend: 0.20

# Network Amplification: 0.15

# Strategy Crafting: 0.10

# - Steps:

# 1. Compute weighted final_score

# 2. Classify post as Trending / High Engagement / Moderate

# 3. Save rubric results and log summary distribution

# - Return: average_final_score, top_posts

# Task: Identify strategy patterns, clusters, and narrative groups

# - Input: rubric results + tag and author data

## 🟪 [6] Strategic & Network Analysis — Detect Patterns and Clusters

# - Output: network JSON file (data/network/YYYY/MM/DD/batch\_<timestamp>.network.json)

# - Steps:

# 1. Build hashtag co-occurrence graph

# 2. Detect author clusters using cosine similarity

# 3. Find top tags driving engagement velocity

# 4. Analyze post timing vs engagement correlation

# - Return: top_tags, tag_clusters, author_groups

## 🟫 [7] Predictive Modeling — Forecast Future Trending Posts

# Task: Predict trending probability for each post

# - Input: combined rubric, score, and growth data

# - Output: prediction JSON file (data/predict/YYYY/MM/DD/batch\_<timestamp>.predict.json)

# - Steps:

# 1. Merge data sources by post_id

# 2. Compute trending_probability using rule-based or ML model

# 3. Highlight posts with probability >= 0.8

# - Return: {post_id, trending_probability, key_factors}

## 🟦 [8] Reporting — Generate Intelligence Report for Discord

# Task: Generate human-readable intelligence report from latest batch

# - Input: combined analysis results (score, rubric, growth, network, prediction)

# - Output: Discord-ready embed JSON

# - Steps:

# 1. Summarize: total posts, avg engagement, top tags

# 2. Highlight top velocity and top rubric posts

# 3. Summarize predictions and weekly focus

# 4. Format as Discord embed payload

# 5. Send via webhook

# - Return: {embed_payload, timestamp, send_status}

## 🟩 [9] Continuous Learning — Refine Rubric and Feature Weights

# Task: Adjust scoring model and rubric weights based on performance

# - Input: previous predictions vs actual trending outcomes

# - Output: updated weight config (config/weights/YYYY/MM/DD/rubric_weights.json)

# - Steps:

# 1. Compare predicted vs actual trending

# 2. Update feature importance (e.g., tone, velocity, tags)

# 3. Save new weights with changelog

# - Return: new rubric weight dict and accuracy score

## 🧩 [10] Meta Analysis — Weekly Strategic Insights

# Task: Generate weekly trend and strategy report

# - Input: all batch results for the last 7 days

# - Output: weekly report JSON (data/reports/weekly/YYYY-MM-DD.summary.json)

# - Steps:

# 1. Identify recurring hashtags and successful strategies

# 2. Compute persistence and consistency metrics

# 3. Generate 7-day content calendar recommendation

# 4. Format weekly summary message for Discord

# - Return: weekly_insights, content_calendar
