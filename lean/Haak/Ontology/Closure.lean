import Haak.Ontology.Basic
import Haak.Ontology.MetaQualities

namespace Haak.Ontology.Closure

open Haak.Ontology
open Haak.Ontology.MetaQualities

/-!
# Reflexive Closure (R3)

Every quality is an entity. The qualification chain terminates because
meta-qualities form a finite closed set (depth ≤ 1).
-/

/-- Quality → Entity injection (Definition R3). -/
def qualityToEntity (q : QualityId) : EntityId :=
  ⟨q.val⟩

theorem qualityToEntity_injective :
    Function.Injective qualityToEntity := by
  intro ⟨a⟩ ⟨b⟩ h
  simp [qualityToEntity] at h
  exact congrArg QualityId.mk h

/-- Qualification depth: meta-qualities are level 0, domain qualities level 1. -/
inductive QualLevel where
  | metaQ (m : MetaQuality) : QualLevel
  | domainQ (q : QualityId) (grounding : MetaQuality) : QualLevel

def QualLevel.depth : QualLevel → Nat
  | .metaQ _ => 0
  | .domainQ _ _ => 1

/-- The qualification chain has bounded depth ≤ 1. -/
theorem closure_terminates (ql : QualLevel) : ql.depth ≤ 1 := by
  cases ql with
  | metaQ _ => simp [QualLevel.depth]
  | domainQ _ _ => simp [QualLevel.depth]

/-- The ontology is monotonic: adding belongings preserves existing ones. -/
theorem monotonic_consistency (bs : List Belonging) (new_b : Belonging) :
    ∀ b ∈ bs, b ∈ (new_b :: bs) :=
  fun _ hb => List.mem_cons_of_mem _ hb

/-- Well-foundedness of the qualification ordering. -/
theorem wellFounded_qualification :
    WellFounded (fun (a b : QualLevel) => a.depth < b.depth) :=
  InvImage.wf QualLevel.depth Nat.lt_wfRel.wf

end Haak.Ontology.Closure
