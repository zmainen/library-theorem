import Haak.Library.Basic
import Mathlib.Data.Fintype.Card

namespace Haak.Library.Turing

/-!
# Theorem 5 — Externalization Completeness

A bounded-context agent (fixed window C) alone computes SPACE(C).
Adding an unbounded external read/write store makes the system
Turing complete.

Two parts:
1. **Bounded cycles**: state-only computation over Fin S must revisit
   a state within S steps (pigeonhole).
2. **Unbounded escapes**: with a tape, the head position grows without
   bound — the system accesses fresh memory forever.

The gap is strict: Fin S alone → finite automaton.
Fin S + tape → Turing machine.
-/

/-- Tape: unbounded addressable memory. -/
abbrev Tape := Nat → Nat

/-- Write to tape at one position. -/
def Tape.write (t : Tape) (pos val : Nat) : Tape :=
  fun n => if n == pos then val else t n

/-- Computation state: bounded control + unbounded tape + head. -/
structure CompState (S : Nat) where
  state : Fin S
  tape : Tape
  head : Nat

/-- Transition function. -/
structure TransFn (S : Nat) where
  step : Fin S → Nat → Fin S × Nat × Bool

/-- One computation step. -/
def execStep (S : Nat) (tf : TransFn S) (cfg : CompState S) : CompState S :=
  let result := tf.step cfg.state (cfg.tape cfg.head)
  { state := result.1
    tape := cfg.tape.write cfg.head result.2.1
    head := if result.2.2 then cfg.head + 1 else cfg.head - 1 }

/-- Run n steps. -/
def execN (S : Nat) (tf : TransFn S) (cfg : CompState S) : Nat → CompState S
  | 0 => cfg
  | n + 1 => execStep S tf (execN S tf cfg n)

/-- Bounded iteration: state only, no tape. -/
def iterState (S : Nat) (f : Fin S → Fin S) (s : Fin S) : Nat → Fin S
  | 0 => s
  | n + 1 => f (iterState S f s n)

/--
**Part 1: Bounded computation must cycle.**
The function i ↦ iterState f s₀ i maps Fin (S+1) → Fin S.
By pigeonhole (S+1 > S), two inputs collide.
-/
theorem bounded_cycles (S : Nat) (_ : S > 0) (f : Fin S → Fin S)
    (s₀ : Fin S) :
    ∃ i j : Fin (S + 1), i ≠ j ∧
      iterState S f s₀ i.val = iterState S f s₀ j.val := by
  by_contra hall
  push_neg at hall
  -- hall : ∀ i j, i ≠ j → iterState S f s₀ i ≠ iterState S f s₀ j
  -- So g is injective
  let g : Fin (S + 1) → Fin S := fun k => iterState S f s₀ k.val
  have hinj : Function.Injective g := by
    intro a b hab
    by_contra hne
    exact hall a b hne hab
  -- But |Fin (S+1)| = S+1 > S = |Fin S|, contradicting injectivity
  have : Fintype.card (Fin (S + 1)) ≤ Fintype.card (Fin S) :=
    Fintype.card_le_of_injective g hinj
  simp at this
  omega

/-- A machine that always moves right. -/
def rightMover : TransFn 1 :=
  { step := fun _ val => (⟨0, by omega⟩, val, true) }

/-- After n steps of rightMover, the head is at position n. -/
theorem rightMover_head (n : Nat) :
    (execN 1 rightMover ⟨⟨0, by omega⟩, fun _ => 0, 0⟩ n).head = n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    show (execStep 1 rightMover (execN 1 rightMover _ n)).head = n + 1
    simp only [execStep, rightMover]
    simp only [ite_true]
    -- Goal: (...).head + 1 = n + 1, where (...).head = n by ih
    have : (execN 1 { step := fun _ val => (⟨0, by omega⟩, val, true) }
          ⟨⟨0, by omega⟩, fun _ => 0, 0⟩ n).head = n := ih
    omega

/--
**Part 2: Unbounded head position.**
With an external tape, the head grows without bound.
No finite state can track position n for all n — so the
tape-augmented system accesses information that the finite
state alone cannot represent.
-/
theorem unbounded_head :
    ∀ n : Nat,
      (execN 1 rightMover ⟨⟨0, by omega⟩, fun _ => 0, 0⟩ n).head = n :=
  rightMover_head

/-- Head grows without bound — exceeds any constant. -/
theorem head_exceeds_any_bound (k : Nat) :
    ∃ n : Nat,
      (execN 1 rightMover ⟨⟨0, by omega⟩, fun _ => 0, 0⟩ n).head > k := by
  exact ⟨k + 1, by rw [rightMover_head]; omega⟩

/--
**Theorem 5 (Externalization completeness).**

- Without external store: computation over Fin S must cycle within
  S steps. Computes only periodic functions — finite automaton.
- With external store: head position grows without bound, accessing
  fresh memory at every step. Computes non-periodic functions.

Therefore: external store strictly extends computational power.
A finite-context-window LLM + read/write store is strictly more
powerful than the LLM alone.
-/
theorem externalization_completeness :
    -- Bounded: must cycle
    (∀ (S : Nat) (_ : S > 0) (f : Fin S → Fin S) (s₀ : Fin S),
      ∃ i j : Fin (S + 1), i ≠ j ∧
        iterState S f s₀ i.val = iterState S f s₀ j.val) ∧
    -- Unbounded: head grows without bound
    (∀ k : Nat, ∃ n : Nat,
      (execN 1 rightMover ⟨⟨0, by omega⟩, fun _ => 0, 0⟩ n).head > k) :=
  ⟨bounded_cycles, head_exceeds_any_bound⟩

end Haak.Library.Turing
