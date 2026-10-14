# Brief for the next agent

Implement VoxEntity-EU from this specification. The goal is an independent public project that demonstrates evaluation engineering capability and reproducible results on spoken entities in DE/FR.

## Reading order

1. README.md and AGENTS.md.
2. docs/01-product.md and docs/02-research.md.
3. docs/03-data.md through docs/07-compute.md.
4. docs/08-publication.md through docs/11-decisions.md.
5. research/artifacts.json and the examples in examples/.

External links justify existing capabilities. Design decisions and acceptance thresholds are decisions of this project, not empirical results.

## First implementation action

Check git status, create the minimal Python package, typed contracts and scorer tests. Create a tiny set of textual fixtures with hand-calculated results. Do not download a full corpus or start a GPU before validating contracts, gold isolation and smoke tests.

## Sequence

Contracts and scorer → cases → generation and QA → acoustic transforms → baselines → agent with slots → human control → reports → Space/notebooks → publication preparation.

If there is no GPU or credentials, continue with all offline work and prepare resumable jobs. Record what is pending in IMPLEMENTATION_STATUS.md. Do not invent results to declare a phase complete.

## Definition of completion

A third party can obtain the published dataset, run offline scoring on verifiable predictions, reproduce at least two open baselines, listen to errors in the Space and understand exactly what each table measures. Public references must exist and open before declaring them published.

The mandatory scope includes a reference agent that persists observable slots. Two commercial providers are an extension conditioned on access and budget; they do not block the open version.

## Suggested continuation prompt

> Read AGENTS.md and START_HERE.md. Implement the backlog in docs/09-implementation.md in order, respecting its acceptance criteria and docs/10-validation.md. Keep the DE/FR scope and synthetic results separate from human control. Use HF/Kaggle resources once configured and leave a trace of any external blocker. Do not add dates or duration estimates.
