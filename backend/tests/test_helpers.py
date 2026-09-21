import pytest
from app.utils.helpers import slugify


class TestSlugify:
    def test_basic_string(self):
        assert slugify("Hello World") == "hello-world"
    
    def test_merchant_name(self):
        assert slugify("Whole Foods Market") == "whole-foods-market"
    
    def test_with_special_characters(self):
        assert slugify("Apple Store!") == "apple-store"
    
    def test_with_multiple_spaces(self):
        assert slugify("The   Quick   Brown") == "the-quick-brown"
    
    def test_multiple_hyphens_collapse(self):
        assert slugify("Test---Value") == "test-value"
    
    def test_leading_trailing_hyphens_stripped(self):
        assert slugify("-hello-world-") == "hello-world"
    
    def test_empty_string(self):
        assert slugify("") == ""
    
    def test_only_special_characters(self):
        assert slugify("!!!###$$$") == ""
    
    def test_with_numbers(self):
        assert slugify("Test 123 Value") == "test-123-value"
    
    def test_uppercase_conversion(self):
        assert slugify("UPPERCASE") == "uppercase"
