"""
Advanced Prompt Suggestion Engine
Tạo gợi ý nội dung thông minh dựa trên phân tích LLM và data insights
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import Counter
import numpy as np

from llms.llm_models import LLMModels

logger = logging.getLogger(__name__)


class PromptSuggestionEngine:
    """Advanced engine for generating intelligent content prompts and suggestions"""

    def __init__(self):
        self.llm = LLMModels()

        # Content archetypes for different goals
        self.content_archetypes = {
            'viral': {
                'characteristics': ['controversial', 'emotional', 'timely', 'relatable'],
                'structures': ['question_hook', 'bold_statement', 'story_revelation'],
                'triggers': ['outrage', 'joy', 'surprise', 'curiosity']
            },
            'engagement': {
                'characteristics': ['interactive', 'discussion_worthy', 'opinion_based'],
                'structures': ['poll_question', 'debate_starter', 'experience_share'],
                'triggers': ['agreement', 'disagreement', 'sharing', 'advice_seeking']
            },
            'educational': {
                'characteristics': ['informative', 'actionable', 'step_by_step'],
                'structures': ['how_to', 'tips_list', 'myth_busting'],
                'triggers': ['learning', 'problem_solving', 'skill_building']
            },
            'community_building': {
                'characteristics': ['inclusive', 'supportive', 'collaborative'],
                'structures': ['community_question', 'shared_experience', 'celebration'],
                'triggers': ['belonging', 'support', 'shared_identity']
            }
        }

        # Proven engagement patterns
        self.engagement_patterns = {
            'question_types': {
                'open_ended': "What's your take on [topic]?",
                'either_or': "Would you rather [option A] or [option B]?",
                'completion': "Fill in the blank: The best part about [topic] is ___",
                'experience': "Share a time when you [experience]",
                'prediction': "What do you think will happen with [trend]?"
            },
            'hook_formulas': {
                'curiosity_gap': "The [surprising thing] about [topic] that nobody talks about",
                'contrarian': "Unpopular opinion: [controversial statement]",
                'behind_scenes': "What it's really like to [experience]",
                'listicle': "[Number] [things] that will [benefit/change]",
                'story_arc': "I thought [assumption], but then [revelation]"
            },
            'cta_variations': {
                'question': "What's your experience with this?",
                'share': "Tag someone who needs to see this",
                'engage': "Drop a [emoji] if you agree",
                'discuss': "Let's discuss in the comments",
                'save': "Save this for later reference"
            }
        }

    async def generate_comprehensive_suggestions(self, analysis_data: Dict, target_goals: List[str] = None) -> Dict:
        """Generate comprehensive content suggestions based on analysis data"""
        logger.info("🎨 Generating comprehensive content suggestions...")

        if target_goals is None:
            target_goals = ['viral', 'engagement', 'educational']

        try:
            suggestions = {}

            # 1. Generate data-driven prompts
            data_driven_prompts = await self._generate_data_driven_prompts(analysis_data)
            suggestions['data_driven'] = data_driven_prompts

            # 2. Generate archetype-based suggestions
            for goal in target_goals:
                archetype_suggestions = await self._generate_archetype_suggestions(analysis_data, goal)
                suggestions[f'{goal}_focused'] = archetype_suggestions

            # 3. Generate trending topic variations
            trending_variations = await self._generate_trending_variations(analysis_data)
            suggestions['trending_variations'] = trending_variations

            # 4. Generate A/B test variations
            ab_test_prompts = await self._generate_ab_test_variations(analysis_data)
            suggestions['ab_test_variations'] = ab_test_prompts

            # 5. Generate time-sensitive suggestions
            timely_suggestions = await self._generate_timely_suggestions(analysis_data)
            suggestions['timely_content'] = timely_suggestions

            # 6. Generate interactive format suggestions
            interactive_suggestions = await self._generate_interactive_formats(analysis_data)
            suggestions['interactive_formats'] = interactive_suggestions

            # Rank all suggestions by predicted performance
            ranked_suggestions = self._rank_suggestions_by_performance(
                suggestions, analysis_data)

            return {
                'suggestions_by_category': suggestions,
                'top_recommendations': ranked_suggestions[:15],
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_suggestions': sum(len(v) if isinstance(v, list) else 0 for v in suggestions.values())
            }

        except Exception as e:
            logger.error(f"Failed to generate comprehensive suggestions: {e}")
            return {}

    async def _generate_data_driven_prompts(self, analysis_data: Dict) -> List[Dict]:
        """Generate prompts based on data insights"""
        try:
            top_posts = analysis_data.get('posts', [])[:10]
            metrics = analysis_data.get('aggregate_metrics', {})
            success_patterns = analysis_data.get('success_patterns', {})

            prompt = f"""
🔬 DATA-DRIVEN CONTENT GENERATION

You are an expert content strategist with access to performance data. Generate 8-10 specific content prompts based on these insights:

TOP PERFORMING CONTENT ANALYSIS:
"""

            for i, post in enumerate(top_posts, 1):
                prompt += f"""
{i}. Score: {post.get('scores', {}).get('performance_score', 0):.1f}/100
   Content: "{post.get('content', '')[:120]}..."
   Engagement: {post.get('metrics', {}).get('engagement_rate', 0):.3f}% rate
   Features: Length={post.get('content_length', 0)}, Tags={len(post.get('tags', []))}
"""

            trending_tags = metrics.get('trending_tags', [])[:5]
            best_tags = success_patterns.get('best_tags', [])[:5]
            optimal_length = success_patterns.get('optimal_length', {})

            prompt += f"""
SUCCESS PATTERNS IDENTIFIED:
- Trending Tags: {', '.join(trending_tags)}
- High-Performance Tags: {', '.join(best_tags)}
- Optimal Length: {optimal_length.get('avg', 100)} characters
- Peak Hours: {success_patterns.get('timing_patterns', {}).get('peak_hours', [])}

GENERATE CONTENT PROMPTS:
For each prompt provide:
1. Full content text (ready to post)
2. Optimal hashtags to include
3. Best posting time
4. Expected engagement type
5. Performance prediction (1-100)

Focus on:
- Using proven successful patterns
- Incorporating trending elements
- Optimizing for engagement
- Creating viral potential

Format as JSON with keys: content, hashtags, timing, engagement_type, performance_prediction, reasoning
"""

            response = await self._get_llm_response(prompt)
            return self._parse_json_suggestions(response, 'data_driven')

        except Exception as e:
            logger.warning(f"Data-driven prompt generation failed: {e}")
            return []

    async def _generate_archetype_suggestions(self, analysis_data: Dict, archetype: str) -> List[Dict]:
        """Generate suggestions for specific content archetype"""
        try:
            archetype_config = self.content_archetypes.get(archetype, {})
            if not archetype_config:
                return []

            metrics = analysis_data.get('aggregate_metrics', {})
            trending_tags = metrics.get('trending_tags', [])[:3]

            prompt = f"""
🎯 {archetype.upper()} CONTENT GENERATION

Generate 6-8 content ideas optimized for {archetype} performance:

ARCHETYPE CHARACTERISTICS:
- Traits: {', '.join(archetype_config.get('characteristics', []))}
- Structures: {', '.join(archetype_config.get('structures', []))}
- Emotional Triggers: {', '.join(archetype_config.get('triggers', []))}

CURRENT TRENDING CONTEXT:
- Hot Topics: {', '.join(trending_tags)}
- Platform: Social media (Twitter-like)
- Audience: General public + niche communities

REQUIREMENTS FOR {archetype.upper()} CONTENT:
"""

            if archetype == 'viral':
                prompt += """
- Create strong emotional reactions
- Use controversial but defensible positions
- Include shareable moments
- Leverage current events/trends
- Optimize for reposts and shares
"""
            elif archetype == 'engagement':
                prompt += """
- Ask compelling questions
- Invite personal experiences
- Create discussion opportunities
- Use polls or either/or choices
- Encourage replies and comments
"""
            elif archetype == 'educational':
                prompt += """
- Provide actionable value
- Break down complex topics
- Include step-by-step guidance
- Offer insider knowledge
- Create save-worthy content
"""
            elif archetype == 'community_building':
                prompt += """
- Foster belonging and connection
- Celebrate community achievements
- Share relatable experiences
- Create inclusive conversations
- Build supportive interactions
"""

            prompt += f"""
Generate specific content examples with:
1. Full post text (under 280 characters)
2. Hashtag strategy
3. Engagement prediction
4. Success metrics to track
5. Variation ideas for A/B testing

Format as structured content ready for immediate use.
"""

            response = await self._get_llm_response(prompt)
            return self._parse_content_suggestions(response, archetype)

        except Exception as e:
            logger.warning(f"{archetype} archetype generation failed: {e}")
            return []

    async def _generate_trending_variations(self, analysis_data: Dict) -> List[Dict]:
        """Generate variations of trending content"""
        try:
            metrics = analysis_data.get('aggregate_metrics', {})
            trending_tags = metrics.get('trending_tags', [])[:5]
            top_authors = metrics.get('top_authors', [])[:3]

            if not trending_tags:
                return []

            prompt = f"""
🔥 TRENDING CONTENT VARIATIONS

Create viral variations of current trending topics:

TRENDING ELEMENTS:
- Tags: {', '.join(trending_tags)}
- Top Performers: {', '.join([author[0] for author in top_authors])}

For each trending tag, create 3 different approaches:
1. SUPPORTIVE ANGLE: Agreeing/building on the trend
2. CONTRARIAN ANGLE: Respectful counter-perspective  
3. EDUCATIONAL ANGLE: Explaining/analyzing the trend

VARIATION REQUIREMENTS:
- Each must be under 250 characters
- Include relevant hashtags
- Add unique perspective/value
- Optimize for different engagement types
- Consider different audience segments

Create content that:
✓ Joins conversations authentically
✓ Adds unique value/perspective
✓ Drives meaningful engagement
✓ Builds authority/credibility

Format each variation with performance prediction and target audience.
"""

            response = await self._get_llm_response(prompt)
            return self._parse_content_suggestions(response, 'trending')

        except Exception as e:
            logger.warning(f"Trending variations generation failed: {e}")
            return []

    async def _generate_ab_test_variations(self, analysis_data: Dict) -> List[Dict]:
        """Generate A/B test variations for content optimization"""
        try:
            success_patterns = analysis_data.get('success_patterns', {})
            optimal_features = success_patterns.get('content_features', {})

            prompt = f"""
                🧪 A/B TEST CONTENT VARIATIONS

                Create systematic A/B test variations to optimize performance:

                CURRENT SUCCESS PATTERNS:
                - Question Rate: {optimal_features.get('has_question_rate', 0):.1%}
                - Exclamation Rate: {optimal_features.get('has_exclamation_rate', 0):.1%}
                - Embed Rate: {optimal_features.get('has_embed_rate', 0):.1%}
                - Avg Hashtags: {optimal_features.get('avg_hashtag_count', 0)}

                CREATE TEST VARIATIONS FOR:

                1. HOOK STYLES:
                Version A: Question hook
                Version B: Statement hook
                Version C: Story hook

                2. CALL-TO-ACTION:
                Version A: Direct question
                Version B: Emoji engagement
                Version C: Share request

                3. CONTENT LENGTH:
                Version A: Concise (under 100 chars)
                Version B: Medium (100-150 chars)
                Version C: Detailed (150-250 chars)

                4. HASHTAG STRATEGY:
                Version A: Trending tags only
                Version B: Niche + trending mix
                Version C: Branded + trending

                5. TIMING APPROACH:
                Version A: News/trend reaction
                Version B: Educational content
                Version C: Personal insight

                For each test, provide:
                - Hypothesis being tested
                - Expected outcome
                - Success metrics
                - Statistical significance requirements
                - Implementation timeline

                Create ready-to-test content pairs with clear differences.
            """

            response = await self._get_llm_response(prompt)
            return self._parse_ab_test_suggestions(response)

        except Exception as e:
            logger.warning(f"A/B test generation failed: {e}")
            return []

    async def _generate_timely_suggestions(self, analysis_data: Dict) -> List[Dict]:
        """Generate time-sensitive content suggestions"""
        try:
            current_time = datetime.now(timezone.utc)
            hour = current_time.hour
            day_of_week = current_time.weekday()

            timing_patterns = analysis_data.get(
                'success_patterns', {}).get('timing_patterns', {})
            peak_hours = timing_patterns.get('peak_hours', [])

            prompt = f"""
                ⏰ TIME-SENSITIVE CONTENT STRATEGY

                Current Time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}
                Day: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]}
                Peak Hours: {peak_hours}

                Generate time-optimized content for:

                1. RIGHT NOW ({hour}:00 UTC):
                - What's trending at this hour?
                - Audience activity level?
                - Optimal content type?

                2. NEXT PEAK HOUR:
                - Prepare for high-engagement window
                - Pre-schedule optimal content
                - Maximize visibility

                3. WEEKLY PATTERN:
                - Day-specific content themes
                - Weekly recurring topics  
                - Long-term engagement cycles

                4. SEASONAL/CYCLICAL:
                - Monthly themes
                - Holiday connections
                - Industry cycles

                Create specific content with:
                - Exact posting time recommendations
                - Time-sensitive hooks
                - Urgency elements
                - Expiration dates where relevant
                - Multi-time-zone considerations

                Focus on creating FOMO and timeliness while maintaining value.
            """

            response = await self._get_llm_response(prompt)
            return self._parse_content_suggestions(response, 'timely')

        except Exception as e:
            logger.warning(f"Timely suggestions generation failed: {e}")
            return []

    async def _generate_interactive_formats(self, analysis_data: Dict) -> List[Dict]:
        """Generate interactive content format suggestions"""
        try:
            engagement_patterns = analysis_data.get(
                'success_patterns', {}).get('engagement_patterns', {})

            prompt = f"""
                🎮 INTERACTIVE CONTENT FORMATS

                Current Engagement Data:
                - Reply Rate: {engagement_patterns.get('avg_like_ratio', 0):.2f}
                - Share Rate: {engagement_patterns.get('avg_repost_ratio', 0):.2f}

                Generate interactive content formats that maximize engagement:

                1. QUESTION FORMATS:
                - This or That questions
                - Fill-in-the-blank
                - Opinion polls (text-based)
                - Prediction games
                - Experience sharing prompts

                2. CHALLENGE FORMATS:
                - Daily/weekly challenges
                - Skill demonstrations  
                - Before/after shares
                - Goal-setting exercises
                - Learning challenges

                3. COLLABORATIVE FORMATS:
                - Thread builders
                - Community projects
                - Crowdsourced content
                - Collective storytelling
                - Group problem-solving

                4. GAME-LIKE FORMATS:
                - Trivia questions
                - Riddles/puzzles
                - Word games
                - Number games
                - Creative challenges

                5. FEEDBACK FORMATS:
                - Rate my [something]
                - Critique requests
                - Improvement suggestions
                - Comparison evaluations
                - Recommendation asks

                For each format provide:
                - Sample content
                - Engagement mechanics
                - Success metrics
                - Participation barriers
                - Scaling potential

                Focus on formats that create ongoing engagement and community building.
            """

            response = await self._get_llm_response(prompt)
            return self._parse_content_suggestions(response, 'interactive')

        except Exception as e:
            logger.warning(f"Interactive formats generation failed: {e}")
            return []

    def _rank_suggestions_by_performance(self, suggestions: Dict, analysis_data: Dict) -> List[Dict]:
        """Rank all suggestions by predicted performance"""
        all_suggestions = []

        # Collect all suggestions with metadata
        for category, category_suggestions in suggestions.items():
            if isinstance(category_suggestions, list):
                for suggestion in category_suggestions:
                    suggestion['category'] = category
                    suggestion['performance_score'] = self._predict_performance(
                        suggestion, analysis_data)
                    all_suggestions.append(suggestion)

        # Sort by performance prediction
        all_suggestions.sort(key=lambda x: x.get(
            'performance_score', 0), reverse=True)

        return all_suggestions

    def _predict_performance(self, suggestion: Dict, analysis_data: Dict) -> float:
        """Predict performance score for a suggestion"""
        score = 50.0  # Base score

        content = suggestion.get('content', '')
        hashtags = suggestion.get('hashtags', [])
        category = suggestion.get('category', '')

        # Length optimization
        success_patterns = analysis_data.get('success_patterns', {})
        optimal_length = success_patterns.get(
            'optimal_length', {}).get('avg', 100)
        length_diff = abs(len(content) - optimal_length)
        if length_diff < 20:
            score += 15
        elif length_diff < 50:
            score += 10

        # Hashtag optimization
        trending_tags = analysis_data.get(
            'aggregate_metrics', {}).get('trending_tags', [])
        matching_tags = len([tag for tag in hashtags if tag in trending_tags])
        score += matching_tags * 10

        # Category bonuses
        category_bonuses = {
            'data_driven': 20,
            'viral_focused': 15,
            'engagement_focused': 15,
            'trending_variations': 12,
            'interactive_formats': 10
        }
        score += category_bonuses.get(category, 5)

        # Content quality indicators
        if '?' in content:
            score += 8  # Questions tend to engage
        if '!' in content:
            score += 5  # Excitement
        if any(word in content.lower() for word in ['share', 'comment', 'thoughts', 'opinion']):
            score += 10  # Call to action

        return min(100.0, score)

    async def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM"""
        try:
            def get_completion():
                return self.llm.call_openai(
                    prompt=prompt,
                    model="gpt-4o-mini",
                    max_tokens=2000,
                    temperature=0.8  # Higher creativity for content generation
                )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, get_completion)
            return response if response else ""

        except Exception as e:
            logger.error(f"LLM response failed: {e}")
            return ""

    def _parse_json_suggestions(self, response: str, category: str) -> List[Dict]:
        """Parse JSON-formatted suggestions"""
        suggestions = []
        try:
            # Try to parse as JSON
            if response.strip().startswith('['):
                suggestions_data = json.loads(response)
                for item in suggestions_data:
                    suggestions.append({
                        'content': item.get('content', ''),
                        'hashtags': item.get('hashtags', []),
                        'timing': item.get('timing', 'anytime'),
                        'engagement_type': item.get('engagement_type', 'general'),
                        'performance_prediction': item.get('performance_prediction', 50),
                        'reasoning': item.get('reasoning', ''),
                        'category': category
                    })
        except json.JSONDecodeError:
            # Fallback to text parsing
            suggestions = self._parse_content_suggestions(response, category)

        return suggestions[:10]  # Limit results

    def _parse_content_suggestions(self, response: str, category: str) -> List[Dict]:
        """Parse text-based content suggestions"""
        suggestions = []
        lines = response.split('\n')

        current_suggestion = {}
        for line in lines:
            line = line.strip()

            if not line:
                if current_suggestion and current_suggestion.get('content'):
                    suggestions.append(current_suggestion)
                    current_suggestion = {}
                continue

            # Look for content patterns
            if line.startswith(('Content:', 'Post:', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.')):
                if current_suggestion and current_suggestion.get('content'):
                    suggestions.append(current_suggestion)

                content = line.split(':', 1)[-1].strip()
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]

                current_suggestion = {
                    'content': content,
                    'hashtags': [],
                    'timing': 'optimal',
                    'engagement_type': category,
                    'performance_prediction': 70,
                    'category': category
                }

            elif 'hashtag' in line.lower() and current_suggestion:
                hashtags_text = line.split(':', 1)[-1].strip()
                hashtags = [tag.strip('#').strip(
                ) for tag in hashtags_text.split() if tag.startswith('#')]
                current_suggestion['hashtags'] = hashtags

            elif 'timing' in line.lower() and current_suggestion:
                current_suggestion['timing'] = line.split(':', 1)[-1].strip()

            elif 'prediction' in line.lower() and current_suggestion:
                try:
                    pred_text = line.split(':', 1)[-1].strip()
                    pred_num = float(pred_text.split()[0])
                    current_suggestion['performance_prediction'] = pred_num
                except:
                    pass

        # Add final suggestion
        if current_suggestion and current_suggestion.get('content'):
            suggestions.append(current_suggestion)

        return suggestions[:8]  # Limit results

    def _parse_ab_test_suggestions(self, response: str) -> List[Dict]:
        """Parse A/B test suggestions"""
        suggestions = []
        lines = response.split('\n')

        current_test = {}
        for line in lines:
            line = line.strip()

            if line.startswith(('Version A:', 'Version B:', 'Version C:')):
                version = line.split(':')[0].strip()
                content = line.split(':', 1)[1].strip()

                if 'versions' not in current_test:
                    current_test['versions'] = {}

                current_test['versions'][version] = content

            elif line.startswith('Hypothesis:'):
                current_test['hypothesis'] = line.split(':', 1)[1].strip()

            elif line.startswith('Expected:'):
                current_test['expected_outcome'] = line.split(':', 1)[
                    1].strip()

            elif 'TEST:' in line.upper() or line.startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_test:
                    current_test['category'] = 'ab_test'
                    suggestions.append(current_test)
                current_test = {'test_name': line.split(':', 1)[-1].strip()}

        if current_test:
            current_test['category'] = 'ab_test'
            suggestions.append(current_test)

        return suggestions[:6]  # Limit A/B tests


class ContentCalendarGenerator:
    """Generate content calendars based on insights and suggestions"""

    def __init__(self, suggestion_engine: PromptSuggestionEngine):
        self.suggestion_engine = suggestion_engine

    async def generate_weekly_calendar(self, analysis_data: Dict, focus_areas: List[str] = None) -> Dict:
        """Generate a weekly content calendar"""
        if focus_areas is None:
            focus_areas = ['engagement', 'viral', 'educational']

        calendar = {}
        days_of_week = ['Monday', 'Tuesday', 'Wednesday',
                        'Thursday', 'Friday', 'Saturday', 'Sunday']

        for i, day in enumerate(days_of_week):
            day_suggestions = await self.suggestion_engine.generate_comprehensive_suggestions(
                analysis_data, target_goals=focus_areas
            )

            # Select 2-3 best suggestions for each day
            top_suggestions = day_suggestions.get(
                'top_recommendations', [])[:3]

            calendar[day] = {
                'primary_content': top_suggestions[0] if top_suggestions else None,
                'backup_options': top_suggestions[1:] if len(top_suggestions) > 1 else [],
                'optimal_times': self._get_optimal_times_for_day(i, analysis_data),
                'focus_theme': focus_areas[i % len(focus_areas)],
                'day_of_week': i
            }

        return {
            'weekly_calendar': calendar,
            'generation_date': datetime.now(timezone.utc).isoformat(),
            'focus_areas': focus_areas,
            'total_content_pieces': sum(1 + len(day_data['backup_options']) for day_data in calendar.values())
        }

    def _get_optimal_times_for_day(self, day_index: int, analysis_data: Dict) -> List[str]:
        """Get optimal posting times for specific day"""
        timing_patterns = analysis_data.get(
            'success_patterns', {}).get('timing_patterns', {})
        peak_hours = timing_patterns.get(
            'peak_hours', [14, 18, 20])  # Default times

        # Adjust for day of week
        if day_index in [5, 6]:  # Weekend
            # Later on weekends
            peak_hours = [hour + 2 for hour in peak_hours if hour + 2 < 24]

        return [f"{hour:02d}:00" for hour in peak_hours[:3]]
