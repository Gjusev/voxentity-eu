# LinkedIn drafts (not posted)

Owner posts manually, after the listening spot check (LAUNCH.md P3). Links go in
the first comment, not the body (platform reach rule). Numbers verified against
reports/ at the time of drafting; re-check before posting.

## Draft A: F4 Time-Anchor Confession (goal: comments)

Halfway through this project I wrote down a conclusion that was wrong.

I had built a benchmark for one narrow question: when someone dictates a phone number, an email or an address in German or French, does the speech system get it exactly right?

My first numbers said the ASR was the bottleneck. Both models captured about 21% of entities.

Then I fed my own extractor the correct written text. It also scored about 21%. I had been measuring my parser, not the models.

After the fix:
Whisper large-v3-turbo: 34.2% exact capture [28.3, 40.4]
Voxtral Mini: 37.1% [30.0, 43.8]
Ceiling with perfect text: 90.8%
Emails: 0 to 20% in German and French, 0% in Spanish.

Two caveats belong in any summary. The audio is synthetic (Qwen3-TTS): 120 test scenarios, each clean and through a simulated phone line, checked by automated QA only. And when I re-synthesized the same scenarios with another TTS, accuracy rose 10 points. The synthesizer moves the numbers.

The retraction is documented in the repo. Everything reproduces on a CPU.

If you work on voice interfaces: what would you add to break it?

#SpeechRecognition #Evaluation

## Draft B: F10 Contrarian with receipts (goal: comments)

A transcript can read perfectly and still get one digit of your phone number wrong. For a voice form, that digit is the whole job.

So I measured exact capture instead of word error rate. Names, phone numbers, emails, dates, addresses and reference codes, dictated in German and French.

The receipts, on 120 synthetic test scenarios, each clean and through a simulated phone line:
Whisper large-v3-turbo captured 34.2% exactly [28.3, 40.4].
Voxtral Mini captured 37.1% [30.0, 43.8].
With the correct text, the same extractor reaches 90.8%.

Emails were among the worst cells: 0 to 20% in German and French, 0% in Spanish.

The phone line alone cost Whisper 5 points [0.8, 10.0].

What surprised me most: re-synthesizing the same scenarios with a second TTS raised accuracy by 10 points. Benchmarks built on synthetic speech partly measure the synthesizer, so I publish both side by side.

Status is provisional. No human has listened to the clips yet; automated QA only. Data, audio and a results browser are public.

Which entity type fails most in your stack?

#SpeechRecognition #Evaluation

## First comment (both drafts)

Code and reports: https://github.com/Gjusev/voxentity-eu
Dataset with audio: https://huggingface.co/datasets/Gjusev/voxentity-eu
Results browser: https://huggingface.co/spaces/Gjusev/voxentity-eu-results
