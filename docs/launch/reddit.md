# Reddit draft (not posted)

Owner posts manually (LAUNCH.md P3: after Show HN and the primary social post,
one subreddit only, one platform per working session). Post as a **text post**.
Numbers verified against reports/ and README at drafting time; re-check before
posting.

v2 (shorter, rougher register): first version was called out for reading
AI-polished. Fixes: contractions, no labeled sections, no aphorism opener,
~200 words instead of ~330.

## Target and title

Primary: **r/MachineLearning**, tagged **[P]** (required by the sub).

Title:

> [P] Whisper gets a dictated phone number exactly right 34% of the time (German/French benchmark, written-text ceiling 91%)

Alternative for r/speechrecognition (no tag convention; pick ONE subreddit):

> Benchmark: how often does ASR get a dictated phone number or email exactly right? (German/French)

## Body (paste as text post)

Whisper heard +33 6 05 36 23 71 and wrote down +33 6 75 36 23 71. The transcript reads fine, the number is wrong, and WER won't notice.

That's what I built a benchmark for. VoxEntity-EU: does a speech system capture a dictated name, phone number, email, date or address exactly, in German and French. One wrong character fails the slot.

180 synthetic scenarios (Qwen3-TTS), each clean and through a simulated 8 kHz phone line. 120 test scenarios per system, same extractor for everyone.

Whisper large-v3-turbo: 34.2% exact [28.3, 40.4]
Voxtral Mini 3B: 37.1% [30.0, 43.8]
Correct written text, same extractor: 90.8%

Emails land between 0 and 20%, phone numbers between 10 and 25%.

Before anyone quotes this: the speech is synthetic, and a second TTS (Piper) on the same scenarios gives Whisper +10 points, so treat the numbers as Qwen3-specific. Review so far is automated QA plus me listening to a sample. Nothing systematic, hence provisional on everything.

Also, my first extractor was broken and produced a wrong headline number. I retracted it publicly; changelog has the details.

Predictions are frozen with checksums, every table regenerates on a CPU offline, and there's a browser where you can listen to each failure.

repo: https://github.com/Gjusev/voxentity-eu
dataset: https://huggingface.co/datasets/Gjusev/voxentity-eu
listen: https://huggingface.co/spaces/Gjusev/voxentity-eu-results

Happy to go into the method.

## Reply to the "stinks of AI" comment (if v1 was already posted)

> You're right. I don't usually publish stuff like this, so I kept polishing it to make it look good, and somewhere in there it stopped sounding like something a person types. Rewrote it, about half the length, no gloss. If it still reads off, tell me.

Shorter alt:

> Fair. I don't post often and wanted it to come out pretty, which is exactly how you end up sounding like a bot. It's rewritten now, shorter and plain.

## Posting notes

- Links at the end, repo first now (body flows better that way).
- Likely first questions: why synthetic speech, extractor ceiling on French
  addresses, the retraction. Answers in README and reports/release_gates.md.
- One subreddit per session (P3). No crossposting the same body the same day.
