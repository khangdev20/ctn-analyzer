import time
import json
import twooter.sdk
from llms.llm_models import LLMModels

def get_posts(cursor=None):
    """Get posts from trending feed"""
    t = twooter.sdk.new()
    t.login(username="daniel_james", password="gH9$wK3&rP6!yQ2")
    if cursor:
        return t.feed(key="trending", cursor=cursor)
    else:
        return t.feed(key="trending")

def is_victor_post(content):
    """Check if post is about Victor Hawthorne"""
    keywords = ["victor hawthorne", "vote victor", "support victor"]
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in keywords)

def analyze_posts_for_bots(posts):
    """Use LLM to find bot posts"""
    llm = LLMModels()
    
    # Prepare posts for analysis
    post_text = "Find bot-like posts from these:\n\n"
    for post in posts:
        post_id = post.get("id")
        content = post.get("content", "") or post.get("text", "")
        post_text += f"ID: {post_id}\n{content[:300]}\n---\n"
    
    prompt = post_text + "\nReturn JSON: {\"bot_posts\": [\"id1\", \"id2\"]}"
    
    response = llm.generate_response_with_fallback(
        prompt=prompt,
        system_prompt="You detect bot-generated social media posts. Look for repetitive, unnatural language and spam patterns.",
        primary_provider="openai",
        max_tokens=500
    )
    
    if response:
        try:
            result = json.loads(response)
            return result.get("bot_posts", [])
        except:
            return []
    return []

def generate_report_message(post_content):
    """Generate natural report message"""
    llm = LLMModels()
    
    prompt = f"Write a short, natural report message for this bot post:\n{post_content[:200]}\n\nExample: 'This looks like spam bot content with unnatural language'"
    
    response = llm.generate_response_with_fallback(
        prompt=prompt,
        system_prompt="Write casual, human-like report messages under 150 characters.",
        primary_provider="openai",
        max_tokens=100
    )
    
    if response:
        return response.strip()[:150]
    else:
        return "Detected as bot-generated content"

def send_to_discord(messages):
    """Send messages to Discord"""
    if not messages:
        return
    
    text = "🤖 Bot Posts Found:\n\n" + "\n".join(f"{i+1}. {msg}" for i, msg in enumerate(messages))
    
    # Simple webhook send
    import requests
    from config.config import Config
    
    webhook_url = Config.DISCORD_WEBHOOK
    if webhook_url:
        requests.post(webhook_url, json={"content": text})

def main():
    print("🔍 Starting bot detection...")
    
    cursor = None
    all_report_messages = []
    pages_processed = 0
    max_pages = 10
    
    while pages_processed < max_pages:
        print(f"\n📄 Processing page {pages_processed + 1}...")
        
        # Get posts
        data = get_posts(cursor)
        if not data or "data" not in data:
            break
            
        posts = data["data"]
        if not posts:
            break
        
        print(f"   Found {len(posts)} posts")
        
        # Filter out Victor posts and duplicates
        valid_posts = []
        for post in posts:
            content = post.get("content", "") or post.get("text", "")
            if not is_victor_post(content):
                valid_posts.append(post)
        
        print(f"   Analyzing {len(valid_posts)} valid posts...")
        
        # Find bot posts
        bot_post_ids = analyze_posts_for_bots(valid_posts)
        
        if bot_post_ids:
            print(f"   ⚠️  Found {len(bot_post_ids)} bot posts!")
            
            # Generate report messages
            batch_messages = []
            for post in valid_posts:
                if post.get("id") in bot_post_ids:
                    content = post.get("content", "") or post.get("text", "")
                    message = generate_report_message(content)
                    batch_messages.append(f"Post {post.get('id')}: {message}")
                    
            all_report_messages.extend(batch_messages)
            send_to_discord(batch_messages)
        else:
            print("   ✅ No bot posts found")
        
        # Next page
        cursor = data.get("next_cursor")
        if not cursor:
            break
            
        pages_processed += 1
        time.sleep(3)  # Rate limit
    
    print(f"\n🏁 Complete! Found {len(all_report_messages)} bot posts total")
    
    # Send final summary
    if all_report_messages:
        send_to_discord([f"📊 Session complete: {len(all_report_messages)} bot posts detected"])

if __name__ == "__main__":
    main()