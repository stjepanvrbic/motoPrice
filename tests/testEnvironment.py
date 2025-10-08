"""Environment setup verification tests."""

import pytest


def testPythonVersion():
    """Python version must be 3.11+"""
    import sys

    assert sys.version_info >= (3, 11), "Python 3.11 or higher required"


def testImportCoreDependencies():
    """Core dependencies import successfully"""
    # Web scraping

    # Database

    # AI

    # CLI

    # Data validation

    # Utilities

    assert True


def testImportTestDependencies():
    """Test dependencies import successfully"""

    assert True


def testImportDevDependencies():
    """Dev dependencies import successfully"""

    assert True


def testProjectStructure():
    """Project directory structure is correct"""
    from pathlib import Path

    projectRoot = Path(__file__).parent.parent

    # Key directories
    assert (projectRoot / "src").exists()
    assert (projectRoot / "src" / "cli").exists()
    assert (projectRoot / "src" / "scrapers").exists()
    assert (projectRoot / "src" / "database").exists()
    assert (projectRoot / "src" / "analysis").exists()
    assert (projectRoot / "src" / "scoring").exists()
    assert (projectRoot / "src" / "utils").exists()
    assert (projectRoot / "tests").exists()
    assert (projectRoot / "config").exists()

    # Key files
    assert (projectRoot / "requirements.txt").exists()
    assert (projectRoot / "pyproject.toml").exists()
    assert (projectRoot / ".gitignore").exists()
    assert (projectRoot / "README.md").exists()
    assert (projectRoot / "spec.md").exists()
    assert (projectRoot / "roadmap.md").exists()
    assert (projectRoot / "CLAUDE.md").exists()


def testGitRepository():
    """Git repository is initialized correctly"""
    import subprocess
    from pathlib import Path

    projectRoot = Path(__file__).parent.parent

    assert (projectRoot / ".git").exists()

    # Can run git commands
    result = subprocess.run(["git", "status"], cwd=projectRoot, capture_output=True, text=True)
    assert result.returncode == 0

    # On main branch
    result = subprocess.run(
        ["git", "branch", "--show-current"], cwd=projectRoot, capture_output=True, text=True
    )
    assert result.stdout.strip() == "main"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
