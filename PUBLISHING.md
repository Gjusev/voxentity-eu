# Publishing (prepared, not run)

Nothing here has been executed. Each step publishes content externally and needs
explicit approval. Replace `<hf-user>` / `<gh-user>` with namespaces verified
during preflight (`voxentity doctor --profile hf`).

## Gates before any push

- [ ] `pytest`, `ruff check .`, `python scripts/check_links.py` green.
- [ ] `python scripts/run_tracks.py && python scripts/score_all.py` then
      `voxentity report …` leaves `reports/` unchanged (`git diff --exit-code reports`).
- [ ] Release bundle rebuilt and `voxentity release validate --bundle release_bundle` ok.
- [ ] `notebooks/reproduce/reproduce.ipynb` runs and reports identical summaries.
- [ ] Corpus label decided: `verified` only after `scripts/review_package.py apply`
      covers 180/180 clean clips; otherwise every artifact says provisional.
- [ ] Rights: `rights_registry.jsonl` has no `blocked` asset in what is uploaded;
      synthetic-audio rights stay `conditional` as stated in DATA_LICENSE.md;
      FLEURS-derived audio keeps CC-BY-4.0 attribution (`attribution.json`).
- [ ] Public text states synthetic speech, simulated telephone channel, sample
      counts and review status; no novelty, production-readiness or hiring claims.

## Commands

```bash
# 1. GitHub (code, reports, small manifests; audio and weights stay ignored)
gh repo create <gh-user>/voxentity-eu --public --source . --push

# 2. Hugging Face dataset: bundle + audio (WAV, explicit sample rates)
hf repo create <hf-user>/voxentity-eu --repo-type dataset
hf upload <hf-user>/voxentity-eu release_bundle . --repo-type dataset
hf upload <hf-user>/voxentity-eu data/audio/synthetic audio/synthetic --repo-type dataset
hf upload <hf-user>/voxentity-eu data/human_control/audio/human_control audio/human_control --repo-type dataset
hf upload <hf-user>/voxentity-eu dataset_card/DATASET_CARD.md README.md --repo-type dataset

# 3. Hugging Face Space (CPU): results.json and audio come from build_space_data.py
python scripts/build_space_data.py
hf repo create <hf-user>/voxentity-eu-results --repo-type space --space_sdk gradio
hf upload <hf-user>/voxentity-eu-results space . --repo-type space --exclude "__pycache__/*"
```

After each push, open the URL logged out, confirm files load, and record the
verified URLs and commit SHAs in `RELEASE_MANIFEST.json`. Only then replace the
"not yet published" wording in README.md and the dataset card.

## Communication drafts (not sent)

Short post:

> VoxEntity-EU is an open German/French benchmark for exact spoken-entity capture
> (names, phone numbers, emails, dates, addresses, reference codes). 120 synthetic
> test scenarios, each in clean and simulated-telephone audio. Whisper
> large-v3-turbo and Voxtral Mini reach 34% and 37% exact capture through the same
> extractor (95% CIs overlap) against a 91% written-text ceiling; emails and phone
> numbers fail most. Synthetic speech, automated QA only. Code, data, report and
> a CPU demo: <links after verification>.

CV line (docs/08 template, real numbers):

> Built VoxEntity-EU, an open German/French spoken-entity benchmark; evaluated two
> ASR families across 120 independent test scenarios with paired telephone-channel
> simulations, publishing reproducible results and final-slot failure analysis.
