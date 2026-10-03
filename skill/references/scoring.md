# Scoring policy

## Relevance score (0–100)

Cardiovascular relevance 25%, scientific relevance 20%, Virelion relevance 15%, novelty 10%, dataset value 10%, translational relevance 10%, reproducibility signal 10%.

## Opportunity score (0–10)

Scientific importance 20%, evidence strength 20%, reproducibility 15%, data availability 15%, computational feasibility 10%, Virelion relevance 10%, differentiation 5%, translational potential 5%.

## Action bands

- `<4`: WATCH
- `4–5.99`: INTERESTING
- `6–7.49`: INVESTIGATE
- `7.5–8.99`: HIGH_PRIORITY
- `>=9`: STRATEGIC

Component scores must be stored so ranking is explainable. Final weighted arithmetic is deterministic and is not delegated to an LLM.
