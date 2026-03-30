/-!
# Ontology — Core Types

Formalizes the relational situational ontology from ontology/01-objects.md
and ontology/02-relations.md.

## Design

The ontology has one primitive relation — *belongs-to* — and a single
extension: the *quality*. Qualities are themselves entities, giving
reflexive closure. This file defines the types; MetaQualities.lean
defines the inference rules; Closure.lean proves termination.

## Key definitions

- `Entity`: anything that exists in the ontology
- `Quality`: the nature of a belonging (how A depends on B)
- `Belonging`: a directed edge A →[q] B
- `AxisRole`: actor, method, domain, material (qualities, not types)
-/

namespace Haak.Ontology

/-- Entity identifiers. Opaque type wrapping a natural number. -/
structure EntityId where
  val : Nat
  deriving DecidableEq, Repr

/-- Quality identifiers. Separate namespace from entities,
    but qualities *are* entities (see Closure.lean). -/
structure QualityId where
  val : Nat
  deriving DecidableEq, Repr

/--
**Definition R1 (Belongs-to).**
The single primitive relation. A belongs to B with quality q.
Directed: A is the dependent, B is the context.

"A file belongs to a paper; the paper does not thereby belong to the file.
A participant belongs to a situation; the situation does not thereby
belong to the participant."
-/
structure Belonging where
  /-- The dependent entity -/
  dependent : EntityId
  /-- The context entity -/
  context : EntityId
  /-- The nature of the dependence -/
  quality : QualityId
  deriving DecidableEq, Repr

/--
**Definition R4 (Axis-role as quality).**
The four axis-roles are not types of entities — they are qualities
of belongings. Nothing *is* an actor in absolute terms; things
*participate as* actors in specific situations.
-/
inductive AxisRole where
  | actor
  | method
  | domain
  | material
  deriving DecidableEq, Repr

/-- A knowledge base: a set of belongings plus quality metadata. -/
structure OntologyState where
  /-- All asserted belongings -/
  belongings : List Belonging
  /-- Entity count (for fresh ID generation) -/
  nextEntity : Nat
  /-- Quality count -/
  nextQuality : Nat

/-- Empty ontology. -/
def OntologyState.empty : OntologyState :=
  { belongings := [], nextEntity := 0, nextQuality := 0 }

/-- Assert a new belonging. -/
def OntologyState.assert (s : OntologyState) (b : Belonging) : OntologyState :=
  { s with belongings := b :: s.belongings }

/-- Query: all belongings where entity e is the dependent. -/
def OntologyState.dependenciesOf (s : OntologyState) (e : EntityId) : List Belonging :=
  s.belongings.filter (fun b => b.dependent == e)

/-- Query: all belongings where entity e is the context. -/
def OntologyState.dependentsOn (s : OntologyState) (e : EntityId) : List Belonging :=
  s.belongings.filter (fun b => b.context == e)

/-- Query: all entities that co-participate in a situation.
    Two entities co-participate if both belong to the same context. -/
def OntologyState.coParticipants (s : OntologyState) (e : EntityId) : List EntityId :=
  let myContexts := (s.dependenciesOf e).map Belonging.context
  s.belongings.filter (fun b => b.dependent != e && myContexts.contains b.context)
    |>.map Belonging.dependent
    |>.eraseDups

end Haak.Ontology
