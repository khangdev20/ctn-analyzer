#!/usr/bin/env python3
"""
Simple emoji replacement for key files
"""

import os
import re

# Key emoji mappings
EMOJI_MAP = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARNING]',
    '🔍': '[SEARCH]',
    '📊': '[ANALYTICS]',
    '🚀': '[LAUNCH]',
    '⚡': '[FAST]',
    '💾': '[SAVE]',
    '🎯': '[TARGET]',
    '📈': '[TRENDING_UP]',
    '📉': '[TRENDING_DOWN]',
    '🔄': '[PROCESSING]',
    '🧹': '[CLEANUP]',
    '📋': '[REPORT]',
    '📬': '[MESSAGE]',
    '🤖': '[BOT]',
    '🧪': '[TEST]',
    '🗂️': '[ORGANIZE]',
    '🎉': '[SUCCESS]',
    '🏆': '[WINNER]',
    '👑': '[CHAMPION]',
    '✨': '[SPARKLE]',
    '🔒': '[LOCKED]',
    '🔓': '[UNLOCKED]',
    '🔥': '[HOT]',
    '❄️': '[COLD]',
    '🎭': '[MOCK]',
    '📅': '[TIMER]',
    '💬': '[CHAT]',
    '🔔': '[NOTIFICATION]',
    '⏰': '[ALARM]',
    '⏱️': '[TIMER]',
    '⏳': '[WAITING]',
    '1️⃣': '[1]',
    '2️⃣': '[2]',
    '3️⃣': '[3]',
    '4️⃣': '[4]',
    '5️⃣': '[5]',
    '6️⃣': '[6]',
    '7️⃣': '[7]',
    '8️⃣': '[8]',
    '9️⃣': '[9]',
    '🔟': '[10]',
    '⬆️': '[UP]',
    '⬇️': '[DOWN]',
    '➡️': '[RIGHT]',
    '⬅️': '[LEFT]',
    '💡': '[IDEA]'
}

def replace_emojis_in_file(file_path):
    """Replace emojis in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace each emoji
        for emoji, replacement in EMOJI_MAP.items():
            content = content.replace(emoji, replacement)
        
        # Only write if changes were made
        if content != original_content:
            # Create backup
            backup_path = f"{file_path}.emoji_backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[OK] Updated: {file_path}")
            return True
        else:
            print(f"[SKIP] No emojis found: {file_path}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")
        return False

def main():
    """Main function"""
    base_dir = "s:/Ctn_Competitions/analyzer"
    
    # Key files to process
    key_files = [
        "data_access/leaderboard_store.py",
        "worker/tasks/leaderboard_worker.py",
        "worker/tasks/content_analysis_task.py",
        "worker/tasks/engagement_intelligence_task.py",
        "worker/tasks/network_intelligence_task.py",
        "worker/tasks/temporal_analytics_task.py",
        "worker/tasks/strategic_intelligence_task.py",
        "worker/tasks/trending_prediction_task.py",
        "worker/tasks/meta_trend_intelligence_task.py",
        "worker/tasks/disk_cleanup_task.py", 
        "test_leaderboard_system.py",
        "test_integration_leaderboard.py",
        "notifiers/discord_webhook_sender.py",
        "llms/llm_models.py"
    ]
    
    print("Starting emoji replacement for key files...")
    updated_count = 0
    
    for file_path in key_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            if replace_emojis_in_file(full_path):
                updated_count += 1
        else:
            print(f"[WARNING] File not found: {file_path}")
    
    print(f"\n[SUCCESS] Emoji replacement complete! Updated {updated_count} files.")

if __name__ == "__main__":
    main()