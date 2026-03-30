# Lean 4 Formalization

Machine-checked proofs for the Library Theorem. All proofs are `sorry`-free.

## Theorems

| Module | Theorem | Status |
|:-------|:--------|:-------|
| `Haak/Library/Basic.lean` | Theorem 0: capacity bound, I/O model | ✓ Complete |
| `Haak/Library/Sequential.lean` | Theorem 1: Ω(N) sequential lower bound | ✓ Complete |
| `Haak/Library/Indexed.lean` | Theorem 2: O(log_b N) indexed upper bound | ✓ Complete |
| `Haak/Library/Separation.lean` | Theorem 3: exponential separation | ✓ Complete |
| `Haak/Library/Turing.lean` | Theorem 5: externalization → Turing completeness | ✓ Complete |
| `Haak/Library/Reasoning.lean` | Theorem 4: reasoning separation | ✓ Complete |
| `Haak/Library/WriteRead.lean` | Theorem 1 (Paper 08): Write-Read Separation — indexed beats sequential iff R = Ω(log_b N) | ✓ Complete |
| `Haak/Library/Inscription.lean` | Theorem 2 (Paper 08): Inscription Theorem — write cost = read cost = O(log_b N) | ✓ Complete |

## Building

Requires [Lean 4](https://leanprover.github.io/) and [elan](https://github.com/leanprover/elan).

```bash
cd lean
lake build
```

Lean version: `leanprover/lean4:v4.28.0`. Depends on Mathlib 4.28.0.
