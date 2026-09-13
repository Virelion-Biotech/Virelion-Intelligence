# Evidence framework

## Evidence level

| Level | Meaning |
|---|---|
| E0 | Unverified signal |
| E1 | Secondary source |
| E2 | Primary publication or authoritative primary record |
| E3 | Primary evidence plus public code/data |
| E4 | Independent reproduction |
| E5 | Replicated across independent studies |

Evidence level describes the strength/status of the underlying evidence. It is not the same as extraction confidence.

## Evidence depth

- M0: metadata only
- M1: abstract
- M2: accessible full-text prose
- M3: full text plus figures/tables
- M4: full text plus linked data/code

## Claim classes

- SOURCE_FACT: directly reported by the source.
- AUTHOR_INTERPRETATION: interpretation stated by the source authors.
- VIRELION_INFERENCE: analysis produced by Virelion Intelligence from one or more sources.
- VIRELION_HYPOTHESIS: proposed question or mechanism requiring future validation.

Never collapse these classes in generated prose.

## Required provenance

Every substantive claim must link to:

```text
claim -> evidence -> source -> stable identifier/URL
```

The evidence record should identify the supporting section, figure, table, or text span when available.
