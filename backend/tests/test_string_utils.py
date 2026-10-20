import pytest
from app.utils.string_utils import slugify

def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"
    assert slugify("Simple Test Case") == "simple-test-case"

def test_slugify_special_characters():
    assert slugify("Hello! @World#") == "hello-world"
    assert slugify("Multiple   Spaces") == "multiple-spaces"
    assert slugify("Trailing spaces   ") == "trailing-spaces"

def test_slugify_unicode():
    assert slugify("Héllò Wörld") == "hello-world"

def test_slugify_lowercase_option():
    assert slugify("Hello World", lowercase=False) == "Hello-World"

def test_slugify_empty_string():
    assert slugify("") == ""
    assert slugify(None) == ""

def test_slugify_numeric():
    assert slugify("Version 1.2.3") == "version-1-2-3"
