# Contratos de datos

Implementar modelos Pydantic y exportar JSON Schema. UTF-8, JSON estricto, enums cerrados, schema_version obligatorio. Rechazar IDs duplicados, valores NaN, rutas fuera del root y referencias rotas.

## Scenario

scenario_id, split (dev/test), locale (de-DE/fr-FR), entity_type, template_family, difficulty_tags[], written_text, synthesis_text, entities[], previous_mentions[], seed.

Entity: entity_id, type, canonical_value, accepted_variants[], mention_text, target=true, case_sensitive opcional (por defecto true para reference_code). postal_address usa objeto street/house_number/postal_code/locality; calendar_value usa objeto day/month y year opcional. No inferir año ausente. Resto usa string; los teléfonos nunca son enteros. La política case_sensitive es pública por tipo de tarea y no puede variar según el valor secreto.

## AudioRecord

audio_id, scenario_id, corpus (synthetic/human_control), condition (clean/telephone), parent_audio_id opcional, path relativa, sha256, sample_rate_hz, channels=1, encoding=pcm_s16le, num_samples, duration_seconds, synthesis_id opcional, transform_id opcional, qa_status, source_id.

Human control referencia external_row_id/external_split y transcript, no obliga entidades sintéticas. Validar relaciones mediante unión por ID, nunca por orden de filas.

## SynthesisRecord y TransformRecord

SynthesisRecord: synthesis_id, model_id, model_revision, speaker_id, language_arg, generation_config, seed, environment_hash, text_sha256, master_sha256, attempt, quality_decision.

TransformRecord: transform_id, recipe_version, input_sha256, output_sha256, filter_config, resampler, codec, noise_seed, target_snr_db, measured_snr_db, clipping_fraction, command_argv y tool_versions.

## Prediction

run_id, audio_id, track (asr/asr_slots/audio_slots/agent_slots), status (ok/error/timeout/unsupported), transcript nullable, predicted_slots[], error_type nullable, raw_artifact_path, observed_final_state_path nullable.

Slot: type, value, evidence optional. No gold IDs suministrados por el modelo. Para emparejar varios slots futuros usar type y matching uno-a-uno; duplicados adicionales cuentan como extra.

Una fila ausente, repetida o con ID desconocido es error de integridad de run. Un timeout es fila válida fallida. Transcripción vacía es salida válida, no ausencia de fila.

## RunManifest

run_id, schema_version, suite_version, dataset_hash, eligible_audio_ids_hash, code_commit, dependency_lock_hash, model_id/revision, backend, device, precision, decoding_config, prompt_hash, normalizer_version, seed, input_audio_policy, track, expected_count, completed_count, failed_count, access_mode (local/remote), charge_limit, observed_usage nullable.

No incluir secretos. No se exigen fechas de calendario; versiones, hashes e IDs proporcionan trazabilidad. El tiempo de cómputo medido es metadata experimental opcional, no calendario de desarrollo.

## Aislamiento

Exportar inputs públicos de evaluación con audio_id opaco, ruta/hash, locale y tipo de slot solicitado; sin canonical_value, texto, dificultad ni metadatos que revelen la respuesta. Mantener gold en otro directorio no montado en workers. El agente sabe qué campo se solicita, pero no recibe posibles respuestas.

## Normalización versionada

Dos puntuaciones: literal (NFC y trim exterior) y canonical. Canonical:
- person_name: NFC, espacios repetidos → uno, lowercase Unicode; preservar acentos y puntuación interna, y preservar ß salvo variante explícita. No usar casefold genérico que convierte ß a ss.
- phone: eliminar separadores de presentación permitidos, convertir prefijo 00 a +, preservar todos los dígitos y ceros iniciales. Equivalencia nacional/internacional solo mediante regla locale declarada, no suposición.
- email: espacios alrededor de @/punto solo si parser explícito; dominio case-insensitive, parte local preservada por defecto. Alias de símbolos hablados pertenecen al extractor.
- calendar_value: comparar componentes válidos; ambigüedad marcada se excluye antes del freeze, nunca resolverla mirando gold.
- postal_address: campos separados, reglas de espacios/case locales; número y sufijo exactos, código postal string. Abreviaturas solo allowlist pública.
- reference_code: preservar ceros, letras y guiones; ignorar case solo si contrato del caso dice case_insensitive. Sin equivalencia O/0 ni I/1.

accepted_variants se define antes de ejecutar modelos y se incluye en hash del dataset. Reportar diferencia entre exactitud literal y canónica. El normalizador no corrige transcripciones utilizando la respuesta conocida.

## Ejemplos

examples/scenario.json y examples/predictions.jsonl son fixtures de diseño, sin audio ni resultados medidos. El código implementado deberá validar sus formas y generar schemas completos.
