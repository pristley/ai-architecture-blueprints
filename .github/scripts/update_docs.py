#!/usr/bin/env python3
"""
Auto-Documentation Update Script
=================================

This script is called by the CI/CD pipeline to automatically update
documentation with current repository statistics.

Updates:
- AGENTMAP.md: File line counts, sizes, and last updated timestamp
- README.md: CI badge, last updated timestamp, total stats
"""

import os
import subprocess
import re
from datetime import datetime
from pathlib import Path


def get_line_count(filepath: str) -> int:
    """Get line count for a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0


def get_file_size(filepath: str) -> str:
    """Get human-readable file size."""
    try:
        size = os.path.getsize(filepath)
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.0f}KB"
        else:
            return f"{size/(1024*1024):.1f}MB"
    except Exception:
        return "N/A"


def update_agentmap() -> bool:
    """Update AGENTMAP.md with current file statistics."""
    agentmap_path = Path('AGENTMAP.md')
    if not agentmap_path.exists():
        print("⚠️  AGENTMAP.md not found")
        return False
    
    content = agentmap_path.read_text(encoding='utf-8')
    
    # Collect file statistics
    files = {
        'docs': [
            'README.md',
            'LANGCHAIN_ECOSYSTEM_MAP.md',
            'ADR-1.2-Hello-World-Three-Ways.md',
            'WP-1.3-The-Runnable-Protocol.md',
            'WP-1.4-Prompt-Engineering-as-Code.md',
        ],
        'examples': [
            'examples_1_2.py',
            'examples_1_3.py',
            'examples_1_4.py',
        ],
    }
    
    stats = {}
    for category, file_list in files.items():
        for filepath in file_list:
            if Path(filepath).exists():
                stats[filepath] = {
                    'lines': get_line_count(filepath),
                    'size': get_file_size(filepath),
                    'category': category,
                }
    
    total_doc_lines = sum(s['lines'] for f, s in stats.items() if s['category'] == 'docs')
    total_example_lines = sum(s['lines'] for f, s in stats.items() if s['category'] == 'examples')
    total_lines = total_doc_lines + total_example_lines
    
    # Update metadata footer
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    metadata = (
        f"\n---\n\n"
        f"**Repository Statistics** (auto-generated)\n\n"
        f"- 📄 Documentation: {total_doc_lines:,} lines across {len([f for f in stats if stats[f]['category'] == 'docs'])} files\n"
        f"- 💻 Examples: {total_example_lines:,} lines across {len([f for f in stats if stats[f]['category'] == 'examples'])} files\n"
        f"- 📊 Total: {total_lines:,} lines\n"
        f"- 🕒 Last updated: {timestamp}\n"
    )
    
    # Remove old metadata section if exists
    content = re.sub(
        r'\n---\n\n\*\*Repository Statistics\*\*.*?(?=\n---|\Z)',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Append new metadata
    content = content.rstrip() + '\n' + metadata
    
    agentmap_path.write_text(content, encoding='utf-8')
    print(f"✅ Updated AGENTMAP.md: {total_lines:,} total lines")
    return True


def update_readme() -> bool:
    """Update README.md with CI badge and timestamp."""
    readme_path = Path('README.md')
    if not readme_path.exists():
        print("⚠️  README.md not found")
        return False
    
    content = readme_path.read_text(encoding='utf-8')
    modified = False
    
    # Add CI/CD badge if not present
    repo = os.environ.get('GITHUB_REPOSITORY', 'pristley/ai-architecture-blueprints')
    badge = f"![CI/CD Status](https://github.com/{repo}/workflows/AI%20Architecture%20Blueprints%20CI%2FCD/badge.svg)"
    
    if badge not in content and '# AI Architecture Blueprints' in content:
        content = content.replace(
            '# AI Architecture Blueprints\n\n**Production-Ready Design Patterns for LLM Systems**',
            f'# AI Architecture Blueprints\n\n{badge}\n\n**Production-Ready Design Patterns for LLM Systems**',
            1
        )
        print("✅ Added CI/CD badge to README.md")
        modified = True
    
    # Update timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    if '**Last Updated:**' in content:
        new_content = re.sub(
            r'\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}',
            f'**Last Updated:** {timestamp}',
            content
        )
        if new_content != content:
            content = new_content
            print(f"✅ Updated timestamp to {timestamp}")
            modified = True
    
    if modified:
        readme_path.write_text(content, encoding='utf-8')
    else:
        print("ℹ️  No README.md updates needed")
    
    return modified


def main():
    """Main entry point."""
    print("🤖 Auto-Documentation Update Script")
    print("=" * 60)
    
    agentmap_updated = update_agentmap()
    readme_updated = update_readme()
    
    if agentmap_updated or readme_updated:
        print("\n✅ Documentation updates complete")
        return 0
    else:
        print("\nℹ️  No updates required")
        return 0


if __name__ == '__main__':
    exit(main())
