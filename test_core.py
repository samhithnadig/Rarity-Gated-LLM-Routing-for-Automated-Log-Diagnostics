from textkit.core import (
    word_count,
    to_snake_case,
    truncate,
    merge_options,
    capitalize_words,
    build_config,
    safe_int,
    slugify,
)


def test_word_count():
    assert word_count("hello world") == 2
    assert word_count("") == 0


def test_to_snake_case():
    assert to_snake_case("Hello World") == "hello_world"


def test_truncate():
    assert truncate("hello", 10) == "hello"
    assert truncate("hello world", 5) == "hell…"


def test_merge_options():
    assert merge_options({"a": 1}) == {"a": 1}


def test_capitalize_words():
    assert capitalize_words("hello world") == "Hello World"


def test_build_config():
    assert build_config({"debug": True}) == {"debug": True}


def test_safe_int():
    assert safe_int("42") == 42
    assert safe_int("nope", fallback=-1) == -1


def test_slugify():
    assert slugify("Hello World") == "hello-world"
