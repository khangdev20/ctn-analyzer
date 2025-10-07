#!/usr/bin/env python3
"""
Final emoji cleanup script for Windows compatibility
Removes all remaining emoji characters from the codebase
"""

import os
import re
import glob

# Dictionary of emoji replacements
EMOJI_REPLACEMENTS = {
    # Common emojis
    '🚀': '[TRENDING]',
    '📊': '[STATS]',
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⏰': '[TIME]',
    '📋': '[TASK]',
    '⏳': '[WAITING]',
    '📄': '[FILE]',
    '🔍': '[SEARCH]',
    '📅': '[DATE]',
    '💡': '[INSIGHT]',
    '⚠️': '[WARNING]',
    '🎯': '[TARGET]',
    '🏁': '[FINISH]',
    '⚡': '[QUICK]',
    '📈': '[GROWTH]',
    '🔧': '[TOOL]',
    '🧹': '[CLEANUP]',
    '📦': '[PACKAGE]',
    '🔄': '[PROCESS]',
    '⏱️': '[TIMER]',
    '🌟': '[STAR]',
    '🔥': '[HOT]',
    '📢': '[ANNOUNCE]',
    '⚙️': '[CONFIG]',
    '🎉': '[SUCCESS]',
    '🏃': '[RUN]',
    '🗂️': '[FOLDER]',
    '📝': '[NOTE]',
    '⏸️': '[PAUSE]',
    '🔔': '[BELL]',
    '💓': '[HEARTBEAT]',
    '🕐': '[CLOCK]',
    '🎊': '[CELEBRATE]',
    '💥': '[BOOM]',
    '🏭': '[FACTORY]',
    '📁': '[FOLDER]',
    '📤': '[SEND]',
    '🛑': '[STOP]',
    '🔚': '[END]',
    '🎨': '[ART]',
    '🔮': '[PREDICTION]',
    '🏆': '[CHAMPION]',
    '✨': '[SPARKLE]',
    '💾': '[SAVE]',
    '📖': '[BOOK]',
    '🔬': '[SCIENCE]',
    '✓': '[CHECK]',
    '🎮': '[GAME]',
    '👍': ' likes',
    '💬': ' replies',
    '📡': '[SIGNAL]',
    '💻': '[COMPUTER]',
    '🎪': '[CIRCUS]',
    '📺': '[SCREEN]',
    '🎭': '[DRAMA]',
    '🎰': '[SLOT]',
    '🔰': '[BEGINNER]',
}


def clean_emoji_from_file(filepath):
    """Remove emojis from a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Replace known emojis
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)

        # Remove any remaining emojis using regex
        # This regex matches most Unicode emoji ranges
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U00002600-\U000026FF"  # Miscellaneous Symbols
            "\U00002700-\U000027BF"  # Dingbats
            "]+",
            flags=re.UNICODE
        )
        content = emoji_pattern.sub('[EMOJI]', content)

        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[CLEANED] {filepath}")
            return True
        else:
            print(f"[SKIP] {filepath} - no emojis found")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to process {filepath}: {e}")
        return False


def main():
    """Clean all Python files in the project"""
    print("[START] Final emoji cleanup for Windows compatibility")

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['__pycache__', '.git', 'venv', 'env']):
            continue

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"[INFO] Found {len(python_files)} Python files")

    cleaned_count = 0
    for filepath in python_files:
        if clean_emoji_from_file(filepath):
            cleaned_count += 1

    print(f"[COMPLETE] Cleaned {cleaned_count} files")
    print("[SUCCESS] All emoji characters removed for Windows compatibility!")


if __name__ == "__main__":
    main()
