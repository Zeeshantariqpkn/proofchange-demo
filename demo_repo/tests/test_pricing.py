"""Existing tests for pricing.

Note: there is intentionally no test for the VIP scenario. This is
the gap ProofChange is designed to detect.
"""
from src.pricing import calculate_discount


def test_premium_discount():
    assert calculate_discount(100, "premium") == 80


def test_regular_customer():
    assert calculate_discount(100, "regular") == 100
