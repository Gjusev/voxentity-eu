# Evaluation and methodology

## Separate tracks

A. ASR: Whisper turbo and Voxtral Mini over identical audio; transcription without entity hints. Explicit language for both. Report corpus WER (sum of errors / sum of words) and CER, including conservative verbal variants. Do not confuse with the per-clip average of voice-evals.

B. ASR → slots: same fixed extractor for both transcripts. Also run it over the gold transcript: it estimates the extractor ceiling. An extractor failure on gold is a failure of the evaluation system, not of the ASR.

C. Audio → slots: optional, a model able to take audio plus instructions; not compared as if it were identical ASR.

D. Agent slots: the agent receives audio and the field request, persists the value via store_slot. Evaluate the final state read from its storage and events; words spoken by the agent do not prove persistence.

Implement a reference extractor based on limited and published rules. For names/addresses use domain grammar and phrase boundaries, without a gold list. Add an optional LLM extractor with fixed prompt/model, temperature and controlled JSON output. Report each system as the combination ASR+extractor, not attributing its failures only to ASR.

## Primary metrics

For N eligible examples with one entity:
- Slot accuracy = examples with correct value / N. error/timeout/empty/not persisted count as incorrect.
- Operational coverage = completed inferences / N.
- Conditional accuracy = correct / completed, secondary alongside coverage.
- Omission = target without prediction / N.
- Substitution = target present with wrong value / N.
- Extra output = examples with unsolicited or duplicated slots / N.
- In correction cases, stale-value rate = final state keeps the previous value / cases with correction.

For future multi-slot suites: TP with one-to-one matching, FP extras and wrong values, FN targets not recovered; publish precision/recall/F1 and all-slots accuracy per case. Do not call every substitution a 'hallucination': the source of the error is not known from the mismatch alone.

## Summaries

Publish counts and scores by language, entity, condition, voice, synthesizer and difficulty type. Main macro: average of the 12 language×entity cells, per condition. Micro and weighting available. No aggregate ranking between incompatible suites or tracks.

Paired degradation = accuracy_clean − accuracy_telephone, in percentage points. Show fail→pass, pass→fail, pass→pass and fail→fail pair transitions. Use the same scenario list for each comparison.

95% percentile bootstrap intervals, 2000 replicas with seed, resampling by scenario_id including its variants and models; stratified by language×entity. For between-system differences, resample the same clusters. In human control, cluster by speaker if available and flag if it can only be done by utterance.

The CI reflects variation between corpus cases, not human speaker diversity nor generation uncertainty. Do not claim significant differences from minimal rankings or small cells. Report absence of a conclusive difference.

## Failures and QA

Eligibility freezes before inference. Do not exclude cases based on performance. Publish generated/accepted/excluded and QA reasons. Same eligible audios for all models; unsupported counts as a failure in a required suite and is shown as such.

Reports of incomplete runs must carry incomplete=true and not participate in full-run ranking. Retries preserve previous results; policy of at most 2 retries of transient errors, never hunting for a correct answer through repeated trials.

## Mandatory experiments

E1 two ASR baselines on the main corpus.
E2 both ASR with shared extractor and the gold→extractor baseline.
E3 reference agent with captured final state, including corrections and the negative control that retains the previous value.
E4 FLEURS control: WER/CER clean vs channel, separate from entity.
E5 second TTS over a stratified subset of 60 cases (5 per cell), if the rights/execution chain is resolved. If not, explicit single-family limitation and prepared profile.

For real provider agents: conditional adapters with the same final contract, audio, questions and policies. Two configurations of the same reference agent are not presented as two providers.

## Error report

Classify digit_swap, missing_prefix, spelling_loss, accent_loss, correction_ignored, address_component_loss, format_only, extra_slot, timeout, synthesis_issue. Automatic classification is heuristic and revisable. Publish all cases, with deterministic selection for demo, without choosing only errors that favor the headline.
