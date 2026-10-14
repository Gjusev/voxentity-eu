# Publishing (prepared, not run)

Nothing here has been executed. Each step publishes content externally and needs
explicit approval. Replace `<hf-user>` / `<gh-user>` with namespaces verified
during preflight (`voxentity doctor --profile hf`, `gh auth status`).
Release-gate evidence: [reports/release_gates.md](reports/release_gates.md).
Launch plan and drafts: [docs/launch/LAUNCH.md](docs/launch/LAUNCH.md).

## Gates before any push

- [ ] `pytest`, `ruff check .`, `python scripts/check_links.py` green (use
      `set -o pipefail` when piping test output).
- [ ] `python scripts/run_tracks.py && python scripts/score_all.py`, `voxentity
      compare …`, `voxentity report …` leave `reports/` unchanged
      (`git diff --exit-code reports`).
- [ ] Release bundle rebuilt and `voxentity release validate --bundle release_bundle` ok.
- [ ] `notebooks/reproduce/reproduce.ipynb` reports identical summaries.
- [ ] Corpus label decided: `verified` only after `scripts/review_package.py apply`
      covers 180/180 clean clips; otherwise every artifact says provisional.
- [ ] Public text states synthetic speech, simulated telephone channel, sample
      counts and review status; no novelty, production-readiness or hiring claims.

## Tier 1: publishable under the current rights registry

Assets with `verified` / `allowed` status or original project work: code
(Apache-2.0), annotations and manifests (CC-BY-4.0), predictions and reports,
FLEURS-derived human-control audio (CC-BY-4.0, attribution in
`attribution.json`). **No synthetic audio.**

```bash
# 1. GitHub (code, reports, small manifests; audio and weights stay ignored)
gh repo create <gh-user>/voxentity-eu --public --source . --push

# 2. Hugging Face dataset: bundle (no audio inside) + human-control audio
hf repo create <hf-user>/voxentity-eu --repo-type dataset
hf upload <hf-user>/voxentity-eu release_bundle . --repo-type dataset
hf upload <hf-user>/voxentity-eu data/human_control/audio/human_control audio/human_control --repo-type dataset
hf upload <hf-user>/voxentity-eu dataset_card/DATASET_CARD.md README.md --repo-type dataset

# 3. Space (CPU) without synthetic audio: tables, transcripts and scores only
python scripts/build_space_data.py
hf repo create <hf-user>/voxentity-eu-results --repo-type space --space_sdk gradio
hf upload <hf-user>/voxentity-eu-results space . --repo-type space --exclude "__pycache__/*" "audio/*"
```

Anyone can regenerate the synthetic audio locally from the published text,
pinned model revisions and `voxentity synthesize`, under their own acceptance of
the model terms.

## Tier 2: synthetic audio (blocked until an explicit owner decision)

Rights registry S03 (Qwen3-TTS outputs) and the Piper suite are `conditional`.
Evidence recorded in the registry: Apache-2.0 at the pinned revision, no usage or
output terms on the model card or in the code repository. AGENTS.md: a model
license alone is not proof of rights over all generated audio, so this tier needs
the project owner's recorded decision (registry entry to `verified`, reason and
date-free justification in `notes`), plus SIWIS CC BY 4.0 attribution for any
French Piper audio.

```bash
hf upload <hf-user>/voxentity-eu data/audio/synthetic audio/synthetic --repo-type dataset
for s in codeswitch multiturn voices piper es; do
  hf upload <hf-user>/voxentity-eu data/ext/$s/audio/synthetic ext/$s/audio --repo-type dataset
done
hf upload <hf-user>/voxentity-eu-results space/audio audio --repo-type space
```

After each push, open the URL logged out, confirm files load, and record the
verified URLs and commit SHAs in `RELEASE_MANIFEST.json`. Only then replace the
"not yet published" wording in README.md and the dataset card.
