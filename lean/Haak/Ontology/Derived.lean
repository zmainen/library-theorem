import Haak.Ontology.Basic

namespace Haak.Ontology.Derived

open Haak.Ontology

/-!
# Derived Social Structure (Situation Graph)

The situation graph is not stored — it is computed from belongings.
Two entities are co-participants if both belong to the same context
(situation). Relationships are derived views, never primitives.

This module proves:
1. Co-participation is symmetric (if A sees B, B sees A)
2. Co-participation is irreflexive (no entity co-participates with itself)
3. Monotonicity: adding a belonging can only add co-participation edges
4. Grounding: every co-participation is witnessed by a specific situation
-/

/-- A witnessed co-participation: two entities sharing a situation,
    with the witnessing situation and belongings made explicit. -/
structure CoParticipation where
  entityA : EntityId
  entityB : EntityId
  situation : EntityId
  belongingA : Belonging
  belongingB : Belonging
  hDistinct : entityA ≠ entityB
  hA : belongingA.dependent = entityA ∧ belongingA.context = situation
  hB : belongingB.dependent = entityB ∧ belongingB.context = situation

/-- Extract all witnessed co-participations from a list of belongings. -/
def allCoParticipations (bs : List Belonging) : List CoParticipation :=
  bs.foldl (fun acc (b1 : Belonging) =>
    bs.foldl (fun acc2 (b2 : Belonging) =>
      if h : Belonging.dependent b1 != Belonging.dependent b2 &&
             Belonging.context b1 == Belonging.context b2 then
        let hne : Belonging.dependent b1 ≠ Belonging.dependent b2 := by
          simp [bne_iff_ne, ne_eq] at h; exact h.1
        { entityA := Belonging.dependent b1
          entityB := Belonging.dependent b2
          situation := Belonging.context b1
          belongingA := b1
          belongingB := b2
          hDistinct := hne
          hA := ⟨rfl, rfl⟩
          hB := ⟨rfl, by simp [beq_iff_eq] at h; exact h.2.symm⟩
        } :: acc2
      else acc2
    ) acc
  ) []

/-- Co-participation is symmetric: if (A, B, S) is a co-participation
    from belongings bs, then (B, A, S) is also one. -/
theorem coparticipation_symmetric (bs : List Belonging)
    (cp : CoParticipation)
    (hA_mem : cp.belongingA ∈ bs)
    (hB_mem : cp.belongingB ∈ bs) :
    ∃ cp' : CoParticipation,
      cp'.entityA = cp.entityB ∧
      cp'.entityB = cp.entityA ∧
      cp'.situation = cp.situation ∧
      cp'.belongingA ∈ bs ∧
      cp'.belongingB ∈ bs := by
  exact ⟨{
    entityA := cp.entityB
    entityB := cp.entityA
    situation := cp.situation
    belongingA := cp.belongingB
    belongingB := cp.belongingA
    hDistinct := Ne.symm cp.hDistinct
    hA := cp.hB
    hB := cp.hA
  }, rfl, rfl, rfl, hB_mem, hA_mem⟩

/-- Co-participation is irreflexive: no entity co-participates with itself. -/
theorem coparticipation_irreflexive (cp : CoParticipation) :
    cp.entityA ≠ cp.entityB :=
  cp.hDistinct

/-- Every co-participation is grounded: there exists a witnessing situation
    and two belongings in the state that justify it. -/
theorem coparticipation_grounded (cp : CoParticipation) :
    ∃ s : EntityId,
      cp.belongingA.context = s ∧
      cp.belongingB.context = s ∧
      cp.belongingA.dependent = cp.entityA ∧
      cp.belongingB.dependent = cp.entityB :=
  ⟨cp.situation, cp.hA.2, cp.hB.2, cp.hA.1, cp.hB.1⟩

/-- Monotonicity: belongings that witness co-participation in a smaller
    state still witness it in any extension. -/
theorem coparticipation_monotone (bs : List Belonging) (new_b : Belonging)
    (cp : CoParticipation)
    (hA_mem : cp.belongingA ∈ bs)
    (hB_mem : cp.belongingB ∈ bs) :
    cp.belongingA ∈ (new_b :: bs) ∧ cp.belongingB ∈ (new_b :: bs) :=
  ⟨List.mem_cons_of_mem _ hA_mem, List.mem_cons_of_mem _ hB_mem⟩

/-- The social graph is a derived view: every field of a CoParticipation
    is determined by two belongings. No new information is added. -/
theorem social_graph_is_view (cp : CoParticipation) :
    cp.entityA = cp.belongingA.dependent ∧
    cp.entityB = cp.belongingB.dependent ∧
    cp.situation = cp.belongingA.context ∧
    cp.belongingA.context = cp.belongingB.context :=
  ⟨cp.hA.1.symm, cp.hB.1.symm, cp.hA.2.symm, by rw [cp.hA.2, cp.hB.2]⟩

end Haak.Ontology.Derived
