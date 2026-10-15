# Reddit draft (not posted)

Owner posts manually (LAUNCH.md P3: after Show HN and the primary social post,
one subreddit only, one platform per working session). Post it as a **text
post**, not a link post: the body is where the caveats and method live, and
r/MachineLearning scores the discussion, not the URL. Numbers verified against
reports/ and README at drafting time (commit e4449b9); re-check before posting.

## Target and title

Primary: **r/MachineLearning**, tagged **[P]** (project). The sub requires one
of [D]/[R]/[P]/[N]; a benchmark built and released by its author is [P].
Title is plain on purpose; the number is the hook, no clickbait survives that
audience.

Title:

> [P] I benchmarked whether ASR captures a dictated phone number exactly, in German and French. Whisper: 34% exact. Same text written down: 91%

Alternative for r/speechrecognition (no tag convention; pick ONE subreddit,
do not post both):

> Open benchmark: exact capture of dictated phone numbers, emails and names in German and French (Whisper 34% exact, written-text ceiling 91%)

## Body (paste as text post)

A transcript can read perfectly and still carry the wrong phone number. The caller says +33 6 05 36 23 71, Whisper writes +33 6 75 36 23 71 on a simulated phone line, the sentence looks fine, and every form downstream now stores a wrong number. WER barely notices, because the rest of the sentence is right.

I built a benchmark around that failure. VoxEntity-EU scores whether a speech system captures a dictated name, phone number, email, date, postal address or reference code exactly, in German and French. One wrong character fails the slot.

Setup: 180 synthetic scenarios voiced with Qwen3-TTS, German and French, each in a clean 16 kHz version and through a simulated 8 kHz telephone channel. 120 independent test scenarios per system, 240 scored items each, same extractor for every system.

Exact slot accuracy, 95% CI:

- Whisper large-v3-turbo: 34.2% [28.3, 40.4]
- Voxtral Mini 3B: 37.1% [30.0, 43.8]
- same correct text into the extractor (ceiling): 90.8% [87.5, 94.2]

The two ASR systems are statistically indistinguishable (difference −2.9 pp [−7.1, +1.3]). It is published as a null result, because that is what it is.

Where it falls apart: emails land at 0 to 20% depending on language and system, phone numbers at 10 to 25%. The simulated phone line alone costs Whisper 5 points [+0.8, +10.0]. On a human-speech control (FLEURS) the simulated channel nearly doubles WER too; that control is a channel check, not a generalization claim, since FLEURS was likely in the training data.

Caveats I want in front, not buried:

- The speech is synthetic. When a second TTS family (Piper) voices the same scenarios, Whisper scores 10 points higher [+4.2, +15.4] and phone numbers jump from 15% to 55 to 70%. Absolute numbers are synthesizer-conditional, so results are published per TTS family.
- Review status: automated QA plus my own listening spot check, which found no issues. No systematic per-clip human review yet, so the corpus is labelled provisional.
- One scar, because it matters here: my first extractor version produced a wrong headline conclusion. I retracted it publicly; the changelog documents what was measured wrong.

Everything rescores on a CPU with no network: predictions are frozen with checksums, and a notebook regenerates every table from the release bundle. There is also a results browser where you can listen to each scored case and hear the failures yourself.

What would you test next? Another TTS family, or a language the extractor is weaker on, would stress the same pipeline. Method questions welcome, I will be in the comments.

Dataset (audio included): https://huggingface.co/datasets/Gjusev/voxentity-eu
Listen to the failures: https://huggingface.co/spaces/Gjusev/voxentity-eu-results
Code and reports: https://github.com/Gjusev/voxentity-eu

## Posting notes

- Three links at the end, repo last (LAUNCH.md: every rented post ends on the
  repo).
- Likely first questions: why synthetic speech at all, why not Common Voice,
  extractor ceiling on French addresses (it is in the README), and the
  retraction. Answers live in README and reports/release_gates.md.
- One subreddit per session (P3). No crossposting the same body the same day.
