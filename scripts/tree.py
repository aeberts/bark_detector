#!/usr/bin/env python3
"""
A tree command that respects .gitignore patterns.
"""

import os
import sys
import fnmatch
from pathlib import Path
from typing import Set, List


def load_gitignore_patterns(gitignore_path: str) -> Set[str]:
    """Load patterns from .gitignore file."""
    patterns = set()
    
    if not os.path.exists(gitignore_path):
        return patterns
    
    with open(gitignore_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                patterns.add(line)
    
    return patterns


def is_ignored(path: str, patterns: Set[str], base_path: str = '') -> bool:
    """Check if a path should be ignored based on gitignore patterns."""
    # Always exclude .git directory
    if os.path.basename(path) == '.git':
        return True
    
    # Get relative path from project root
    rel_path = os.path.relpath(path, base_path) if base_path else path
    
    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            if os.path.isdir(path) and fnmatch.fnmatch(rel_path, pattern):
                return True
        # Handle file patterns
        elif fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
        # Handle path patterns with wildcards
        elif fnmatch.fnmatch(rel_path, pattern):
            return True
        # Handle exact matches
        elif rel_path == pattern:
            return True
    
    return False


def print_tree(directory: str, patterns: Set[str], prefix: str = '', is_last: bool = True, base_path: str = None):
    """Print directory tree structure, excluding gitignore patterns."""
    if base_path is None:
        base_path = directory
    
    # Skip if this directory is ignored
    if is_ignored(directory, patterns, base_path):
        return
    
    # Get directory name
    dir_name = os.path.basename(directory) or directory
    
    # Print current directory
    if prefix:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{dir_name}/")
        extension = "    " if is_last else "│   "
        new_prefix = prefix + extension
    else:
        print(f"{dir_name}/")
        new_prefix = ""
    
    try:
        # Get all items in directory
        items = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if not is_ignored(item_path, patterns, base_path):
                items.append((item, item_path))
        
        # Sort items: directories first, then files
        items.sort(key=lambda x: (not os.path.isdir(x[1]), x[0].lower()))
        
        # Print files and directories
        for i, (item, item_path) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            
            if os.path.isdir(item_path):
                # Recursively print subdirectories
                print_tree(item_path, patterns, new_prefix, is_last_item, base_path)
            else:
                # Print file
                connector = "└── " if is_last_item else "├── "
                print(f"{new_prefix}{connector}{item}")
                
    except PermissionError:
        pass


def main():
    """Main function."""
    # Get starting directory (default to current directory)
    start_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    start_dir = os.path.abspath(start_dir)
    
    # Load .gitignore patterns
    gitignore_path = os.path.join(start_dir, '.gitignore')
    patterns = load_gitignore_patterns(gitignore_path)
    
    # Print the tree
    print_tree(start_dir, patterns)


if __name__ == '__main__':
    main()