# Corpus, acquisition and rights

## A. Main synthetic corpus

180 cases = 2 languages × 6 classes × 15 cases per class. A case has one target entity; a correction may also mention a previous value, but the gold contains only the final one. Each case generates a clean audio and a telephone transform: 360 files, with an explicit parent relation.

Classes: person_name, phone, email, calendar_value, postal_address, reference_code.

Per language/class cell distribute 15 cases as: 5 direct, 4 with spelling/phonetic difficulty, 3 segmented or spelled out, 3 with self-correction. For dates, segmentation means verbalization of components, not artificial spelling. Each language requires its own templates.

Reserve 5 dev and 10 test cases per cell: 60 dev / 120 test, 120/240 audios. Assign template families and values to a single split. Keep all acoustic versions, voices and synthesizers of the same scenario in its partition. Do not generate near-identical synonyms on both sides.

Create original pools with seed and rules, without scraping real people's names/addresses. Fictitious values may coincide with real people; never claim they are verifiably nonexistent identities. Do not link multiple identifiers to real people.

Emails: example.com/example.org. Phones: prefer fictional ranges documented by the regulator; if no DE/FR range is verified, use explicit test sequences, do not assert they are reserved numbers. Do not call or validate by SMS. The task measures digit and prefix copying, not reachability. Addresses: fictitious combinations, no geocoding or attached identity.

## B. Voice generation

Qwen CustomVoice 0.6B is the primary candidate (S03). Use predefined voices, no personal recording or cloning. Choose two valid speaker IDs via the API, test both in both languages and balance 90 cases per voice: per cell, 8/7 alternating. Do not assign voice by difficulty.

Save written text, text actually sent to TTS, parameters, voice, revision, environment, seed and all attempts. Verbalize numbers, signs and abbreviations explicitly when pronunciation is part of the case. Do not replace the target spellings in the gold with pronunciation.

Do not assume identical audio across GPUs. Freeze bytes and hashes; regeneration is a new artifact version. A second TTS family is a separate analysis over the same cases, without falsely adding statistical independence.

## C. QA without new speakers

Lack of recruitment does not imply lack of review. The author or implementer may listen to already generated material; they do not have to contribute their voice.

Automated validation: decodable file, mono, finite amplitude, no material clipping, nonzero energy, duration reasonable for length, no truncation. Proposed values: duration between 1 and 45 seconds, saturated-sample fraction below 0.1%; record justified exceptions.

Transcription by one or more ASRs only produces alerts. Never discard an audio because the evaluated model cannot transcribe it: that would bias the benchmark.

Before calling the corpus 'verified', review each clean audio by listening to the entities and corrections. Categories: accepted, wrong_synthesis, ambiguous, truncated, pending_review. On wrong pronunciation, fix the generation or exclude with a reason; never modify the gold to favor a prediction. Record replaced IDs and attempts.

If the implementer lacks reliable hearing or language competence, publish only an 'automated-QA/provisional' version with that limitation. Do not declare human review nonexistent. Technical delivery may advance; the 'verified' label stays blocked.

Review acoustic transforms automatically and listen to a stratified sample plus all technical failures. The noise must not introduce external speech or PII.

## D. Acoustic channel

clean: PCM16 mono 16 kHz, derived from a preserved TTS master.
telephone: from the same master; 300–3400 Hz filter, resample to 8 kHz, seeded gaussian noise at 20 dB SNR of active speech, G.711 A-law encode/decode; store PCM16 mono 8 kHz.

Pin the implementation and filter coefficients (order-6 Butterworth SOS), resampler, activity/energy calculation, seed, codec and versions. Measure SNR before the codec. Adjust the gain of the pair with a common rule and record clipping, never normalize each condition arbitrarily afterwards.

This is a simulated channel, not a PSTN call nor a representation of all codecs. Add bandlimit-only and noise of varying intensity as optional ablations; the main comparison mixes effects and does not causally identify each one.

## E. Existing human control

FLEURS de_de and fr_fr, pinned revision. Deterministically select 50 rows per language from the test split by ID hash without looking at results. If fewer exist, report the exact quantity. Do not alter text or replace it with synthetic entities over the original audio.

100 original recordings; paired clean/telephone versions allow measuring WER and degradation on human reading speech. Tag corpus=human_control and preserve speaker if present; never infer absent identity.

Do not force six entity classes or trim to fake calls. A future manual annotation of audible entities would be another suite with its own coverage. Do not mix main synthetic scoring with this control.

Download only DE/FR and the required split. Use a pinned snapshot, an explicit file list and a safe reader; do not enable remote script execution by default. If an old format requires it, inspect the script and look for a safe official export before deciding.

## F. Mandatory rights registry

Each source: source_id, URL, revision, file and SHA256, declared license, license text URL, holder/attribution, transformations, redistribution conditions, review status (verified/conditional/blocked), reason.

Separate licenses for code, weights, training dataset, resulting audio and annotation. FLEURS requires attribution and indicating modifications. CC0/CC-BY of a base dataset does not suffice to infer rights over a derived checkpoint.

Do not download commercial call corpora or reuse YouTube/podcasts merely because they are accessible. Do not use people's audio to clone voices. The core does not depend on that material.
