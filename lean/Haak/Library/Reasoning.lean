import Haak.Library.Basic
import Haak.Library.Separation
import Mathlib.Tactic.Linarith

namespace Haak.Library.Reasoning

open Haak.Library

/-!
# Theorem 4 — Reasoning Separation

A reasoning agent with bounded working memory performs T reasoning
steps, each requiring retrieval of a prior intermediate result.

**Without an index**: step i scans up to i stored intermediates.
Total cost = T * (T + 1), which is Θ(T²).

**With an index**: each retrieval costs h (B-tree height).
Total cost = T * h, where h = ⌈log_b T⌉.

The separation ratio is (T+1)/h — unbounded as T grows.
For h = log_b T, this is Ω(T / log T).

This formalizes the advantage of "thinking with notes" over
"thinking in your head" — the core connection to the chain-of-thought
literature (Feng et al. 2023, Merrill & Sabharwal 2024).
-/

/-- Sequential reasoning cost: step i scans i items. -/
def sequentialReasoningCost (T : Nat) : Nat :=
  T * (T + 1)

/-- Indexed reasoning cost: T lookups at height h. -/
def indexedReasoningCost (T h : Nat) : Nat :=
  T * h

/-- Sequential cost grows as T². -/
theorem sequential_quadratic (T : Nat) :
    sequentialReasoningCost T ≥ T * T := by
  unfold sequentialReasoningCost
  exact Nat.mul_le_mul_left T (Nat.le_succ T)

/--
**Theorem 4a (Reasoning separation).**
Sequential cost exceeds indexed cost by factor (T+1)/h.
Stated without division: seq * h ≥ idx * (T + 1).
-/
theorem reasoning_separation (T h : Nat) :
    sequentialReasoningCost T * h ≥ indexedReasoningCost T h * (T + 1) := by
  unfold sequentialReasoningCost indexedReasoningCost
  nlinarith

/--
**Theorem 4b (Unbounded gap).**
For any constant speedup factor k, there exists T such that
sequential cost ≥ k × indexed cost.
Witness: T = k * h suffices.
-/
theorem reasoning_gap_unbounded (k h : Nat) (_ : h > 0) :
    ∃ T, sequentialReasoningCost T ≥ k * indexedReasoningCost T h := by
  use k * h
  unfold sequentialReasoningCost indexedReasoningCost
  nlinarith

/--
**Theorem 4c (Exponential regime).**
When T ≥ 2^h, the sequential cost is at least 2^h * (2^h + 1).
Combined with Theorem 3, this shows the gap is exponential in h.
-/
theorem reasoning_exponential_regime (T h : Nat)
    (hcovers : T ≥ 2 ^ h) :
    sequentialReasoningCost T ≥ 2 ^ h * (2 ^ h + 1) := by
  unfold sequentialReasoningCost
  calc T * (T + 1) ≥ 2 ^ h * (T + 1) := Nat.mul_le_mul_right _ hcovers
    _ ≥ 2 ^ h * (2 ^ h + 1) := Nat.mul_le_mul_left _ (by omega)

/-- In the exponential regime, sequential cost grows at least as (h+1)².
    Uses exp_dominates_linear from Separation: 2^h ≥ h+1. -/
theorem reasoning_vs_indexed_exponential (T h : Nat)
    (hcovers : T ≥ 2 ^ h) :
    sequentialReasoningCost T ≥ (h + 1) * (h + 1) := by
  have hexp := Separation.exp_dominates_linear h
  calc sequentialReasoningCost T
      ≥ 2 ^ h * (2 ^ h + 1) := reasoning_exponential_regime T h hcovers
    _ ≥ (h + 1) * (2 ^ h + 1) := Nat.mul_le_mul_right _ hexp
    _ ≥ (h + 1) * (h + 1) := Nat.mul_le_mul_left _ (by omega)

end Haak.Library.Reasoning
