# Agent instructions

This repository currently contains a plan, not an implementation. Read START_HERE.md and every linked specification before implementing its component.

## User constraints

- Independent public project named VoxEntity-EU.
- German and French first; Spanish is a later optional extension.
- No ELO integrations, enterprise document tooling or related positioning.
- Hugging Face PRO and Kaggle are available in principle; verify account access and actual compute before use.
- No recruitment or newly recorded consenting speakers is required.
- Do not add calendar schedules, deadlines or development-duration estimates.
- Keep the original Orca transcript and other repositories untouched.

## Execution

Implement the ordered backlog; update its checkboxes only with evidence. Routine local implementation and tests should continue autonomously. This handoff is not permission to incur unbounded paid inference charges or send outreach messages.

Keep core scoring CPU-only and offline. Isolate optional model dependencies. Never silently replace real model runs with fixtures or mocks. Never hide failed requests by shrinking denominators.

Do not feed gold labels, filenames encoding values, candidate lists, QA transcripts or generation prompts to evaluated systems. Predictions and truth use separate access paths.

Every downloaded model/dataset must resolve to an immutable revision and documented rights. Public availability and a model license are not proof of unrestricted rights in all generated audio. Preserve asset-specific attribution.

The public narrative must state synthetic speech, simulated telephone channel, sample counts and review status. Human-control scores stay separate. Do not assert first-ever novelty, production readiness or causal hiring impact.

Use git diff and targeted tests before each implementation commit. Exclude secrets, weights, caches, downloaded corpora and bulk audio from Git. Do not modify sibling voice-evals; build an adapter here.
