namespace Haak.Library

/-!
# Library Theorem — Computational Model

The I/O complexity model for bounded-capacity reasoning over external memory.
Adapted from Aggarwal & Vitter (1988) to transformer-based systems.
-/

/-- Configuration of a bounded reasoning system. -/
structure Config where
  /-- Context window size (number of tokens). -/
  C : Nat
  /-- Alphabet size. -/
  alphaSize : Nat
  /-- Number of pages in external store. -/
  N : Nat
  /-- Overhead per pointer in an index node (tokens). -/
  overhead : Nat
  /-- C > 0 -/
  hC : C > 0
  /-- Alphabet has at least 2 symbols -/
  hAlpha : alphaSize ≥ 2
  /-- Store is non-empty -/
  hN : N > 0
  /-- Overhead is less than context window -/
  hOverhead : overhead < C

/-- Branching factor of a B-tree index: b = C / overhead. -/
def Config.branchingFactor (cfg : Config) : Nat :=
  cfg.C / cfg.overhead

/-- The branching factor is at least 2 when overhead > 0 and C ≥ 2 * overhead. -/
theorem Config.branchingFactor_ge_two (cfg : Config)
    (hpos : cfg.overhead > 0) (h : cfg.C ≥ 2 * cfg.overhead) :
    cfg.branchingFactor ≥ 2 := by
  unfold branchingFactor
  exact (Nat.le_div_iff_mul_le hpos).mpr h

/-- A step in the computation: the agent reads or writes one page. -/
inductive Step where
  | read  (page : Nat) : Step
  | write (page : Nat) (content : Nat) : Step

/-- Cost of an algorithm is the number of steps it takes. -/
def cost (steps : List Step) : Nat := steps.length

/--
**Theorem 0 (Capacity bound).**
Each read step extracts at most C * alphaSize bits from the store.
-/
def Config.bitsPerStep (cfg : Config) : Nat :=
  cfg.C * cfg.alphaSize

theorem Config.bitsPerStep_pos (cfg : Config) : cfg.bitsPerStep > 0 := by
  unfold bitsPerStep
  exact Nat.mul_pos cfg.hC (Nat.lt_of_lt_of_le (by omega) cfg.hAlpha)

end Haak.Library
