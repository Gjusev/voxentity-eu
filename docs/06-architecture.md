# Architecture and execution contracts

Python 3.11 as the proposed base environment. Package src/voxentity_eu, CLI voxentity. Core: Pydantic, NumPy, SciPy, soundfile, jiwer; visualization/Parquet/HF in extras. PyTorch and each backend in separate environments if versions clash. Resolve real locks during implementation.

## Target tree

- src/voxentity_eu/contracts.py, provenance.py, cli.py
- corpus/{generate,split,validate,rights}.py
- audio/{synthesize,channel,qa}.py
- adapters/{base,whisper,voxtral,slots,agent,voice_evals}.py
- scoring/{normalize,match,aggregate,bootstrap}.py
- reporting/{tables,errors,render}.py
- configs/{corpus,channel,systems,release}.yaml
- schemas/, tests/{unit,integration,contract}, examples/
- notebooks/{generate,evaluate,reproduce}/
- space/app.py, space/requirements.txt
- scripts/, dataset_card/, reports/, licenses/
- data/manifest and small versioned gold; large audio and results outside Git.

## Interfaces

Synthesizer.generate(text, locale, voice_id, config) → master audio + provenance.
ASR.transcribe(audio, locale, config) → transcript/status; no gold parameters.
SlotExtractor.extract(transcript, requested_type, locale) → slots/status.
Agent.evaluate(audio, requested_type, locale) → transcript, events and observable final state.
Scorer.score(gold, predictions, policy) → deterministic details.
Runner does not import the scorer nor mount gold. Scorer does not call the network.

## CLI to implement

These commands are future specification; they do not work yet:

- voxentity doctor --profile local|kaggle|hf
- voxentity corpus build --config configs/corpus.yaml --out data/generated
- voxentity corpus validate --manifest PATH --gold PATH
- voxentity synthesize --manifest PATH --profile qwen --resume
- voxentity qa --manifest PATH --out PATH
- voxentity transform --manifest PATH --recipe configs/channel.yaml --resume
- voxentity export-inputs --manifest PATH --out PATH
- voxentity run --inputs PATH --system PATH --out PATH --resume
- voxentity score --gold PATH --predictions PATH --manifest PATH --out PATH
- voxentity compare --runs PATH PATH --out PATH
- voxentity human-control --source-lock research/artifacts.json --out PATH
- voxentity export voice-evals --manifest PATH --voice-id ID --condition ID --out PATH
- voxentity report --results PATH --out PATH
- voxentity release validate --bundle PATH

Exit codes: 0 completed operation, 1 failed quality gate, 2 invalid input/config, 3 missing dependency or resource. Partial runs with errors produce a report but nonzero exit. stdout JSON with --json; logs on stderr.

## Resume and cache

The cache key includes audio hash, system, prompt, model, applicable normalization and environment. Write atomically per clip; verify checksum before reuse. Policy changes invalidate the relevant cache. Do not overwrite different runs with the same ID. Save an index of successes/failures and parameters, not only the final table.

## Reference agent

Local server/process with audio interface, transcript, extractor and sqlite or JSONL of store_slot events. session_id per case, strict reset; finish, read state via an independent API and export it. A correction replaces the previous value. Negative test keeps the first, positive test keeps the last. No phone calls or external accounts needed.

One recorded session proves observed persistence; it does not imply behavior of another provider. External adapters must provide equivalent observation or use a separate declared-response track.

## Deterministic reference extractor

Create DE/FR parsers per requested type: cardinal numbers and digit sequences; email symbol words; months and calendar components; spelled alphabet and reference blocks. Separate text extraction from value canonicalization. For names and addresses, accept the documented linguistic constructions and return unsupported_parse if not interpretable, without resorting to gold lookup.

Detect correction markers ('pardon', 'je corrige', 'Entschuldigung', 'ich korrigiere') with scope rules: they replace the corresponding entity, not any earlier number. Version the rules and test negation, multiple mentions and politeness prefixes. These are design examples, not an exhaustive linguistic list.

The grammar may know task structure, but not template_id nor canonical entities of the case. Test templates belong to reserved families; freeze parsers using dev. Evaluate gold→parser per cell before comparisons and report its ceiling, even if low. A test-based improvement demands a new version and explicit statement of test reuse.

## Verified voice-evals integration

Local code inspected: C:/Code Main/voice-evals, commit in research/artifacts.json. FixtureCallerVoice indexes clips by exact text: two audios of the same text would collide. Create a separate manifest per voice×condition and reject duplicates within each manifest.

Shape: format={sample_rate,channels,sample_width,encoding}, clips=[{text,file,sha256,provenance}], note. WAV/PCM supported; no silent resampling. Export the derived telephone audio explicitly at 16 kHz for compatible transport, keeping the original 8 kHz and both hashes. Upsampling does not restore bandwidth.

Replay uses id, scenario{name,expected_outcome}, ground_truth_transcript and available observations. Export outcome only when state was read; do not fabricate timings. required_facts by substring does not replace our entity scorer. Deliver VoxEntity results in a sidecar.

The new repo keeps independence; voice-evals is an optional integration, with pinned version and a real contract test.
