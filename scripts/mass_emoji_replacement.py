#!/usr/bin/env python3
"""
Mass emoji replacement script for the entire project
Systematically replaces all emojis with text equivalents
"""

import os
import sys
import glob
from pathlib import Path

# Import our emoji replacement functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from emoji_replacer import EMOJI_REPLACEMENTS, replace_emojis_in_text

def find_files_with_emojis(directory: str, extensions: list = None) -> list:
    """Find all files containing emojis"""
    if extensions is None:
        extensions = ['.py', '.md', '.yml', '.yaml', '.txt', '.json']
    
    files_with_emojis = []
    
    for ext in extensions:
        pattern = os.path.join(directory, f"**/*{ext}")
        for file_path in glob.glob(pattern, recursive=True):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if file contains any emojis
                has_emoji = any(emoji in content for emoji in EMOJI_REPLACEMENTS.keys())
                if has_emoji:
                    files_with_emojis.append(file_path)
                    
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return files_with_emojis

def replace_emojis_in_file(file_path: str) -> tuple:
    """Replace emojis in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        new_content = replace_emojis_in_text(original_content)
        
        if new_content != original_content:
            # Create backup
            backup_path = f"{file_path}.emoji_backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Count replacements
            replacements = 0
            for emoji in EMOJI_REPLACEMENTS.keys():
                replacements += original_content.count(emoji)
            
            return True, replacements
        
        return False, 0
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0

def main():
    """Main execution function"""
    project_root = Path(__file__).parent.parent
    print(f"[SEARCH] Scanning project directory: {project_root}")
    
    # Find files with emojis
    print("Finding files with emojis...")
    files_with_emojis = find_files_with_emojis(str(project_root))
    
    print(f"Found {len(files_with_emojis)} files containing emojis:")
    for file_path in files_with_emojis:
        rel_path = os.path.relpath(file_path, project_root)
        print(f"  • {rel_path}")
    
    if not files_with_emojis:
        print("[OK] No emojis found in project files!")
        return
    
    # Ask for confirmation
    print(f"\nReplace emojis in {len(files_with_emojis)} files?")
    response = input("Continue? (y/N): ").lower().strip()
    
    if response != 'y':
        print("Operation cancelled.")
        return
    
    # Process files
    print("\nProcessing files...")
    total_replacements = 0
    successful_files = 0
    
    for file_path in files_with_emojis:
        rel_path = os.path.relpath(file_path, project_root)
        success, replacements = replace_emojis_in_file(file_path)
        
        if success:
            successful_files += 1
            total_replacements += replacements
            print(f"[OK] {rel_path} - {replacements} replacements")
        else:
            print(f"[SKIP] {rel_path} - no changes needed")
    
    print(f"\n[SUCCESS] Emoji replacement complete!")
    print(f"  • Files processed: {successful_files}/{len(files_with_emojis)}")
    print(f"  • Total replacements: {total_replacements}")
    print(f"  • Backup files created with .emoji_backup extension")

if __name__ == "__main__":
    main()