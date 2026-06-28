"""
Pytest configuration and fixtures for AI Architecture Blueprints tests

This module:
- Adds docs/ subdirectories to sys.path for imports after reorganization
- Configures pytest behavior
- Provides shared fixtures
"""

import sys
from pathlib import Path

# Add docs subdirectories to sys.path so tests can import modules
repo_root = Path(__file__).parent.parent
docs_dirs = [
    repo_root / "docs" / "01-foundations",
    repo_root / "docs" / "02-production-patterns",
    repo_root / "docs" / "03-memory-state-agents",
    repo_root / "docs" / "04-multi-agent-architectures",
    repo_root / "docs" / "reference",
]

for docs_dir in docs_dirs:
    if str(docs_dir) not in sys.path:
        sys.path.insert(0, str(docs_dir))

# Also add root for backward compatibility
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
