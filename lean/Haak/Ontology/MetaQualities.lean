import Haak.Ontology.Basic

namespace Haak.Ontology.MetaQualities

open Haak.Ontology

/-!
# Meta-Qualities (R5.1–R5.5)

The five meta-qualities are the grammar of the quality language.
-/

/-- Definition R5: the closed set of meta-qualities. -/
inductive MetaQuality where
  | inst       -- R5.1: classification
  | inverse    -- R5.2: bidirectional traversal
  | implies    -- R5.3: inference
  | transitive -- R5.4: closure
  | appliesTo  -- R5.5: domain constraint
  deriving DecidableEq, Repr

/-- A quality-level assertion: q1 relates to q2 via a meta-quality. -/
structure QualityRelation where
  source : QualityId
  target : QualityId
  kind : MetaQuality
  deriving DecidableEq, Repr

/-- Extended ontology state with quality-level metadata. -/
structure ExtendedState extends OntologyState where
  qualityRelations : List QualityRelation

/-- Inverse rule (R5.2): if A →[q₁] B and q₁ inverse q₂, then B →[q₂] A. -/
def deriveInverse (qs : List QualityRelation) (bs : List Belonging) : List Belonging :=
  bs.foldl (fun acc b =>
    match qs.find? (fun qr => qr.source == b.quality && qr.kind == MetaQuality.inverse) with
    | some qr => { dependent := b.context, context := b.dependent, quality := qr.target } :: acc
    | none => acc
  ) []

/-- Implies rule (R5.3): if A →[q₁] B and q₁ implies q₂, then A →[q₂] B. -/
def deriveImplied (qs : List QualityRelation) (bs : List Belonging) : List Belonging :=
  bs.foldl (fun acc b =>
    match qs.find? (fun qr => qr.source == b.quality && qr.kind == MetaQuality.implies) with
    | some qr => { b with quality := qr.target } :: acc
    | none => acc
  ) []

/-- Transitive rule (R5.4): if A →[q] B →[q] C and q transitive, then A →[q] C. -/
def deriveTransitive (qs : List QualityRelation) (bs : List Belonging) : List Belonging :=
  let transitiveQs := qs.filter (fun qr => qr.kind == MetaQuality.transitive) |>.map (·.source)
  bs.foldl (fun acc b1 =>
    if transitiveQs.contains b1.quality then
      let extensions := bs.filter (fun b2 =>
        b2.dependent == b1.context && b2.quality == b1.quality)
      extensions.foldl (fun acc2 b2 =>
        { dependent := b1.dependent, context := b2.context, quality := b1.quality } :: acc2
      ) acc
    else acc
  ) []

/-- The meta-quality set is complete. -/
def allMetaQualities : List MetaQuality :=
  [.inst, .inverse, .implies, .transitive, .appliesTo]

theorem allMetaQualities_complete (m : MetaQuality) : m ∈ allMetaQualities := by
  cases m <;> simp [allMetaQualities]

end Haak.Ontology.MetaQualities
