import Haak.Ontology.Basic
import Haak.Ontology.MetaQualities

namespace Haak.Ontology.Expressiveness

open Haak.Ontology
open Haak.Ontology.MetaQualities

/-!
# Expressiveness — BFO and DOLCE Reductions

Every primitive relation from BFO (Basic Formal Ontology) and DOLCE
reduces to belongs-to with an appropriate quality. This module
encodes each reduction as a structure and proves the reductions
are well-formed (each BFO/DOLCE relation maps to exactly one
belongs-to triple with determinate quality behavior).
-/

/-- A reduction: a BFO/DOLCE relation expressed as a belongs-to triple
    plus the meta-quality behavior of the quality involved. -/
structure Reduction where
  /-- Name of the source relation (documentation only) -/
  name : String
  /-- The quality used in the belongs-to encoding -/
  quality : QualityId
  /-- Meta-quality behaviors this quality has -/
  behaviors : List MetaQuality

/-- The 6 BFO primitive relations, each reduced to belongs-to + quality. -/
def bfoReductions : List Reduction :=
  [ { name := "continuant-part-of", quality := ⟨100⟩,
      behaviors := [.transitive] },
    { name := "has-participant",    quality := ⟨101⟩,
      behaviors := [.inverse] },
    { name := "realizes",           quality := ⟨102⟩,
      behaviors := [] },
    { name := "instance-of",        quality := ⟨103⟩,
      behaviors := [.inst] },
    { name := "inheres-in",         quality := ⟨104⟩,
      behaviors := [] },
    { name := "occurs-in",          quality := ⟨105⟩,
      behaviors := [] } ]

/-- The 6 DOLCE primitive relations, each reduced. -/
def dolceReductions : List Reduction :=
  [ { name := "part",               quality := ⟨200⟩,
      behaviors := [.transitive] },
    { name := "constitution",        quality := ⟨201⟩,
      behaviors := [] },
    { name := "participation",       quality := ⟨202⟩,
      behaviors := [] },
    { name := "quality-inherence",   quality := ⟨203⟩,
      behaviors := [] },
    { name := "quale",               quality := ⟨204⟩,
      behaviors := [] },
    { name := "dependence",          quality := ⟨205⟩,
      behaviors := [] } ]

/-- Every meta-quality behavior referenced in a reduction is valid
    (belongs to the closed meta-quality set). -/
theorem bfo_behaviors_valid :
    ∀ r ∈ bfoReductions, ∀ m ∈ r.behaviors, m ∈ allMetaQualities := by
  intro r hr m hm
  simp [bfoReductions] at hr
  rcases hr with ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩ |
                  ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩
  all_goals (simp at hm; try exact allMetaQualities_complete _)
  all_goals (rcases hm with rfl; exact allMetaQualities_complete _)

theorem dolce_behaviors_valid :
    ∀ r ∈ dolceReductions, ∀ m ∈ r.behaviors, m ∈ allMetaQualities := by
  intro r hr m hm
  simp [dolceReductions] at hr
  rcases hr with ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩ |
                  ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩ | ⟨rfl, rfl, rfl⟩
  all_goals (simp at hm; try exact allMetaQualities_complete _)
  all_goals (rcases hm with rfl; exact allMetaQualities_complete _)

/-- BFO reductions use distinct qualities (no conflation). -/
theorem bfo_qualities_distinct :
    (bfoReductions.map Reduction.quality).Nodup := by
  simp [bfoReductions, List.map, List.Nodup]

/-- DOLCE reductions use distinct qualities. -/
theorem dolce_qualities_distinct :
    (dolceReductions.map Reduction.quality).Nodup := by
  simp [dolceReductions, List.map, List.Nodup]

/-- Total count: 12 external relations reduced. -/
theorem total_reductions :
    bfoReductions.length + dolceReductions.length = 12 := by
  native_decide

/-- A concrete reduction: BFO's "has-participant" encodes as
    participant → situation with the inverse meta-quality,
    so "situation has-participant X" becomes "X belongs-to situation
    as participant" and the inverse derivation recovers the original
    direction. -/
example : ∃ r ∈ bfoReductions,
    r.name = "has-participant" ∧ MetaQuality.inverse ∈ r.behaviors := by
  exact ⟨bfoReductions[1], List.get_mem _ _, rfl, List.Mem.head _⟩

end Haak.Ontology.Expressiveness
