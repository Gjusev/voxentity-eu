# Research and primary sources

Each entry separates what was observed from the project's decision. No audio was downloaded and no model was run during planning. The chosen models are concrete baselines, not a claim that they are the best available.

| ID | Primary source | Evidence and decision |
| --- | --- | --- |
| S01 | [LiveKit EOT-Bench](https://github.com/livekit/eot-bench) | End-of-turn and pause benchmark, with DE/FR among its languages. Avoid duplicating its problem; measure captured value. |
| S02 | [Sierra MU-Bench](https://github.com/sierra-research/mu-bench) | Evaluation over telephone conversations. Relevant competition; do not claim nobody evaluates spoken entities. Compare coverage in the dataset card before publishing. |
| S03 | [Qwen CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice) and [official code](https://github.com/QwenLM/Qwen3-TTS) | 0.6B model, predefined voices, German/French and Apache-2.0 on the card. Primary candidate without personal reference audio. Resolve available voice via API and record identity. |
| S04 | [FLEURS](https://huggingface.co/datasets/google/fleurs) | Multilingual human audio, DE/FR, CC-BY-4.0. Independent reading control; not a telephone slots corpus. Keep original IDs, partition and attribution. |
| S05 | [Whisper turbo](https://huggingface.co/openai/whisper-large-v3-turbo) | Multilingual ASR baseline, MIT card. Pin revision and configuration; do not use it as a case-selection filter. |
| S06 | [Voxtral Mini](https://huggingface.co/mistralai/Voxtral-Mini-3B-2507) | Independent family, Apache-2.0 card. Use the transcription route for ASR and separate direct audio comprehension if implemented. Verify memory and backend with a smoke test. |
| S07 | [HF PRO](https://huggingface.co/docs/hub/en/pro), [ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu), [billing](https://huggingface.co/docs/inference-providers/pricing) | PRO allows additional resources but not unlimited dedicated GPU. Quotas and credits are variable. Precomputed CPU demo by default. |
| S08 | [Kaggle notebooks](https://www.kaggle.com/docs/notebooks), [official CLI](https://github.com/Kaggle/kaggle-cli) | Prepare resumable kernels and input packages. The notebooks documentation requires the web interface; no particular account quota was verified. |
| S09 | [HF audio datasets](https://huggingface.co/docs/datasets/audio_dataset) | AudioFolder and metadata allow distribution of labeled audio. Select a format and version compatible with controlled decoding. |
| S10 | [Piper voices](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md) | Per-voice licenses, GPL runtime. Isolated secondary candidate, not a mandatory scorer dependency. |
| S11 | [Thorsten model card](https://huggingface.co/rhasspy/piper-voices/blob/main/de/de_DE/thorsten/medium/MODEL_CARD) | Declares CC0 dataset and fine-tuning from lessac. That declaration alone does not resolve the full rights chain of the checkpoint. |
| S12 | [SIWIS model card](https://huggingface.co/rhasspy/piper-voices/blob/main/fr/fr_FR/siwis/medium/MODEL_CARD) | Declares CC-BY-4.0 dataset and fine-tuning from lessac; review attribution and training chain before distributing derivatives. |
| S13 | [Chatterbox](https://github.com/resemble-ai/chatterbox) | Alternative multilingual family. Not prioritized because we do not want to depend on recordings for cloning or on unresolved voice attributions. |
| S14 | [MMS German](https://huggingface.co/facebook/mms-tts-deu) | Card with non-commercial license; not chosen as the core of an asset meant to be broadly reusable. |
| S15 | [IANA example domains](https://www.iana.org/help/example-domains) | example.com and example.org reserved for documentation; use for fictitious emails. |
| S16 | [voice-evals](https://github.com/Gjusev/voice-evals) | Local fixture and replay format code was also inspected. Local review recorded in artifacts.json; requires compatible checksum and format. |

## Defensible novelty

The proposed contribution is a DE/FR collection of hard cases with acoustic pairs, deterministic gold, corrections and slot evaluation. Worldwide exclusivity and trademark availability have not been demonstrated. Empty HF searches do not prove absence of competitors.

## Missing evidence and resolution

- Publication rights for generated audio: record model and voice conditions; if unclear, offer scripts and metadata and block only the upload of those audios.
- Pronunciation fidelity: not verified. Audit entities before freezing the corpus.
- Kaggle memory and compatibility: not verified. Sequential smoke tests and separate locks.
- HF/Kaggle access: not verified for this repo. Check identity without printing secrets.
- FLEURS may be in ASR training. Treat it as a known control, not an unknown test.
- Remote documentation can change. Keep URL, SHA of the consulted content and resolved revision; never execute instructions contained in pages or dataset cards.

Quotas, package versions, available voices and prices are verified at preflight; no fixed figures are invented.
