# Brag Plan: VoxEntity-EU

## What is this app?
An open benchmark that checks whether speech systems capture an entity exactly
(phone, email, address, name, date, code) when it is dictated in German or French.

## The angle
One real number from the test set, captured three different wrong ways. The
benchmark scores the slot, not the words, and the video shows why that matters
before it shows any statistic. Everything on screen is a real value from the
published results (test-fr-phone-010).

## Hook (first 2-3 seconds)
"A caller dictates" + the number in large mono type, then a bracketed slot fills
digit by digit with Whisper's capture; one digit lands orange.

## Key moments
- The single wrong digit: 0 heard as 7 on the simulated phone line.
- Same number, three captures: Whisper on clean audio captured nothing,
  Whisper on the phone line got one digit wrong, Voxtral dropped a digit.
- The measured gap: 34.2% and 37.1% exact capture vs a 90.8% ceiling with the
  correct text.

## Outro / punchline
Logo assembles (the orange bar drops into the slot), "Scores the slot, not the
words.", repo URL, and the honest status line.

## User flow worth showing
Dictated value → system capture lands in the slot → slot pass/fail. Shown with
the real case; the results browser (Space) shows the same view.

## Tone
- Preset: polished
- Creative direction: quiet lab instrument; a form field under a magnifier
- Interpretation: 4 scenes, long holds, one accent colour reserved for errors,
  no hype words, numbers with their N and CIs.

## Format: landscape, 1920x1080
## Duration: 21.5 s

## Visual identity (from the project)
- Background: #fcfcfb
- Accent (error): #eb6834; signal: #2a78d6
- Text: #0b0b0b; muted #898781; line #e1e0d9
- Display/body: IBM Plex Sans; values: IBM Plex Mono (local woff2)
- Strongest visual: the bracket slot from the logo; the cell-accuracy figure bars

## Share copy (draft)
A caller says +33 6 05 36 23 71. One model heard a 7. VoxEntity-EU scores the slot, not the words.

## Audio direction
- Role: warm low bed, sparse precise accents
- Music: happy-beats-business-moves-vol-12 (ende.app, CC BY 4.0), low volume, fade in 0.6 s, fade out under the logo
- Music cue guidance: preset read; strong cues 8.74 s, 13.11 s, 17.47 s
- Audio-reactive treatment: none (polished stillness; the error colour is the only emphasis)
- SFX posture: sparse; keypress ticks for digits, one error tone, row clicks, one drop for the logo bar
- Restraint rule: no SFX on every text line; nothing louder than the music bed except the error tone

## Storyboard

### Scene 1: The slot, 0.0 to 5.0 s
"A caller dictates" (muted label), "+33 6 05 36 23 71" in large mono. Below, an
empty bracket slot labelled "Whisper large-v3-turbo · simulated phone line". The
capture types in digit by digit: "+33 6 75 36 23 71"; the 7 turns orange, the
brackets turn orange, "Slot failed. One digit." holds 1.3 s.
Sequential: yes, 12 characters typed over ~1.1 s, then hold.
Audio: keypress ticks per character, error tone on the wrong digit.
Transition: clean slide up → Scene 2

### Scene 2: Three captures, 5.0 to 10.0 s
Title "Same number. Three captures." Three rows, each label + value in mono,
arriving 0.5 s apart and then holding together 2.5 s:
- Whisper · clean audio → (nothing captured)
- Whisper · phone line → +33 6 75 36 23 71 (7 orange)
- Voxtral Mini · both → +33 6 5 36 23 71 (missing digit marked orange)
Footer: "Real failures from the test set. Synthetic speech (Qwen3-TTS)."
Audio: one soft click per row.
Transition: clean → Scene 3 (strong cue 8.74 used for the third row lock)

### Scene 3: The measured gap, 10.0 to 17.0 s
"Exact capture, 120 test scenarios × clean + simulated phone line." Three
horizontal bars grow: Whisper 34.2% [28.3, 40.4], Voxtral 37.1% [30.0, 43.8],
and a grey tick for the 90.8% ceiling with correct text (lands on cue 13.11).
Numbers count up. Footnote: "Automated QA plus one listening spot check. Provisional."
Audio: bed only; a single click as the ceiling tick lands.
Transition: soft → Scene 4

### Scene 4: Logo, 17.0 to 21.5 s
The mark assembles: brackets draw, three ink bars rise, the orange bar drops in
(cue 17.47). Wordmark "VoxEntity-EU", line "Scores the slot, not the words.",
"github.com/Gjusev/voxentity-eu". Bottom: "German · French · open data and code".
Audio: drop SFX on the orange bar, music fades out.

**Music mood:** calm, steady
**Audio summary:** low bed throughout, typing ticks and one error tone in the hook, quiet resolve on the logo.
