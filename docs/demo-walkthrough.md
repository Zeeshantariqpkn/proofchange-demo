# Demo Walkthrough: VIP Discount Change

## 1. What Changed

A new conditional branch was added to [`calculate_discount()`](../demo_repo/src/pricing.py:4) in
[`demo_repo/src/pricing.py`](../demo_repo/src/pricing.py).

The diff (`demo_repo/change.diff`) shows the following lines were inserted:

```diff
+    if customer_type == "vip":
+        return price * 0.70
```

Before the change the function had two possible code paths:

| Condition | Behaviour |
|---|---|
| `customer_type == "premium"` | Apply 20 % discount → `price * 0.80` |
| anything else | Return full price → `price` |

After the change a third path exists:

| Condition | Behaviour |
|---|---|
| `customer_type == "premium"` | Apply 20 % discount → `price * 0.80` |
| `customer_type == "vip"` | Apply 30 % discount → `price * 0.70` |
| anything else | Return full price → `price` |

---

## 2. Which Function Was Affected

**`calculate_discount(price, customer_type)`** — the only function in
[`demo_repo/src/pricing.py`](../demo_repo/src/pricing.py:4).

It accepts two arguments:

- `price` — the original price (numeric)
- `customer_type` — a string token that selects the discount tier

---

## 3. What Branch Was Added

The new branch is:

```python
if customer_type == "vip":
    return price * 0.70
```

It introduces a **VIP discount tier** that reduces the price to 70 % of the
original (a 30 % discount). The branch is evaluated only when the earlier
`"premium"` check has already failed, so the two tiers are mutually exclusive
by position in the function.

---

## 4. Why the Existing Tests Don't Cover It

[`demo_repo/tests/test_pricing.py`](../demo_repo/tests/test_pricing.py)
currently contains **a verbatim copy of the source module** rather than actual
test cases. There are no `assert` statements, no test functions, and no import
of `src.pricing`. As a result:

- The test file exercises **zero** behaviour of `calculate_discount()`.
- The `"vip"` branch was never reachable from any test.
- Even the existing `"premium"` and fallback paths are untested.

Because no test calls `calculate_discount` with `customer_type="vip"`, the new
branch has **0 % coverage** and any regression in its logic (wrong multiplier,
typo in the string literal, missing `return`, etc.) would go undetected.

---

## 5. What the Ideal Test Would Look Like

A minimal but complete test suite for the current state of the function:

```python
"""Tests for demo_repo/src/pricing.py — calculate_discount."""
import pytest
from src.pricing import calculate_discount


class TestCalculateDiscount:

    # ── existing behaviour ──────────────────────────────────────────────────

    def test_premium_customer_receives_20_percent_discount(self):
        assert calculate_discount(100, "premium") == 80.0

    def test_regular_customer_pays_full_price(self):
        assert calculate_discount(100, "regular") == 100

    def test_unknown_customer_type_pays_full_price(self):
        assert calculate_discount(50, "unknown") == 50

    # ── new VIP branch ──────────────────────────────────────────────────────

    def test_vip_customer_receives_30_percent_discount(self):
        """Core coverage for the new branch: price * 0.70."""
        assert calculate_discount(100, "vip") == 70.0

    def test_vip_discount_scales_with_price(self):
        assert calculate_discount(200, "vip") == 140.0

    def test_vip_and_premium_are_mutually_exclusive(self):
        """Verify the two tiers produce different results for the same price."""
        premium = calculate_discount(100, "premium")
        vip = calculate_discount(100, "vip")
        assert vip < premium, "VIP discount should be deeper than premium"

    # ── edge cases ──────────────────────────────────────────────────────────

    def test_zero_price_returns_zero_for_vip(self):
        assert calculate_discount(0, "vip") == 0.0

    def test_fractional_price_vip(self):
        result = calculate_discount(99.99, "vip")
        assert abs(result - 69.993) < 1e-9
```

### Why each test matters

| Test | Purpose |
|---|---|
| `test_vip_customer_receives_30_percent_discount` | Directly hits the new branch; fails if the multiplier is wrong or the string is mistyped |
| `test_vip_discount_scales_with_price` | Confirms the multiplier is applied, not a hard-coded return value |
| `test_vip_and_premium_are_mutually_exclusive` | Guards against accidentally merging or reordering the two conditions |
| `test_zero_price_returns_zero_for_vip` | Edge case: zero input must not produce a non-zero result |
| `test_fractional_price_vip` | Real-world prices are not always integers |
