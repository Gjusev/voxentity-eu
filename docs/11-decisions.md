# Decisions and limits

## Fixed

D01 Independent repo voxentity-eu, no ELO.
D02 Synthetic DE/FR core and public human control kept separate.
D03 No recruitment, personal cloning or scraping of unlicensed audio.
D04 Qwen CustomVoice as primary candidate; revision recorded, execution pending.
D05 Whisper turbo and Voxtral Mini as concrete candidate baselines.
D06 Evaluate final persistence in addition to text.
D07 CPU Space and offline scoring; Kaggle for GPU batch.
D08 Gold isolated from evaluated systems.
D09 180 scenarios/360 files as initial scope; QA-driven differences are reported.
D10 Dates and development estimates absent; technical audio magnitudes and references to models whose names contain numbers are allowed.

## Conditionals already resolved by policy

No valid voice: select another predefined voice of the same model and repeat QA, no cloning.
No resolved rights: block redistribution of the asset, continue implementation.
No accessible FLEURS: leave human control pending with evidence, do not substitute TTS labeled as human.
No executable second model: report a partial single baseline, do not declare a complete comparison.
No provider access: reference agent and open baselines; adapter prepared and disabled.
No listening review: corpus clearly labeled provisional.
No second TTS family: main analysis allowed with an explicit limitation.
No external publication permission in the next brief: bundle and commands prepared locally.

## Aspects the implementer must resolve through testing

Exact dependency versions; speaker IDs; GPU memory and precision; Voxtral backend; hashes of alternative voices; most compatible physical format of FLEURS; effective DE/FR pronunciation quality.

These do not require asking preferences again: run smoke tests, document the decision and continue. Only account, access, budget or rights limits that cannot be resolved locally justify an external blockage.
