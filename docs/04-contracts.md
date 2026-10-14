# Data contracts

Implement Pydantic models and export JSON Schema. UTF-8, strict JSON, closed enums, mandatory schema_version. Reject duplicate IDs, NaN values, paths outside the root and broken references.

## Scenario

scenario_id, split (dev/test), locale (de-DE/fr-FR), entity_type, template_family, difficulty_tags[], written_text, synthesis_text, entities[], previous_mentions[], seed.

Entity: entity_id, type, canonical_value, accepted_variants[], mention_text, target=true, case_sensitive optional (default true for reference_code). postal_address uses a street/house_number/postal_code/locality object; calendar_value uses a day/month object with optional year. Do not infer a missing year. The rest use string; phones are never integers. The case_sensitive policy is public per task type and cannot vary with the secret value.

## AudioRecord

audio_id, scenario_id, corpus (synthetic/human_control), condition (clean/telephone), parent_audio_id optional, relative path, sha256, sample_rate_hz, channels=1, encoding=pcm_s16le, num_samples, duration_seconds, synthesis_id optional, transform_id optional, qa_status, source_id.

Human control references external_row_id/external_split and transcript; it does not impose synthetic entities. Validate relations by ID joins, never by row order.

## SynthesisRecord and TransformRecord

SynthesisRecord: synthesis_id, model_id, model_revision, speaker_id, language_arg, generation_config, seed, environment_hash, text_sha256, master_sha256, attempt, quality_decision.

TransformRecord: transform_id, recipe_version, input_sha256, output_sha256, filter_config, resampler, codec, noise_seed, target_snr_db, measured_snr_db, clipping_fraction, command_argv and tool_versions.

## Prediction

run_id, audio_id, track (asr/asr_slots/audio_slots/agent_slots), status (ok/error/timeout/unsupported), transcript nullable, predicted_slots[], error_type nullable, raw_artifact_path, observed_final_state_path nullable.

Slot: type, value, optional evidence. No gold IDs supplied to the model. For matching several future slots use type and one-to-one matching; additional duplicates count as extra.

A missing, repeated row or unknown ID is a run integrity error. A timeout is a valid failed row. Empty transcript is valid output, not a missing row.

## RunManifest

run_id, schema_version, suite_version, dataset_hash, eligible_audio_ids_hash, code_commit, dependency_lock_hash, model_id/revision, backend, device, precision, decoding_config, prompt_hash, normalizer_version, seed, input_audio_policy, track, expected_count, completed_count, failed_count, access_mode (local/remote), charge_limit, observed_usage nullable.

No secrets. Calendar dates are not required; versions, hashes and IDs provide traceability. Measured compute time is optional experimental metadata, not a development calendar.

## Isolation

Export public evaluation inputs with opaque audio_id, path/hash, locale and requested slot type; without canonical_value, text, difficulty or metadata that reveal the answer. Keep gold in another directory not mounted into workers. The agent knows which field is requested, but receives no candidate answers.

## Versioned normalization

Two scores: literal (NFC and outer trim) and canonical. Canonical:
- person_name: NFC, repeated whitespace → one, Unicode lowercase; preserve accents and internal punctuation, and preserve ß unless an explicit variant exists. Do not use generic casefold that maps ß to ss.
- phone: strip allowed presentation separators, convert 00 prefix to +, preserve all digits and leading zeros. National/international equivalence only through the declared locale rule, not assumption.
- email: strip whitespace around @/dot only with an explicit parser; domain case-insensitive, local part preserved by default. Spoken-symbol aliases belong to the extractor.
- calendar_value: compare valid components; marked ambiguity is excluded before the freeze, never resolved by looking at gold.
- postal_address: separate fields, locale-specific space/case rules; house number and suffix exact, postal code string. Abbreviations only via a public allowlist.
- reference_code: preserve zeros, letters and dashes; ignore case only if the case contract says case_insensitive. No O/0 or I/1 equivalence.

accepted_variants is defined before running models and is included in the dataset hash. Report the gap between literal and canonical accuracy. The normalizer does not correct transcripts using the known answer.

## Examples

examples/scenario.json and examples/predictions.jsonl are design fixtures, without audio or measured results. The implemented code must validate their shapes and generate full schemas.
