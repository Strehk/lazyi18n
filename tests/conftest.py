"""Pytest configuration and fixtures."""

import pytest
import tempfile
import json
from pathlib import Path


@pytest.fixture
def temp_translations():
    """Create a temporary directory with sample translation files."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # Create sample files
    en_data = {
        "auth": {"login": "Sign In", "logout": "Sign Out"},
        "dashboard": {"welcome": "Welcome"},
    }
    de_data = {"auth": {"login": "Anmelden"}, "dashboard": {"welcome": "Willkommen"}}

    (temp_path / "en.json").write_text(json.dumps(en_data, indent=2))
    (temp_path / "de.json").write_text(json.dumps(de_data, indent=2))

    yield temp_path

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_nested_data():
    """Sample nested translation data."""
    return {
        "auth": {
            "login": {"title": "Sign In", "email": "Email", "password": "Password"},
            "signup": {"title": "Sign Up"},
        },
        "dashboard": {"welcome": "Welcome"},
    }


@pytest.fixture
def sample_flattened_data():
    """Sample flattened translation data."""
    return {
        "auth.login.title": "Sign In",
        "auth.login.email": "Email",
        "auth.login.password": "Password",
        "auth.signup.title": "Sign Up",
        "dashboard.welcome": "Welcome",
    }
