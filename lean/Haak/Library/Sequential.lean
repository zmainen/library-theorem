import Haak.Library.Basic
import Mathlib.Data.Finset.Card

namespace Haak.Library.Sequential

open Haak.Library

/-!
# Theorem 1 — Sequential Lower Bound

Without indexing structure, retrieving a target item from N pages
costs Ω(N) steps.
-/

/-- A search algorithm over an unstructured store. -/
structure SearchAlgorithm where
  strategy : (N : Nat) → List Nat

/-- Correct if every possible target location appears in the read sequence. -/
def SearchAlgorithm.correct (alg : SearchAlgorithm) (N : Nat) : Prop :=
  ∀ target : Nat, target < N → target ∈ alg.strategy N

/--
**Theorem 1 (Sequential lower bound).**
Any correct search algorithm must read at least N pages.

Proof: correctness requires all N distinct values {0, ..., N-1} in the
strategy list. By pigeonhole, the list length ≥ N.
-/
theorem sequential_lower_bound (alg : SearchAlgorithm) (N : Nat)
    (hcorrect : alg.correct N) :
    (alg.strategy N).length ≥ N := by
  by_contra h
  push_neg at h
  -- The strategy list has fewer elements than N
  -- But every i < N must appear in it (correctness)
  -- So toFinset has ≥ N elements, but length < N — contradiction
  have hsub : Finset.range N ⊆ (alg.strategy N).toFinset := by
    intro i hi
    exact List.mem_toFinset.mpr (hcorrect i (Finset.mem_range.mp hi))
  have hcard : N ≤ (alg.strategy N).toFinset.card := by
    calc N = (Finset.range N).card := by simp
    _ ≤ (alg.strategy N).toFinset.card := Finset.card_le_card hsub
  have hle : (alg.strategy N).toFinset.card ≤ (alg.strategy N).length :=
    List.toFinset_card_le _
  omega

end Haak.Library.Sequential
