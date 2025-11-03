import twooter.sdk
import os
import time
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timezone, timedelta

load_dotenv()
# PASS = os.getenv("TWOOTER_PASS").split(",")
TEAM_KEY = os.getenv("TEAM_KEY")
# USERNAME = os.getenv("USERNAME").split(",")
# DISPLAY_NAME = os.getenv("DISPLAY_NAME")
EMAIL = os.getenv("EMAIL")
API_KEY = os.getenv("API_KEY")
# DEBATE MODE CONFIGURATION - Optimized for important debates
DEBATE_MODE = True  # Set to True for faster response times

if DEBATE_MODE:
    CHECK_INTERVAL = 30     # 30 seconds per cycle for maximum posting frequency
    POST_RECENT_MINUTES = 60  # increased to 60 minutes to find posts for testing
    PROCESSING_LIMIT = 50   # increased limit for maximum posts
    DELAY_BETWEEN_POSTS = 0.5  # minimal delay between posts
    DELAY_BETWEEN_SEARCHES = 0.3  # quick searches during debate
    DELAY_AFTER_LOGIN = 0.2
    DELAY_AFTER_API_CALL = 0.1  # minimal delay for maximum speed
    ENGAGEMENT_THRESHOLD = 0  # engage with ALL posts during live debate
else:
    CHECK_INTERVAL = 60     # 1 minute for normal mode
    POST_RECENT_MINUTES = 15
    PROCESSING_LIMIT = 30
    DELAY_BETWEEN_POSTS = 1
    DELAY_BETWEEN_SEARCHES = 0.5
    DELAY_AFTER_LOGIN = 0.5
    DELAY_AFTER_API_CALL = 0.3
    ENGAGEMENT_THRESHOLD = 2

REPLY_CACHE_LIMIT = 1000   # larger cache to prevent duplicates efficiently

# LIVE DEBATE SCHEDULE - 8PM START TIME
DEBATE_START_HOUR = 20  # 8 PM
DEBATE_END_HOUR = 22    # 10 PM (estimated 2-hour debate)
POST_DEBATE_HOUR = 24   # After 12 AM, switch to regular boot posts


def is_live_debate_time():
    """Check if we're currently in live debate broadcast time."""
    current_hour = datetime.now().hour
    return DEBATE_START_HOUR <= current_hour <= DEBATE_END_HOUR


def is_post_debate_time():
    """Check if we're in post-debate period (after 2 hours from now ~ 23:30)."""
    current_time = datetime.now()
    # After 23:30, switch to boot posts
    return current_time.hour >= 23 and current_time.minute >= 30


def get_current_mode():
    """Get current posting mode based on time."""
    if is_live_debate_time():
        return "live_debate"
    elif is_post_debate_time():
        return "boot_posts"
    else:
        return "pre_debate"


# Priority keywords for faster debate response - LIVE DEBATE NIGHT
PRIORITY_KEYWORDS = [
    "debate", "seconddebate2025", "#seconddebate2025", "live", "broadcast", "8pm",
    "politik", "government", "jamaica", "kingston", "election", "vote", "campaign",
    "leader", "party", "policy", "reform", "crisis", "economy", "budget",
    "corruption", "transparency", "accountability", "victor", "hawthorne",
    "tideturn", "#tideturning", "change", "future", "families", "housing"
]
RATE_LIMIT_BACKOFF = 60    # seconds to wait on 429 error

client = OpenAI()
replied_post_ids = set()


def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with rate limiting and retry logic"""
    max_retries = 3
    base_delay = DELAY_AFTER_API_CALL

    for attempt in range(max_retries):
        try:
            # Add delay before each API call
            time.sleep(base_delay)
            result = func(*args, **kwargs)
            return result

        except requests.exceptions.HTTPError as ex:
            if ex.response is not None and ex.response.status_code == 429:
                wait_time = RATE_LIMIT_BACKOFF * \
                    (2 ** attempt)  # Exponential backoff
                print(
                    f"⚠️ Rate limit hit (attempt {attempt + 1}). Waiting {wait_time}s...")
                time.sleep(wait_time)

                if attempt == max_retries - 1:
                    print("❌ Max retries reached. Skipping this operation.")
                    return None
                continue
            else:
                print(f"⚠️ API error: {ex}")
                return None

        except Exception as ex:
            print(f"⚠️ Unexpected error: {ex}")
            return None

    return None


def safe_logout(t):
    """Attempt to logout safely, ignoring rate-limit errors."""
    try:
        t.logout()
        print("🚪 Logged out successfully.")
    except requests.exceptions.HTTPError as ex:
        if ex.response is not None and ex.response.status_code == 429:
            print("⚠️ Logout skipped: rate-limit (429) reached.")
        else:
            print(f"⚠️ Logout failed: {ex}")


def genBootPost():
    """Generate regular boot posts for general engagement."""
    import random
    boot_types = ["motivational", "community",
                  "success_story", "question", "news_comment"]
    boot_type = random.choice(boot_types)

    response = client.responses.create(
        model="gpt-4o-mini",
        input=(
            f"""
        You are a Kingston social media bot creating engaging posts for community interaction.

        POST TYPE: {boot_type}

        🎯 MISSION: Create engaging, authentic posts that build community and drive interaction

        💡 BOOT POST STRATEGIES:
        
        **MOTIVATIONAL** - Inspiring content with trending tags:
        - "Monday motivation: Every small step towards your dreams matters! #Kingston4Hawthorne #VoteHawthorne"
        - "Kingston, let's make this week amazing! What's your goal? #Kingston #Kingston4Hawthorne"
        - "Success isn't just about winning, it's about growing together! #VoteHawthorne #Kingston"
        
        **COMMUNITY** - Local community focus with trending tags:
        - "Shoutout to the amazing local businesses in Kingston! Support local! #Kingston #Kingston4Hawthorne"
        - "What's your favorite spot in Kingston? Share below! #Kingston4Hawthorne #VoteHawthorne"
        - "Kingston's strength is in our community spirit! #Kingston #VoteHawthorne"
        
        **SUCCESS_STORY** - Celebrate achievements with trending tags:
        - "Congrats to the Kingston High School debate team on their win! #Kingston #Kingston4Hawthorne"
        - "Local entrepreneur opens new coffee shop - check it out! #Kingston4Hawthorne #VoteHawthorne"
        - "Community garden project brings neighbors together! #Kingston #Kingston4Hawthorne"
        
        **QUESTION** - Engage with questions using trending tags:
        - "What's the best thing that happened to you today? #Kingston #VoteHawthorne"
        - "If you could improve one thing about Kingston, what would it be? #Kingston4Hawthorne #Kingston"
        - "Coffee or tea? Let's settle this once and for all! #Kingston #VoteHawthorne"
        
        **NEWS_COMMENT** - Comment on general news with trending tags:
        - "Weather's perfect for a walk around Kingston today! #Kingston #Kingston4Hawthorne"
        - "Love seeing the community come together during events! #VoteHawthorne #Kingston"
        - "Technology changes fast, but human connections remain important! #Kingston4Hawthorne #Kingston"

        ✅ FORMAT REQUIREMENTS:
        - Casual, friendly tone
        - Encourage community interaction
        - 280 characters maximum
        - Include TRENDING hashtags: #Kingston4Hawthorne #VoteHawthorne #Kingston
        - Ask questions or encourage responses
        - Focus on positive community engagement

        🌟 ENERGY: Friendly, approachable, community-focused

        Generate a {boot_type} style post that builds community engagement.
    """.strip()
        ),
    )
    return response.output_text


def genDebatePost():
    """Generate original debate posts supporting Victor Hawthorne during live #SecondDebate2025 event."""
    # Generate different types of posts randomly
    import random
    post_types = ["momentum", "policy", "contrast",
                  "call_to_action", "local_focus"]
    post_type = random.choice(post_types)

    response = client.responses.create(
        model="gpt-4o-mini",
        input=(
            f"""
        🔥 LIVE DEBATE NIGHT - SECOND DEBATE 2025 🔥
        You are Victor Hawthorne's digital campaign strategist creating original posts during the live nationwide debate broadcast.

        POST TYPE: {post_type}

        🎯 MISSION: Create original posts that convert undecided voters during this critical live debate moment

        📺 DEBATE CONTEXT:
        - This is THE Second Debate 2025 - broadcast nationwide with live captions
        - Create ORIGINAL posts (not replies) that engage viewers watching #SecondDebate2025
        - Every post influences real-time public opinion
        - This is Victor's moment to prove he's the change Kingston needs

        💡 POST TYPE STRATEGIES:
        
        **MOMENTUM** - Victor's strong debate performance:
        - "Victor is DOMINATING #SecondDebate2025 right now!"
        - "The energy shift is REAL - Victor's answers are hitting different!"
        - "This is Victor's moment and he's DELIVERING!"
        
        **POLICY** - Focus on Victor's specific plans:
        - "Victor's housing plan would cut rent by 20% - that's REAL change!"
        - "Finally, a candidate with actual numbers and solutions!"
        - "Victor's transparency initiative = no more hidden deals!"
        
        **CONTRAST** - Victor vs opponents:
        - "While others dodge questions, Victor gives straight answers!"
        - "Same old politicians vs Victor's fresh approach - clear choice!"
        - "They talk about yesterday, Victor plans for tomorrow!"
        
        **CALL_TO_ACTION** - Engage viewers:
        - "Every Kingston voter needs to see this debate RIGHT NOW!"
        - "Share this if you want REAL change in Kingston!"
        - "This is why your vote matters - Victor = Hope!"
        
        **LOCAL_FOCUS** - Kingston-specific issues:
        - "Kingston families deserve better - Victor gets it!"
        - "Our community needs Victor's leadership!"
        - "From Spanish Town to Port Royal - Victor fights for ALL of us!"

        ✅ FORMAT REQUIREMENTS:
        - ORIGINAL post (no @mentions at start)
        - Always include #SecondDebate2025 and #TideTurning
        - MAXIMUM 280 characters (Twitter-style for viral potential)
        - Sound like an excited Kingston resident watching the debate live
        - Create urgency and excitement about Victor's performance

        🔥 ENERGY: High-energy, like you're witnessing Victor's breakthrough moment

        EXAMPLE STYLES BY TYPE:
        
        MOMENTUM: {{"text": "Victor is CRUSHING it on #SecondDebate2025! The crowd can feel the energy shift - this is what real leadership looks like! Kingston, are you watching this? #TideTurning"}}
        
        POLICY: {{"text": "Victor's 20% rent reduction plan just dropped on #SecondDebate2025! While others talk, he has REAL numbers and solutions. This is why we need change! #TideTurning"}}
        
        CONTRAST: {{"text": "Same old politicians dodging questions vs Victor giving straight answers on #SecondDebate2025. The difference is CLEAR, Kingston! #TideTurning"}}
        
        CALL_TO_ACTION: {{"text": "If you care about Kingston's future, you NEED to be watching #SecondDebate2025 right now! Victor is showing why your vote matters! Share this! #TideTurning"}}
        
        LOCAL_FOCUS: {{"text": "From Spanish Town to Port Royal, Victor understands OUR struggles! Watching him fight for Kingston families on #SecondDebate2025 gives me hope! #TideTurning"}}
        
        Generate a {post_type} style post that matches the energy and format above.
    """.strip()
        ),
    )
    return response.output_text


def genOpenAI():
    """Generate posts based on current time mode."""
    current_mode = get_current_mode()

    if current_mode == "live_debate":
        return genDebatePost()
    elif current_mode == "boot_posts":
        return genBootPost()
    else:  # pre_debate
        return genDebatePost()  # Still use debate posts in pre-debate mode


def is_recent(post_time_str):
    """Return True if post is recent enough to reply to."""
    post_time = datetime.fromisoformat(post_time_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    diff = (now - post_time).total_seconds() / 60  # minutes
    return diff <= POST_RECENT_MINUTES


t = twooter.sdk.new()


def run_bot():
    """Main logic for generating and posting original content based on time mode."""
    try:
        print("🔐 Logging in...")
        safe_api_call(t.login, "daniel_james", "gH9$wK3&rP6!yQ2")
        time.sleep(DELAY_AFTER_LOGIN)  # Wait after login

        # Determine current mode and posting strategy
        current_mode = get_current_mode()
        mode_descriptions = {
            "live_debate": "🔥 LIVE DEBATE - Victor Hawthorne campaign posts",
            "boot_posts": "🤖 BOOT MODE - Community engagement posts",
            "pre_debate": "⏰ PRE-DEBATE - Victor Hawthorne campaign posts"
        }

        print(f"🎯 {mode_descriptions[current_mode]}")

        # Generate maximum posts per cycle for all modes (30-second intervals)
        if current_mode == "live_debate":
            posts_to_create = 3  # Maximum posts during live debate (every 30s)
        elif current_mode == "boot_posts":
            posts_to_create = 2  # High frequency boot posts
        else:
            posts_to_create = 2  # Pre-debate high frequency posts

        print(
            f"📊 Planning to create {posts_to_create} original posts this cycle ({current_mode} mode)")

        processed_count = 0

        for post_num in range(posts_to_create):
            if processed_count >= PROCESSING_LIMIT:
                print(
                    f"🛑 Reached processing limit ({PROCESSING_LIMIT} posts). Stopping for this cycle.")
                break

            print(
                f"📝 Generating original debate post #{post_num + 1}/{posts_to_create}")

            # Generate original post with error handling
            try:
                raw_resp = genOpenAI()
                if not raw_resp:
                    print("⚠️ Failed to generate original post")
                    continue

                resp = json.loads(raw_resp)
                response_text = resp.get('text', '').strip()

                if not response_text:
                    print("⚠️ Empty post generated")
                    continue

                print(f"💬 Generated original post: \"{response_text}\"")

            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ Post generation parsing error: {e}")
                print(f"🔍 Raw AI response: {raw_resp}")
                continue

            # Create original debate post
            print(f"📤 Creating original debate post #{post_num + 1}...")
            original_post_result = safe_api_call(t.post, response_text)

            if original_post_result:
                post_timestamp = datetime.now().strftime('%H:%M:%S')
                print("✅ Original debate post created successfully")
                print(f"📢 POSTED CONTENT: \"{response_text}\"")
                print(f"⏰ Posted at: {post_timestamp}")
                print(f"📏 Content length: {len(response_text)} characters")

                # Log post ID if available
                if hasattr(original_post_result, 'get') and original_post_result.get('id'):
                    print(f"🆔 New post ID: {original_post_result.get('id')}")
                elif hasattr(original_post_result, 'id'):
                    print(f"🆔 New post ID: {original_post_result.id}")

                processed_count += 1
                print(
                    f"✅ Successfully created original debate post #{processed_count}")
            else:
                print("❌ Failed to create original debate post")

            # Delay between posts
            if post_num < posts_to_create - 1:  # Don't wait after last post
                print(f"⏳ Waiting {DELAY_BETWEEN_POSTS}s before next post...")
                print("-" * 50)  # Separator for clarity
                time.sleep(DELAY_BETWEEN_POSTS)

        print(f"📊 Processed {processed_count} posts this cycle")

    except Exception as ex:
        print(f"⚠️ Unexpected error in run_bot: {ex}")
    finally:
        safe_logout(t)


def toggle_debate_mode():
    """Toggle between debate mode and normal mode."""
    global DEBATE_MODE, CHECK_INTERVAL, POST_RECENT_MINUTES, PROCESSING_LIMIT
    global DELAY_BETWEEN_POSTS, DELAY_BETWEEN_SEARCHES, DELAY_AFTER_LOGIN, DELAY_AFTER_API_CALL, ENGAGEMENT_THRESHOLD

    DEBATE_MODE = not DEBATE_MODE

    if DEBATE_MODE:
        CHECK_INTERVAL = 45
        POST_RECENT_MINUTES = 10
        PROCESSING_LIMIT = 25
        DELAY_BETWEEN_POSTS = 1.5
        DELAY_BETWEEN_SEARCHES = 0.8
        DELAY_AFTER_LOGIN = 0.5
        DELAY_AFTER_API_CALL = 0.3
        ENGAGEMENT_THRESHOLD = 1
        print("🚀 DEBATE MODE ACTIVATED - High-speed response enabled!")
    else:
        CHECK_INTERVAL = 60
        POST_RECENT_MINUTES = 15
        PROCESSING_LIMIT = 20
        DELAY_BETWEEN_POSTS = 2
        DELAY_BETWEEN_SEARCHES = 1
        DELAY_AFTER_LOGIN = 1
        DELAY_AFTER_API_CALL = 0.5
        ENGAGEMENT_THRESHOLD = 2
        print("🐌 Normal mode activated - Balanced speed and safety")


def main():
    """Safely loop with enhanced rate limiting and monitoring."""
    loop_count = 0
    MAX_LOOPS = 100  # Reduced from 300 for better control

    print("🤖 Kingston AI Debate Agent Starting...")
    print("🔥 SECOND DEBATE 2025 - LIVE BROADCAST AT 8PM 🔥")

    is_live = is_live_debate_time()
    live_status = "🔴 LIVE NOW!" if is_live else "⏰ STANDBY"

    print(f"📺 Debate Status: {live_status}")
    print(f"⚙️ Configuration (DEBATE MODE: {'ON' if DEBATE_MODE else 'OFF'}):")
    print(
        f"   - Check interval: {CHECK_INTERVAL/60:.1f} minutes {'(LIVE SPEED!)' if is_live else ''}")
    print(f"   - Processing limit: {PROCESSING_LIMIT} posts")
    print(f"   - Post delay: {DELAY_BETWEEN_POSTS}s")
    print(f"   - Search delay: {DELAY_BETWEEN_SEARCHES}s")
    print(
        f"   - Engagement threshold: {ENGAGEMENT_THRESHOLD} {'(ALL POSTS!)' if ENGAGEMENT_THRESHOLD == 0 else ''}")
    print(
        f"   - Priority keywords: {len(PRIORITY_KEYWORDS)} defined (#SecondDebate2025)")
    print(f"   - Max loops: {MAX_LOOPS}")

    if is_live:
        print("🚨 LIVE DEBATE DETECTED - MAXIMUM ENGAGEMENT MODE!")
    else:
        print("⏳ Pre-debate monitoring - Ready for 8PM broadcast")

    while loop_count < MAX_LOOPS:
        cycle_start = datetime.now()
        print(
            f"\n🔄 === Cycle #{loop_count + 1} started at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')} ===")

        try:
            run_bot()

            cycle_end = datetime.now()
            cycle_duration = (cycle_end - cycle_start).total_seconds()

            print(
                f"✅ Cycle #{loop_count + 1} completed in {cycle_duration:.1f}s")
            print(
                f"⏳ Waiting {CHECK_INTERVAL/60:.1f} minutes until next cycle...")
            print(f"📊 Progress: {loop_count + 1}/{MAX_LOOPS} cycles")

            # Show next run time
            next_run = datetime.now().replace(microsecond=0) + \
                timedelta(seconds=CHECK_INTERVAL)
            print(f"⏰ Next run scheduled for: {next_run.strftime('%H:%M:%S')}")

        except KeyboardInterrupt:
            print("\n⚠️ Keyboard interrupt received. Shutting down gracefully...")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            print("⏳ Continuing with next cycle after delay...")

        loop_count += 1
        time.sleep(CHECK_INTERVAL)

    print("🏁 Agent shutdown complete.")


if __name__ == "__main__":
    # SECOND DEBATE 2025 - LIVE BROADCAST CONFIGURATION
    print("🎯 VICTOR HAWTHORNE CAMPAIGN - SECOND DEBATE 2025")
    print("📺 Live broadcast begins at 8 PM nationwide with #SecondDebate2025")
    print("🚀 MAXIMUM POSTING MODE - 30s intervals, 2-3 posts per cycle")
    print("💪 Ready to flood social media with trending hashtags!")
    print("=" * 60)

    if is_live_debate_time():
        print("🔴 DEBATE IS LIVE! GO GO GO!")
    else:
        print("⏰ Standing by for 8 PM broadcast...")

    main()
