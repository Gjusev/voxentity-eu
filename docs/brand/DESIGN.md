# VoxEntity-EU visual identity

Method: /awwwards concept and system phases, applied to a logo, a short demo
video and the README (no website in scope).

## Concepts considered

| # | Territory | Idea | Signature | Orig | Fit | Feas | Portability (lower is better) |
|---|---|---|---|---|---|---|---|
| A | Material of the work | **The slot.** Speech goes into a form field; it either locks exactly or it does not. | A dictated phone number fills a slot digit by digit; one digit lands wrong and turns orange. | 4 | 5 | 5 | 2 |
| B | Formal system | Waveform to characters: audio bars morph into monospaced glyphs. | Bars collapse into text. | 3 | 4 | 4 | 4 |
| C | Place | EU telephone switchboard, patch cables per language. | Cable plugs into DE/FR socket. | 3 | 2 | 3 | 3 |

**Chosen: A.** It is the benchmark's actual unit of measure (exact capture per slot,
one wrong character fails the slot), and it could not be moved to another project.

## Concept card

```
Idea:        One wrong digit and the slot fails; this benchmark counts slots, not words.
Metaphor:    A form field being filled by voice.
Signature:   Digits drop into a bracketed slot; one lands wrong and the slot fails.
Emotion:     Calm precision, then a small jolt.
Motion verb: snap into place, like a character locking into a field.
Screenshot:  [ +49 172 1? 59 98 16 ] with one orange digit and "slot failed".
```

## System

- Palette (shared with the report figures, already validated for colour-blind
  separation in light and dark):
  - ground `#fcfcfb` (dark `#1a1a19`)
  - ink `#0b0b0b` (dark `#f0efec`)
  - muted `#898781`
  - line `#e1e0d9`
  - signal blue `#2a78d6` (correct, ASR series 1)
  - error orange `#eb6834` (wrong character, ASR series 2)
- Type: IBM Plex Sans (display and body, engineering register, Google Fonts) and
  IBM Plex Mono (every captured value, so digits align like a form field).
- Shape: square corners; brackets are the only "container".
- Motion: snappy ease-out, 0.25 to 0.45 s entrances, holds long enough to read;
  big type moves slower than digits.

## Design Read and dials

Reading this as: a launch demo, brand mark and README for speech/ML engineers and
technical reviewers, in a quiet lab-instrument style, dial ENERGY 1 / RHYTHM 2 /
MOTION 2.

- ENERGY 1: light ground, two inks, one accent; the content (a real failing value)
  carries the attention, not decoration.
- RHYTHM 2: each video scene uses a different composition (left-aligned stack,
  ruled rows, bar chart, centred lockup) inside one consistent grid.
- MOTION 2: motion only where it carries meaning (digits typing into the slot,
  bars growing to their value, the orange bar dropping into the mark); no loops.
- Identity motif: the bracket slot, repeated in the logo, the video and the figures'
  error colour.
- Space README metadata uses the telephone emoji because Hugging Face requires an
  emoji for the Space card; it names the simulated telephone channel.

## Copy decisions (R-31)

- Tagline "Scores the slot, not the words.": the contrast is the benchmark's actual
  method (exact slot accuracy instead of word error rate), not a rhetorical formula.
- Every value on screen is a real output from the published test set
  (test-fr-phone-010); nothing in the demo is invented.
- Orange is reserved for errors so the one accent always means the same thing.

## Genericness test

A generic take would be a glowing waveform on a dark gradient with "AI-powered
voice evaluation". Changed: no gradient, no glow, light ground, the waveform only
appears inside the slot brackets, and the hero element is a real failing value
from the benchmark rather than a slogan.
