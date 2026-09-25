# Demo Repository

A minimal Python repository used by the ProofChange demo.

## Scenario

A developer adds VIP discount support to `calculate_discount()`.
The existing tests cover `premium` and `regular` customers, but not
the new `vip` branch. CI would be green, yet the new behavior is
unverified.

ProofChange detects this gap, generates a test, executes it, and
produces a Change Evidence Package.

## Layout
