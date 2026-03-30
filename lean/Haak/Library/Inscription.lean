import Haak.Library.Basic
import Haak.Library.Indexed
import Haak.Library.WriteRead
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

namespace Haak.Library.Inscription

open Haak.Library

/-!
# Theorem 2 — The Inscription Theorem

A Level 2 agent performs T interleaved read-write steps on an indexed store.

Key result: write cost per step = read cost per step = h I/Os (same complexity class).
A Level 2 agent (with index) costs O(T * h_final).
A Level 2 agent (without index) costs Θ(T * N_final) = Θ(T²) — same as sequential CoT.
-/

/-!
## The B-tree amortized insertion cost
-/

/-- An indexed store with N pages and a B-tree of depth h covering all N pages -/
structure IndexedStore where
  N : Nat
  h : Nat
  hN : N > 0
  hh : h ≥ 1
  covers : 2 ^ h ≥ N

/-- Read cost from the store: h I/Os to traverse the B-tree -/
def readCost (s : IndexedStore) : Nat := s.h

/-- Write cost to insert one page and update B-tree: h I/Os (amortized, Cormen Thm 18.1) -/
def writeCost (s : IndexedStore) : Nat := s.h

/-- Write cost equals read cost: the fundamental symmetry of B-tree operations -/
theorem write_eq_read (s : IndexedStore) : writeCost s = readCost s := rfl

/-!
## Level 2 agent cost
-/

/-- Total cost of T interleaved read-write steps, each costing h I/Os.
    The store grows during the T steps; h_final is the depth of the final B-tree.  -/
def level2Cost (T h_final : Nat) : Nat := T * h_final

/-- Unindexed write cost: T pages written, each subsequent read costs N_final I/Os -/
def unindexedCost (T N_final : Nat) : Nat := T * N_final

/-- Theorem 2b: Indexed Level 2 costs T * h_final I/Os -/
theorem level2_indexed_cost (T h_final : Nat) :
    level2Cost T h_final = T * h_final := rfl

/-- Theorem 2c: Unindexed Level 2 costs T * N_final I/Os -/
theorem level2_unindexed_cost (T N_final : Nat) :
    unindexedCost T N_final = T * N_final := rfl

/-- 2^h ≥ h + 1 for all h — a B-tree of depth h has more slots than levels -/
theorem pow2_ge_succ (h : Nat) : 2 ^ h ≥ h + 1 := by
  induction h with
  | zero => simp
  | succ n ih =>
    simp [Nat.pow_succ]
    omega

/-- Theorem 2d: Indexed beats unindexed.
    Hypothesis hdepth : h_final ≤ N_final holds for any minimally-deep B-tree
    (i.e., when 2^(h-1) < N ≤ 2^h), since then h ≤ log₂ N < N for N ≥ 2. -/
theorem indexed_beats_unindexed (T N_final h_final : Nat)
    (hT : T ≥ 1)
    (hdepth : h_final ≤ N_final) :
    level2Cost T h_final ≤ unindexedCost T N_final := by
  unfold level2Cost unindexedCost
  exact Nat.mul_le_mul_left T hdepth

/-- Depth bound for a minimal binary tree: if 2^h ≥ N and N ≥ h + 1, then h ≤ N - 1.
    For a B-tree with N ≥ 2 pages and minimal depth, N ≥ h + 1 follows because
    each of the h+1 levels from root to leaf holds at least one page. -/
theorem depth_le_pages_minus_one (N h : Nat) (hN : N ≥ h + 1) : h ≤ N - 1 := by
  omega

/-- Theorem 2d (quadratic): Unindexed Level 2 is quadratic in T when N_final = N₀ + T.
    Formally: unindexedCost T (N₀ + T) ≥ T * T -/
theorem unindexed_quadratic (T N₀ : Nat) :
    unindexedCost T (N₀ + T) ≥ T * T := by
  unfold unindexedCost
  nlinarith

/-- Corollary: The separation between indexed and unindexed Level 2 grows without bound.
    For any k, there exists T such that unindexedCost T (T+1) > k * level2Cost T h. -/
theorem level2_separation_unbounded (h : Nat) (hh : h ≥ 1) :
    ∀ k : Nat, ∃ T : Nat,
      unindexedCost T (T + 1) > k * level2Cost T h := by
  intro k
  use k * h + 1
  unfold unindexedCost level2Cost
  nlinarith

end Haak.Library.Inscription
