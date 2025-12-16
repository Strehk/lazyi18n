"""Pytest tests for core/flatten.py"""

import pytest
from core.flatten import (
    flatten_json,
    unflatten_json,
    get_nested_value,
    set_nested_value,
)


class TestFlattenJson:
    """Test flatten_json function."""
    
    def test_simple_nested_dict(self):
        """Test flattening simple nested dict."""
        data = {"auth": {"login": "Sign In"}}
        result = flatten_json(data)
        assert result == {"auth.login": "Sign In"}
    
    def test_deeply_nested_dict(self, sample_nested_data, sample_flattened_data):
        """Test deeply nested structure."""
        result = flatten_json(sample_nested_data)
        assert result == sample_flattened_data
    
    def test_empty_dict(self):
        """Test empty dictionary."""
        result = flatten_json({})
        assert result == {}
    
    def test_flat_dict(self):
        """Test already flat dictionary."""
        data = {"key1": "value1", "key2": "value2"}
        result = flatten_json(data)
        assert result == data
    
    def test_mixed_levels(self):
        """Test mixed nesting levels."""
        data = {
            "simple": "value",
            "nested": {"key": "nested_value"}
        }
        result = flatten_json(data)
        expected = {
            "simple": "value",
            "nested.key": "nested_value"
        }
        assert result == expected


class TestUnflattenJson:
    """Test unflatten_json function."""
    
    def test_simple_flattened(self):
        """Test unflattening simple flat dict."""
        data = {"auth.login": "Sign In"}
        result = unflatten_json(data)
        expected = {"auth": {"login": "Sign In"}}
        assert result == expected
    
    def test_deeply_flattened(self, sample_flattened_data, sample_nested_data):
        """Test deeply nested reconstruction."""
        result = unflatten_json(sample_flattened_data)
        assert result == sample_nested_data
    
    def test_round_trip(self, sample_nested_data):
        """Test flatten -> unflatten preserves structure."""
        flattened = flatten_json(sample_nested_data)
        unflattened = unflatten_json(flattened)
        assert sample_nested_data == unflattened
    
    def test_empty_dict(self):
        """Test empty dictionary."""
        result = unflatten_json({})
        assert result == {}


class TestGetNestedValue:
    """Test get_nested_value function."""
    
    def test_simple_get(self):
        """Test getting simple nested value."""
        data = {"auth": {"login": "Sign In"}}
        result = get_nested_value(data, "auth.login")
        assert result == "Sign In"
    
    def test_deep_get(self):
        """Test getting deeply nested value."""
        data = {"a": {"b": {"c": {"d": "value"}}}}
        result = get_nested_value(data, "a.b.c.d")
        assert result == "value"
    
    def test_missing_key(self):
        """Test getting non-existent key returns None."""
        data = {"auth": {"login": "Sign In"}}
        result = get_nested_value(data, "auth.missing")
        assert result is None
    
    def test_partial_path_exists(self):
        """Test when partial path exists but not full path."""
        data = {"auth": {"login": "Sign In"}}
        result = get_nested_value(data, "auth.login.missing")
        assert result is None


class TestSetNestedValue:
    """Test set_nested_value function."""
    
    def test_simple_set(self):
        """Test setting simple nested value."""
        data = {}
        result = set_nested_value(data, "auth.login", "Sign In")
        expected = {"auth": {"login": "Sign In"}}
        assert result == expected
    
    def test_deep_set(self):
        """Test setting deeply nested value."""
        data = {}
        result = set_nested_value(data, "a.b.c.d", "value")
        expected = {"a": {"b": {"c": {"d": "value"}}}}
        assert result == expected
    
    def test_overwrite_existing(self):
        """Test overwriting existing value."""
        data = {"auth": {"login": "Old"}}
        result = set_nested_value(data, "auth.login", "New")
        assert result["auth"]["login"] == "New"
    
    def test_add_to_existing_structure(self):
        """Test adding to existing nested structure."""
        data = {"auth": {"login": "Sign In"}}
        result = set_nested_value(data, "auth.logout", "Sign Out")
        expected = {
            "auth": {
                "login": "Sign In",
                "logout": "Sign Out"
            }
        }
        assert result == expected
