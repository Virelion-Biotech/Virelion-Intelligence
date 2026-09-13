# Dataset metadata rules

## Acceptance

A dataset may be marked `ACCEPTED` only when its identity is resolved, the accession is authoritative, condition/control fields are interpretable, and replicate/sample structure is sufficiently specified for the intended analysis.

## Mandatory non-inference rules

Never infer donor or animal identity from sample order. Never treat technical replicates as biological replicates. Never infer infarct, border, remote, or other anatomical zone labels from unrelated metadata. Never infer missing condition labels from a publication title alone.

## Statuses

`RESOLVED` means the required identity structure is supported by source metadata. `REVIEW_REQUIRED` means the dataset may be useful but cannot be automatically accepted. `UNRESOLVED` and `AMBIGUOUS` are blocked for automatic ingestion.

## Recommended fields

Accession, study title, organism, tissue, cell type, condition, control, assay, platform, sample count, replicate count, donor/animal identifier, anatomical region, timepoint, batch and publication linkage.
