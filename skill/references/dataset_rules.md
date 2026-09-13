# Dataset integrity rules

Dataset discovery optimizes for safe acceptance, not maximum recall.

## Required checks

Before automatic acceptance, establish:

- study/accession identity
- sample identity
- donor/animal linkage when applicable
- condition/control labels
- biological vs technical replicate structure
- tissue/anatomical region or injury zone where relevant
- assay/platform
- sample counts

## Blocking states

`UNRESOLVED`, `AMBIGUOUS`, and `REVIEW_REQUIRED` block automatic ingestion.

Never infer donor IDs, animal IDs, replicate relationships, infarct/border zone labels, or condition labels from weak context. Such cases remain explicit review items.

## Suitability vs identity

Dataset suitability is query-dependent. Keep the underlying metadata record separate from the relevance score for a specific research question.
