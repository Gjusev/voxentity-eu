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
systems capture exact entities (names, phone numbers, emails, dates,
addresses, reference codes) in German and French dictation, in clean and
simulated-telephone audio.*

The hook that travels: **both ASR families tested capture barely a third of
entities exactly (34.2% / 37.1%, overlapping CIs) against a 91% written-text
ceiling, and emails fail almost completely (0 to 20% in all three languages
tested)**. A transcript that reads fine can still carry the wrong digit. That is
a concrete, verifiable claim from `reports/report.md`; it is about the two ASR
systems measured, not about any commercial voice agent.

Secondary hooks, each its own future announcement (see Ongoing):

- Simulated telephone channel alone costs +5 pp on capture (whisper,
  [+0.8, +10.0]); on human speech WER nearly doubles (0.115 → 0.221).
- Multi-turn corrections: state persistence works (19/19 when both turns are
  heard); the loss is perception, not memory.
- Same scenarios, second TTS family: +10 pp. Corpus numbers are synthesizer-
  conditional; we publish both families side by side.

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
- **Rented (1 to 2, chosen):** X/Twitter or LinkedIn for the maintainer's
  existing network (pick whichever has real followers; check before launch);
  Hacker News *Show HN*; one subreddit post (r/MachineLearning or
  r/speechrecognition). Rented posts exist to funnel to the dataset/repo.
- **Borrowed (identify, do not pitch from this session):** HF community forum
  / Discord benchmark channels; speech newsletters that accept community
  submissions (candidates to list when launch day approaches); a Show HN or
  Reddit thread where the author answers technical questions in comments is
  itself borrowed credibility.

## Phases (entry conditions, not dates)

- **P0 Internal (done).** Gates G1 to G6 green with evidence
  (`reports/release_gates.md`); adversarial audit closed; bundle validates;
  notebook reproduces byte-identical numbers from the bundle.
- **P0.5 Private reproduction (alpha): skipped by owner decision** (went public
  directly). Its goal moves to P4: ask early readers for reproductions.
  Original plan: Entry: P0. The owner shares the repo
  privately with 2 to 3 people who know speech evaluation and asks one thing: run
  `notebooks/reproduce/reproduce.ipynb` from a clean checkout and try to break
  the scorer. Exit: at least one independent reproduction reports identical
  numbers, and every reported problem is fixed or documented. (Invitations are
  the owner's; nothing is sent from this repository's tooling.)
- **P1 Repo public (done; CI green on first run).** Entry: tier-1 gates re-run green on the exact commit to
  be pushed. Action: `gh repo create` (PUBLISHING.md §Tier 1). Verify the
  clone builds and tests pass from a clean checkout.
- **P2 Dataset + Space public (done, with audio; verified logged out, see
  RELEASE_MANIFEST.json).** Entry: P1 verified; dataset card matches the
  bundle; Space runs in the no-audio configuration. Actions: HF upload
  commands in PUBLISHING.md §Tier 1; then open both URLs logged out and
  confirm files load; record URLs + SHAs in `RELEASE_MANIFEST.json`; replace
  "not yet published" wording in README and dataset card.
- **P3 Announcements (unblocked; owner-triggered only).** Entry: P2 URLs live
  and verified (met) **and** a listening spot check of the synthetic clips
  (council condition: Taleb, Kahneman), reported in the post either way.
  Spot check done by the owner, no issues surfaced; recorded in the post
  draft below. Nothing is posted by repository tooling. Order: Show HN
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

## Owned capture (what a visit turns into)

No email list or blog, by choice. For a benchmark the conversion is a contribution:

- GitHub Discussions on, with a pinned "Reproductions" thread (post your numbers,
  matching or not) and a "Submit a system" issue template that points to
  CONTRIBUTING.md (predictions only, never gold; same scorer).
- HF dataset "Community" tab for data questions; the Space links back to both.
- Every rented/borrowed post ends with one link: the repo README.

## Launch assets

- `reports/figures/cell_accuracy.svg` rendered to PNG for social cards (the SVG
  is the source; re-render if numbers change).
- One Space screenshot in the no-audio configuration, showing a real error case.
- The README results table as the single source of quoted numbers.
- `docs/media/voxentity-eu-social-4x5.mp4`: 18.5 s, 1080×1350 social cut for the
  LinkedIn feed (upload natively; use `voxentity-eu-social-4x5-thumb.jpg` as the
  thumbnail). Source: `brag-output/social-4x5/`. Status line stays on screen throughout.

## Deliberately not used

- Product Hunt: consumer/SaaS audience, launch-day ranking dynamics; a research
  benchmark gains nothing from it.
- Paid promotion, cold outreach, influencer pitches: out of scope (AGENTS.md).

## Ongoing cadence

Scale the announcement to the change (skill matrix): a new measured suite or
system = its own short post (P5); scorer/extractor versions (rex-N, norm-N) =
CHANGELOG.md entry plus a note in the report; fixes = CHANGELOG only. Each
announcement re-runs the gates first.

## Metrics (no targets, no dates)

Repo: stars, forks, issues/PRs, clones. Dataset: downloads/likes on HF.
Space: visits. Quality signals worth more than volume: third-party
reproductions (matching or discrepant), citations, an issue that reports a
real scoring bug, someone adding a system to `runs/`.

## Drafts (not sent; numbers from reports/, quoted 2026-10 commit)

### Show HN title + text

> **Show HN: VoxEntity-EU, can ASR capture your phone number in German or French?**
>
> Open benchmark for exact spoken-entity capture: names, phone numbers,
> emails, dates, addresses, reference codes: the part a voice form has to get
> right character for character. 180 synthetic scenarios
> (Qwen3-TTS, DE+FR), each as clean audio and a simulated 8 kHz telephone
> channel; 120 independent test scenarios per system. Automated QA only, no
> human listening review yet, so it is provisional.
>
> Headline results (test, n=240 scenario×condition, same extractor for all
> systems): Whisper large-v3-turbo 34.2% [28.3, 40.4] and Voxtral Mini
> 37.1% [30.0, 43.8] exact capture, vs a 90.8% written-text ceiling. The two
> ASR families are statistically indistinguishable. Emails fail at 0 to 20% in
> German, French and Spanish. The simulated phone channel alone costs +5 pp
> (whisper). And on the same scenarios a second TTS family (Piper) scores
> +10 pp, so corpus numbers depend on the synthesizer, which we publish
> per-family.
>
> Everything is CPU-reproducible from frozen predictions (checksums in the
> release bundle; a notebook regenerates every table offline). Human-speech
> control (FLEURS, CC-BY; likely seen in ASR training, so a channel check, not a
> generalization test) reported separately: telephone simulation nearly doubles
> WER on human speech too. Code, reports, dataset card and a CPU
> demo: https://huggingface.co/datasets/Gjusev/voxentity-eu.

### LinkedIn post (link in first comment; X uses the shorter body below)

> A transcript can read perfectly and still carry the wrong phone number.
>
> +33 6 05 36 23 71 came back as +33 6 75 36 23 71. The text looked fine.
> The number was wrong, and every downstream form inherited it.
>
> That failure is what VoxEntity-EU measures: exact spoken-entity capture in
> German and French. Names, phone numbers, emails, dates, addresses,
> reference codes. One wrong character fails the slot.
>
> Setup: 180 synthetic scenarios (Qwen3-TTS), each recorded clean and
> through a simulated 8 kHz telephone channel. 120 independent test
> scenarios per system, n=240 scored items each, same extractor for every
> system.
>
> Exact capture, 95% CI:
>
> Whisper large-v3-turbo: 34.2% [28.3, 40.4]
> Voxtral Mini 3B: 37.1% [30.0, 43.8]
> Written-text ceiling: 90.8% [87.5, 94.2]
>
> The two ASR families are statistically indistinguishable. That is a null
> result and it is published as one.
>
> Where it breaks: emails reach 0 to 20% per language and system. The
> simulated phone line alone costs Whisper 5 points [+0.8, +10.0]. When a
> second TTS family (Piper) voices the same scenarios, scores move +10
> points [+4.2, +15.4], so every absolute number here is
> synthesizer-conditional and published per family.
>
> One honest scar: my first extractor version produced a wrong headline
> conclusion. I retracted it publicly and the changelog documents what was
> measured wrong.
>
> Status: synthetic speech, simulated channel, review is automated QA plus my
> listening spot check, which surfaced no issues. The systematic per-clip
> review is still open, so the corpus stays provisional. Everything rescores
> on a CPU with no network.
>
> Link in the first comment.
>
> #ASR #SpeechRecognition

First comment:

> Repo: https://github.com/Gjusev/voxentity-eu
> Dataset (audio included): https://huggingface.co/datasets/Gjusev/voxentity-eu
> Listen to real failures: https://huggingface.co/spaces/Gjusev/voxentity-eu-results

### LinkedIn post, short version (preferred; same first comment)

> A transcript can read fine and still carry the wrong phone number.
>
> The caller said +33 6 05 36 23 71. On a simulated phone line, Whisper wrote
> +33 6 75 36 23 71. One digit, and any form that stores it now holds a wrong
> number.
>
> VoxEntity-EU measures that failure. Does a speech model capture a dictated
> name, phone number, email, date, address or reference code exactly, in
> German and French? One wrong character fails the slot.
>
> 120 synthetic test scenarios, each clean and through a simulated phone
> line, 240 scored items per model:
>
> Whisper large-v3-turbo: 34.2% [28.3, 40.4]
> Voxtral Mini 3B: 37.1% [30.0, 43.8]
> Same extractor on the correct text: 90.8%
>
> Emails land at 0 to 20%.
>
> Read the numbers with one caveat: the speech is synthetic (Qwen3-TTS), and
> a second TTS scores 10 points higher, so absolute values depend on the
> synthesizer. Review so far is automated QA plus my own listening spot
> check, so the corpus stays provisional.
>
> Code, data with audio and a results browser where you can hear each
> failure are open. Links in the first comment.
>
> Which entity breaks your voice pipeline first?
>
> #SpeechRecognition #ASR

### Hugging Face post (huggingface.co/posts; links allowed in the body)

> Released VoxEntity-EU v0.1.0, an open benchmark for exact spoken-entity
> capture in German and French: names, phone numbers, emails, dates, postal
> addresses, reference codes.
>
> The metric is exact slot match, not WER. A phone number with one wrong digit
> counts as a failure.
>
> Test split: 120 synthetic scenarios × (clean 16 kHz + simulated 8 kHz
> telephone) = 240 items per system, same extractor for every system,
> stratified bootstrap 95% CIs.
>
> - openai/whisper-large-v3-turbo: 34.2% [28.3, 40.4]
> - mistralai/Voxtral-Mini-3B-2507: 37.1% [30.0, 43.8]
> - correct text through the same extractor (ceiling): 90.8% [87.5, 94.2]
> - the phone line costs Whisper +5.0 pp [+0.8, +10.0]
> - emails: 0 to 20% per language and system
> - the same scenarios voiced by Piper instead of Qwen3-TTS: +10.0 pp
>   [+4.2, +15.4], so absolute numbers depend on the synthesizer
>
> Status: provisional. Synthetic speech (Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice),
> simulated channel, automated QA plus a maintainer listening spot check; no
> systematic per-clip review yet.
>
> Dataset (1,864 WAVs, gold, frozen predictions, checksums):
> https://huggingface.co/datasets/Gjusev/voxentity-eu
> Listen to every scored case:
> https://huggingface.co/spaces/Gjusev/voxentity-eu-results
> Code, CPU-only rescoring: https://github.com/Gjusev/voxentity-eu
>
> To add your model: run it on the exported inputs (no gold), score with
> `voxentity score`, open an issue with the template. Scorer criticism welcome.

### Short social post (X, same substance)

> A transcript can read fine and still get your phone number wrong. VoxEntity-EU:
> open DE/FR benchmark for exact entity capture (names, phones, emails,
> dates, addresses, codes). 120 independent synthetic test scenarios × clean
> + simulated telephone. Result: Whisper 34%, Voxtral 37% exact capture vs a
> 91% ceiling; emails ≈ 0 to 20% in all 3 languages we tested. Provisional
> (automated QA). CPU-reproducible, data + demo: https://github.com/Gjusev/voxentity-eu

### Reddit (r/MachineLearning, title prefixed `[P]`): opening text

> We built a benchmark for the boring but decisive part of voice interfaces:
> whether the system captures exact values (phone numbers, emails, names,
> dates, addresses, reference codes) rather than roughly the right words.
> German + French, 180 synthetic scenarios via Qwen3-TTS with a simulated
> telephone channel; automated QA only (provisional). Same extractor for all
> systems: Whisper large-v3-turbo 34.2%, Voxtral Mini 37.1% (CIs overlap) vs
> 90.8% written ceiling; per-cell failure analysis in the report. A second
> TTS family moves the numbers +10 pp, so we publish per-synthesizer. Happy
> to answer methods questions; criticism of the scorer is welcome; norm-2 and
> the extractor are frozen and documented. Links in the repo README.

### HF community forum: opening text

> Sharing a DE/FR spoken-entity benchmark (names/phones/emails/dates/
> addresses/codes): 180 synthetic scenarios (Qwen3-TTS; provisional,
> automated QA only), clean + simulated telephone, frozen predictions in the
> release bundle, CPU notebook that reproduces every number. Two ASR families
> land at ~34 to 37% exact capture vs a 91% written ceiling; emails fail almost
> everywhere. Extension suites: code-switching, multi-turn corrections,
> voice variation, second TTS family (+10 pp), Spanish. Looking for
> third-party reproductions and scorer criticism, not applause.

### One-line for profiles/bios

> Maintainer of VoxEntity-EU, an open DE/FR benchmark for exact spoken-entity
> capture in voice interfaces (synthetic speech, provisional, reproducible).

## Pre-launch checklist (mirrors PUBLISHING.md gates)

- [ ] All PUBLISHING.md gates green on the exact commit to be pushed.
- [ ] `hf` / `gh` namespaces confirmed (`voxentity doctor --profile hf`,
      `gh auth status`): verified read-only in this session: GitHub `Gjusev`
      (scopes repo, workflow; `Gjusev/voxentity-eu` free), HF `Gjusev` (dataset and
      Space names return 404-equivalent 401 = not existing).
- [ ] Drafts re-checked against the final published numbers (regenerate
      reports and re-quote; do not carry numbers across report changes).
- [ ] Guardrails section above re-read immediately before posting anything.
- [ ] Each announcement links to verified URLs only (post-P2), never to local
      paths or "coming soon".
