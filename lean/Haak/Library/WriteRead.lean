import Haak.Library.Basic
import Haak.Library.Indexed
import Haak.Library.Sequential
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

namespace Haak.Library.WriteRead

open Haak.Library

/-!
# Theorem 1 — Write-Read Separation

Compares total cost of sequential vs indexed strategies.
For R retrievals from a store of N pages with B-tree depth h:

  seqCost N R = N + R * N        (write N pages, each retrieval scans all N)
  idxCost N R h = N * h + R * h  (N insertions at h cost each, R lookups at h each)
                = h * (N + R)

Sequential beats indexed when R is small; indexed beats sequential when R is large.
The crossover is at R ≈ h = log_b N.
The full N/h separation manifests at R = N.
-/

/-- Total cost of sequential strategy: write N pages (no index) + R full scans -/
def seqCost (N R : Nat) : Nat := N + R * N

/-- Total cost of indexed strategy: N B-tree insertions (h I/Os each) + R lookups (h I/Os each) -/
def idxCost (N R h : Nat) : Nat := N * h + R * h

/-- idxCost factors as h * (N + R) -/
lemma idxCost_factor (N R h : Nat) : idxCost N R h = h * (N + R) := by
  unfold idxCost; ring

/-- seqCost factors as N * (1 + R) -/
lemma seqCost_factor (N R : Nat) : seqCost N R = N * (1 + R) := by
  unfold seqCost; ring

/-!
## Part (a): For zero retrievals, indexed is more expensive (h ≥ 2)
-/

/-- With no retrievals, index construction cost N*h dominates. Sequential (cost N) beats indexed (cost N*h) when h ≥ 2. -/
theorem idx_worse_no_retrievals (N h : Nat) (hN : N ≥ 1) (hh : h ≥ 2) :
    idxCost N 0 h > seqCost N 0 := by
  unfold idxCost seqCost
  simp
  nlinarith

/-!
## Part (b): Crossover condition
-/

/-- Indexed costs less than sequential when h*(N+R) ≤ N*(1+R) (approximately R ≥ h). -/
theorem idx_beats_seq_of_crossover (N R h : Nat)
    (hcross : h * (N + R) ≤ N * (1 + R)) :
    idxCost N R h ≤ seqCost N R := by
  rw [idxCost_factor, seqCost_factor]
  exact hcross

/-!
## Part (c): Full separation at R = N
The ratio seqCost(N,N) / idxCost(N,N,h) ≥ N / (2*h).
Stated without division: 2*h * seqCost(N,N) ≥ N * idxCost(N,N,h).
-/

/-- At R = N retrievals, sequential cost is at least N/(2h) times indexed cost.
    Stated as: 2*h * seqCost(N,N) ≥ N * idxCost(N,N,h). -/
theorem separation_bound (N h : Nat) (hN : N ≥ 1) (hh : h ≥ 1) :
    2 * h * seqCost N N ≥ N * idxCost N N h := by
  unfold seqCost idxCost
  nlinarith [Nat.mul_comm N h, Nat.mul_comm N N]

/-- Lemma: for h ≥ 1 and any k, k*h*2+1 ≥ k+1. -/
private lemma witness_ge (k h : Nat) (hh : h ≥ 1) : k * h * 2 + 1 ≥ k + 1 := by
  nlinarith

/-- Corollary: The separation ratio grows without bound as N grows (h fixed).
    For any k there exists N such that 2h·seqCost(N,N) ≥ k·idxCost(N,N,h). -/
theorem separation_unbounded (h : Nat) (hh : h ≥ 1) :
    ∀ k : Nat, ∃ N : Nat, 2 * h * seqCost N N ≥ k * idxCost N N h := by
  intro k
  -- Take N = k * h * 2 + 1. Since h ≥ 1, N ≥ k + 1 > k.
  -- Then 2h*seqCost(N,N) = 2h*(N + N²) and k*idxCost(N,N,h) = k*2hN.
  -- Sufficient: N + N² ≥ k*N, i.e. 1 + N ≥ k. True since N ≥ k + 1.
  refine ⟨k * h * 2 + 1, ?_⟩
  unfold seqCost idxCost
  have hN : k * h * 2 + 1 ≥ k + 1 := witness_ge k h hh
  nlinarith [Nat.mul_pos (show k * h * 2 + 1 > 0 by omega) (show h > 0 by omega)]

end Haak.Library.WriteRead
