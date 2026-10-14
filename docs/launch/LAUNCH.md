# Launch plan and drafts (prepared, not executed)

Everything here is a draft. No account has been used to publish, post or
message anyone; sending anything requires the owner's explicit go-ahead
(AGENTS.md). No calendar dates or durations: each phase starts when its entry
condition holds, not on a schedule.

## Guardrails (apply to every text, in every channel)

1. State, in the text itself: synthetic speech, simulated telephone channel,
   sample counts, automated-QA-only review status ("provisional", no human
   listening yet).
2. No "first ever", no production-readiness, no hiring-impact claims.
3. Human-control numbers stay separate from synthetic-corpus numbers.
4. Numbers always with n and, where comparison is claimed, confidence
   intervals. Null results are stated as null (whisper vs voxtral: no
   conclusive difference).
5. Absolute numbers are conditional on the synthesizer (Piper suite: +10 pp on
   the same scenarios). Say so when quoting absolutes.
6. Spanish is an extension suite, not a third core locale.

## Positioning

One sentence: *an open, CPU-reproducible benchmark measuring whether speech
systems capture exact entities — names, phone numbers, emails, dates,
addresses, reference codes — in German and French dictation, in clean and
simulated-telephone audio.*

The hook that travels: **both ASR families tested capture barely a third of
entities exactly (34.2% / 37.1%, overlapping CIs) against a 91% written-text
ceiling, and emails fail almost completely (0–20% in all three languages
tested)**. Voice agents that "sound fine" still lose the address. That is a
concrete, honest, verifiable claim from `reports/report.md`.

Secondary hooks, each its own future announcement (see Ongoing):

- Simulated telephone channel alone costs +5 pp on capture (whisper,
  [+0.8, +10.0]); on human speech WER nearly doubles (0.115 → 0.221).
- Multi-turn corrections: state persistence works (19/19 when both turns are
  heard); the loss is perception, not memory.
- Same scenarios, second TTS family: +10 pp. Corpus numbers are synthesizer-
  conditional — a caution the field under-reports.

## Audiences (in priority order)

1. ASR / voice-agent engineers who need a failure-mode benchmark (HF, GitHub).
2. Speech and multilingual NLP researchers (DE/FR focus; evaluation interest).
3. Eval-curious ML practitioners who engage with benchmarks on HF.

## Channels (ORB)

- **Owned (canonical):** GitHub repo; HF dataset (tier-1 bundle + human-control
  audio); HF Space (CPU, tables/transcripts/scores, runs without audio/);
  README + dataset card as the permanent explainer. Everything rented/borrowed
  links only here. No email list or blog exists yet; add when there is
  traffic worth capturing.
- **Rented (1–2, chosen):** X/Twitter or LinkedIn for the maintainer's
  existing network (pick whichever has real followers — check before launch);
  Hacker News *Show HN*; one subreddit post (r/MachineLearning or
  r/speechrecognition). Rented posts exist to funnel to the dataset/repo.
- **Borrowed (identify, do not pitch from this session):** HF community forum
  / Discord benchmark channels; speech newsletters that accept community
  submissions (candidates to list when launch day approaches); a Show HN or
  Reddit thread where the author answers technical questions in comments is
  itself borrowed credibility.

## Phases (entry conditions, not dates)

- **P0 Internal (done).** Gates G1–G6 green with evidence
  (`reports/release_gates.md`); adversarial audit closed; bundle validates;
  notebook reproduces byte-identical numbers from the bundle.
- **P1 Repo public.** Entry: tier-1 gates re-run green on the exact commit to
  be pushed. Action: `gh repo create` (PUBLISHING.md §Tier 1). Verify the
  clone builds and tests pass from a clean checkout.
- **P2 Dataset + Space public.** Entry: P1 verified; dataset card matches the
  bundle; Space runs in the no-audio configuration. Actions: HF upload
  commands in PUBLISHING.md §Tier 1; then open both URLs logged out and
  confirm files load; record URLs + SHAs in `RELEASE_MANIFEST.json`; replace
  "not yet published" wording in README and dataset card.
- **P3 Announcements.** Entry: P2 URLs live and verified. Order: Show HN
  (morning-neutral, author available all day to answer), maintainer's stronger
  social platform, then the subreddit, then the HF forum thread. One platform
  per working session so questions get real answers.
- **P4 Listen and triage.** Answer every technical comment; convert recurring
  questions into README/FAQ commits; log third-party reproductions and
  discrepancies as issues, not defenses.
- **P5 Next launch moments (staggered, each entry = a merged, measured suite
  plus a green gate run):** Spanish suite; second-TTS-family cautionary
  result; multi-turn persistence finding; code-switching. One short post each,
  linking back to the same repo/dataset. Stagger rather than bundle: each is a
  separate reason for someone to look.

Tier-2 (synthetic audio) is not a launch phase; it unlocks only by the
owner's recorded rights decision (PUBLISHING.md §Tier 2).

## Metrics (no targets, no dates)

Repo: stars, forks, issues/PRs, clones. Dataset: downloads/likes on HF.
Space: visits. Quality signals worth more than volume: third-party
reproductions (matching or discrepant), citations, an issue that reports a
real scoring bug, someone adding a system to `runs/`.

## Drafts (not sent; numbers from reports/, quoted 2026-10 commit)

### Show HN title + text

> **Show HN: VoxEntity-EU – can ASR capture your phone number in German or French?**
>
> Open benchmark for exact spoken-entity capture: names, phone numbers,
> emails, dates, addresses, reference codes — the part voice assistants
> actually have to get right character-for-character. 180 synthetic scenarios
> (Qwen3-TTS, DE+FR), each as clean audio and a simulated 8 kHz telephone
> channel; 120 independent test scenarios per system. Automated QA only, no
> human listening review yet — provisional by design.
>
> Headline results (test, n=240 scenario×condition, same extractor for all
> systems): Whisper large-v3-turbo 34.2% [28.3, 40.4] and Voxtral Mini
> 37.1% [30.0, 43.8] exact capture, vs a 90.8% written-text ceiling. The two
> ASR families are statistically indistinguishable. Emails fail at 0–20% in
> German, French and Spanish. The simulated phone channel alone costs +5 pp
> (whisper). And on the same scenarios a second TTS family (Piper) scores
> +10 pp — so corpus numbers are synthesizer-conditional, which we publish
> per-family.
>
> Everything is CPU-reproducible from frozen predictions (checksums in the
> release bundle; a notebook regenerates every table offline). Human-speech
> control (FLEURS, CC-BY) reported separately: telephone simulation nearly
> doubles WER on human speech too. Code, reports, dataset card and a CPU
> demo: <links after P2 verification>.

### Short social post (X/LinkedIn, same body)

> Voice agents sound fluent — and still lose your phone number. VoxEntity-EU:
> open DE/FR benchmark for exact entity capture (names, phones, emails,
> dates, addresses, codes). 120 independent synthetic test scenarios × clean
> + simulated telephone. Result: Whisper 34%, Voxtral 37% exact capture vs a
> 91% ceiling; emails ≈ 0–20% in all 3 languages we tested. Provisional
> (automated QA). CPU-reproducible, data + demo: <links>.

### Reddit (r/MachineLearning, flair: Project/Finder) — opening text

> We built a benchmark for the boring but decisive part of voice interfaces:
> whether the system captures exact values (phone numbers, emails, names,
> dates, addresses, reference codes) rather than roughly the right words.
> German + French, 180 synthetic scenarios via Qwen3-TTS with a simulated
> telephone channel; automated QA only (provisional). Same extractor for all
> systems: Whisper large-v3-turbo 34.2%, Voxtral Mini 37.1% (CIs overlap) vs
> 90.8% written ceiling; per-cell failure analysis in the report. A second
> TTS family moves the numbers +10 pp, so we publish per-synthesizer. Happy
> to answer methods questions; criticism of the scorer welcome — norm-2 and
> the extractor are frozen and documented. Links in the repo README.

### HF community forum — opening text

> Sharing a DE/FR spoken-entity benchmark (names/phones/emails/dates/
> addresses/codes): 180 synthetic scenarios (Qwen3-TTS; provisional,
> automated QA only), clean + simulated telephone, frozen predictions in the
> release bundle, CPU notebook that reproduces every number. Two ASR families
> land at ~34–37% exact capture vs a 91% written ceiling; emails fail almost
> everywhere. Extension suites: code-switching, multi-turn corrections,
> voice variation, second TTS family (+10 pp), Spanish. Looking for
> third-party reproductions and scorer criticism, not applause.

### One-line for profiles/bios

> Maintainer of VoxEntity-EU, an open DE/FR benchmark for exact spoken-entity
> capture in voice interfaces (synthetic speech, provisional, reproducible).

## Pre-launch checklist (mirrors PUBLISHING.md gates)

- [ ] All PUBLISHING.md gates green on the exact commit to be pushed.
- [ ] `hf` / `gh` namespaces confirmed (`voxentity doctor --profile hf`,
      `gh auth status` — done 2026-10: gh=Gjusev, hf=Gjusev).
- [ ] Drafts re-checked against the final published numbers (regenerate
      reports and re-quote; do not carry numbers across report changes).
- [ ] Guardrails section above re-read immediately before posting anything.
- [ ] Each announcement links to verified URLs only (post-P2), never to local
      paths or "coming soon".
