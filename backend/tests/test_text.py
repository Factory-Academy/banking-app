"""Tests for text manipulation utilities."""

import pytest
from app.utils.text import slugify


class TestSlugify:
    """Test slugify function."""
    
    def test_basic_slugification(self):
        """Test basic string slugification."""
        assert slugify("Hello World") == "hello-world"
    
    def test_uppercase_to_lowercase(self):
        """Test that uppercase letters are converted to lowercase."""
        assert slugify("HELLO WORLD") == "hello-world"
        assert slugify("MixedCase Text") == "mixedcase-text"
    
    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        assert slugify("Hello, World!") == "hello-world"
        assert slugify("User@Domain.com") == "userdomaincom"
        assert slugify("Test#$%&*()123") == "test123"
    
    def test_multiple_spaces_collapsed(self):
        """Test that multiple spaces are collapsed to single separator."""
        assert slugify("Hello    World") == "hello-world"
        assert slugify("Too   Many    Spaces") == "too-many-spaces"
    
    def test_leading_trailing_whitespace_trimmed(self):
        """Test that leading and trailing whitespace is removed."""
        assert slugify("  Hello World  ") == "hello-world"
        assert slugify("   Trimmed   ") == "trimmed"
    
    def test_empty_string(self):
        """Test that empty string returns empty string."""
        assert slugify("") == ""
    
    def test_whitespace_only_string(self):
        """Test that whitespace-only string returns empty string."""
        assert slugify("   ") == ""
        assert slugify("\t\n") == ""
    
    def test_numbers_preserved(self):
        """Test that numbers are preserved in the slug."""
        assert slugify("Python 3.10 is great") == "python-3-10-is-great"
        assert slugify("Version 2.0.1") == "version-2-0-1"
    
    def test_unicode_characters_normalized(self):
        """Test that unicode characters are normalized to ASCII."""
        assert slugify("Café") == "cafe"
        assert slugify("Naïve résumé") == "naive-resume"
        assert slugify("Zürich") == "zurich"
    
    def test_custom_separator(self):
        """Test using a custom separator."""
        assert slugify("Hello World", separator="_") == "hello_world"
        assert slugify("Test Case", separator=".") == "test.case"
    
    def test_duplicate_separators_removed(self):
        """Test that duplicate separators are collapsed."""
        assert slugify("Hello--World") == "hello-world"
        assert slugify("Test___Case", separator="_") == "test_case"
    
    def test_max_length_truncation(self):
        """Test that slugs are truncated to max length."""
        long_text = "This is a very long string that should be truncated"
        result = slugify(long_text, max_length=20)
        assert len(result) <= 20
        assert result == "this-is-a-very-long"
    
    def test_max_length_no_trailing_separator(self):
        """Test that truncation doesn't leave trailing separator."""
        text = "Hello World Test Case"
        result = slugify(text, max_length=12)
        assert not result.endswith("-")
        assert result == "hello-world"
    
    def test_ampersand_handling(self):
        """Test that ampersands are handled correctly."""
        assert slugify("Bread & Butter") == "bread-butter"
        assert slugify("Rock & Roll") == "rock-roll"
    
    def test_url_like_strings(self):
        """Test slugification of URL-like strings."""
        assert slugify("http://example.com") == "httpexamplecom"
        assert slugify("user@example.com") == "userexamplecom"
    
    def test_consecutive_special_characters(self):
        """Test multiple consecutive special characters."""
        assert slugify("Hello!!!World???") == "helloworld"
        assert slugify("Test...Case") == "testcase"
    
    def test_underscores_converted_to_separator(self):
        """Test that underscores are converted to the separator."""
        assert slugify("hello_world_test") == "hello-world-test"
        assert slugify("test_case", separator="_") == "test_case"
    
    def test_hyphens_preserved(self):
        """Test that existing hyphens are preserved."""
        assert slugify("pre-existing-hyphens") == "pre-existing-hyphens"
        assert slugify("test-case-123") == "test-case-123"
    
    def test_mixed_separators_normalized(self):
        """Test that mixed separators are normalized."""
        assert slugify("hello_world-test case") == "hello-world-test-case"
    
    def test_only_special_characters(self):
        """Test string with only special characters."""
        assert slugify("!@#$%^&*()") == ""
        assert slugify("...") == ""
    
    def test_real_world_examples(self):
        """Test real-world use cases."""
        assert slugify("How to Install Python 3.10?") == "how-to-install-python-3-10"
        assert slugify("User's Guide & Reference") == "users-guide-reference"
        assert slugify("2024 Annual Report (Final)") == "2024-annual-report-final"
        assert slugify("São Paulo, Brazil") == "sao-paulo-brazil"
