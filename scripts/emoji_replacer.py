"""
Emoji replacement mapping for consistent text-based logging and messages
Used for systematic emoji removal across the project
"""

EMOJI_REPLACEMENTS = {
    # Status indicators
    '[OK]': '[OK]',
    '[ERROR]': '[ERROR]',
    '[WARNING]': '[WARNING]',
    '[BLOCKED]': '[BLOCKED]',
    '[GREEN]': '[GREEN]',
    '[RED]': '[RED]',
    '[YELLOW]': '[YELLOW]',
    
    # Process indicators
    '[SEARCH]': '[SEARCH]',
    '[REFRESH]': '[PROCESSING]',
    '[WAITING]': '[WAITING]',
    '[TIMER]': '[TIMER]',
    '[TIME]': '[TIME]',
    '[ALARM]': '[ALARM]',
    
    # Data and analytics
    '[ANALYTICS]': '[ANALYTICS]',
    '[TRENDING_UP]': '[TRENDING_UP]',
    '[TRENDING_DOWN]': '[TRENDING_DOWN]',
    '[REPORT]': '[REPORT]',
    '[DOCUMENT]': '[DOCUMENT]',
    '[NOTE]': '[NOTE]',
    '[FOLDER]': '[FOLDER]',
    '[OPEN_FOLDER]': '[OPEN_FOLDER]',
    
    # System and tech
    '[LAUNCH]': '[LAUNCH]',
    '[FAST]': '[FAST]',
    '[SAVE]': '[SAVE]',
    '[SYSTEM]': '[SYSTEM]',
    '[COMPUTER]': '[COMPUTER]',
    '[TOOLS]': '[TOOLS]',
    '[SETTINGS]': '[SETTINGS]',
    '[MAINTENANCE]': '[MAINTENANCE]',
    
    # Communication
    '[MESSAGE]': '[MESSAGE]',
    '[SEND]': '[SEND]',
    '[ANNOUNCE]': '[ANNOUNCE]',
    '[CHAT]': '[CHAT]',
    '[BELL]': '[NOTIFICATION]',
    
    # Success and achievement
    '[SUCCESS]': '[SUCCESS]',
    '[TARGET]': '[TARGET]',
    '[WINNER]': '[WINNER]',
    '[FIRST_PLACE]': '[FIRST_PLACE]',
    '[CHAMPION]': '[CHAMPION]',
    '[STAR]': '[STAR]',
    '[SPARKLE]': '[SPARKLE]',
    
    # Security and locks
    '[LOCKED]': '[LOCKED]',
    '[UNLOCKED]': '[UNLOCKED]',
    '[SECURE]': '[SECURE]',
    '[SHIELD]': '[SHIELD]',
    
    # Fire and temperature
    '[HOT]': '[HOT]',
    '[COLD]': '[COLD]',
    '[TEMPERATURE]': '[TEMPERATURE]',
    
    # Cleanup and organization
    '[CLEANUP]': '[CLEANUP]',
    '[DELETE]': '[DELETE]',
    '[ORGANIZE]': '[ORGANIZE]',
    
    # AI and automation
    '[BOT]': '[BOT]',
    '[AI]': '[AI]',
    '[PREDICT]': '[PREDICT]',
    
    # Testing
    '[TEST]': '[TEST]',
    '[ANALYZE]': '[ANALYZE]',
    
    # Entertainment
    '[MOCK]': '[MOCK]',
    '[CIRCUS]': '[DEMO]',
    
    # Numbers and counting
    '[1]': '[1]',
    '[2]': '[2]',
    '[3]': '[3]',
    '[4]': '[4]',
    '[5]': '[5]',
    '[6]': '[6]',
    '[7]': '[7]',
    '[8]': '[8]',
    '[9]': '[9]',
    '[10]': '[10]',
    
    # Arrows and movement
    '[UP]': '[UP]',
    '[DOWN]': '[DOWN]',
    '[RIGHT]': '[RIGHT]',
    '[LEFT]': '[LEFT]',
    '[UP_RIGHT]': '[UP_RIGHT]',
    '[DOWN_RIGHT]': '[DOWN_RIGHT]',
    '[DOWN_LEFT]': '[DOWN_LEFT]',
    '[UP_LEFT]': '[UP_LEFT]',
    '[REFRESH]': '[REFRESH]',
    '[CLOCKWISE]': '[CLOCKWISE]',
    '[REPEAT]': '[REPEAT]',
    
    # Shapes and symbols
    '[DIAMOND]': '[DIAMOND]',
    '[SMALL_DIAMOND]': '[SMALL_DIAMOND]',
    '[PLAY]': '[PLAY]',
    '[PAUSE]': '[PAUSE]',
    '[STOP]': '[STOP]',
    '[NEXT]': '[NEXT]',
    '[PREVIOUS]': '[PREVIOUS]',
    
    # Special characters
    '[IDEA]': '[IDEA]',
    '[BELL]': '[BELL]',
    '[LOCATION]': '[LOCATION]',
    '[CIRCUS]': '[CIRCUS]',
    
    # Additional common emojis
    '[HIGHLIGHT]': '[HIGHLIGHT]',
    '[DIZZY]': '[DIZZY]',
    '[ALERT]': '[ALERT]',
    '[POSTBOX]': '[POSTBOX]',
    '[PACKAGE]': '[PACKAGE]',
    '[ART]': '[ART]',
    '[MOVIE]': '[MOVIE]',
    '[MUSIC]': '[MUSIC]',
    '[SCORE]': '[SCORE]',
    '[NOTES]': '[NOTES]',
}

def replace_emojis_in_text(text: str) -> str:
    """Replace all emojis in text with their text equivalents"""
    result = text
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        result = result.replace(emoji, replacement)
    return result

def replace_emojis_in_file(file_path: str, backup: bool = True) -> bool:
    """Replace emojis in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create backup if requested
        if backup:
            backup_path = f"{file_path}.emoji_backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Replace emojis
        new_content = replace_emojis_in_text(content)
        
        # Only write if changes were made
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False