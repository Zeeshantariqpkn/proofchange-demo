"""Tests for pricing rules in the demo repository."""
from src.pricing import calculate_discount


def test_premium_discount():
    """Premium customers receive a 20% discount."""
    assert calculate_discount(100, "premium") == 80.0


def test_regular_price():
    """Regular customers receive no discount."""
    assert calculate_discount(100, "regular") == 100
