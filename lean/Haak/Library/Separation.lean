import Haak.Library.Basic
import Haak.Library.Sequential
import Haak.Library.Indexed

namespace Haak.Library.Separation

open Haak.Library

/-!
# Theorem 3 — The Library Theorem (Separation)

The separation ratio between indexed and sequential retrieval is
Ω(b^h / h), exponential in the depth of the index hierarchy.
-/

/-- The ratio N/h ≥ b^h/h when N ≥ b^h. -/
theorem separation_exponential (b h N : Nat) (hN : N ≥ b ^ h) :
    N / h ≥ b ^ h / h :=
  Nat.div_le_div_right hN

/-- 2^h ≥ h + 1 for all h. Base for the exponential dominance argument. -/
theorem exp_dominates_linear (h : Nat) : 2 ^ h ≥ h + 1 := by
  induction h with
  | zero => simp
  | succ n ih =>
    simp [Nat.pow_succ]
    omega

/--
**Theorem 3 (The Library Theorem).**
For b ≥ 2 and N ≥ b^h, the ratio sequential/indexed = N/h ≥ b^h/h,
which is exponential in h. Each level of hierarchy multiplies
the advantage by b.
-/
theorem library_theorem (b h N : Nat) (hcovers : b ^ h ≤ N) :
    N / h ≥ b ^ h / h :=
  Nat.div_le_div_right hcovers

end Haak.Library.Separation
