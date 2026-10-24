from app.utils.text import slugify


def test_slugify_handles_spaces_and_punctuation():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_collapses_repeated_separators():
    assert slugify("  Bank   Transfer  ") == "bank-transfer"


def test_slugify_transliterates_accents():
    assert slugify("Crème brûlée") == "creme-brulee"
