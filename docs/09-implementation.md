# Backlog de implementación

Orden por dependencias, sin calendario. Una casilla marcada cita su evidencia; escribir documentación no significa haber implementado funcionalidad.

## P0 — Fundaciones

- [x] Crear pyproject, paquete, CLI y extras separados; escoger lock tool y registrar decisión. — evidencia: pyproject + CLI `voxentity`, extras tts/asr-*/space; lock `uv-core.lock`.
- [x] Implementar schemas y validar ejemplos. — evidencia: contracts.py; tests/unit/test_contracts.py.
- [x] Crear tests de IDs, rutas, tipos, duplicados y aislamiento de gold. — evidencia: tests/unit/test_contracts.py, test_corpus.py.
- [x] Añadir CI CPU offline, lint y validación de links internos. — evidencia: `.github/workflows/ci.yml` (ruff, scripts/check_links.py, pytest sobre uv-core.lock).
Aceptación: instalación limpia, import sin torch/GPU/red; CLI help y ejemplos parseables; tests adversariales pasan.

## P1 — Scorer

Depende P0.
- [x] Normalización por entidad con literal/canonical separados. — evidencia: scoring/normalize.py (norm-2); test_normalize.py.
- [x] Scoring con fallos, omisión, sustitución, extras y correcciones. — evidencia: scoring/match.py; outcomes en runs/scored/*.json.
- [x] Agregación, comparación pareada e intervalos por cluster. — evidencia: scoring/aggregate.py + bootstrap.py; `voxentity compare` (test_compare_cli.py).
- [x] Fixtures con resultados calculados a mano y controles negativos. — evidencia: tests/unit/test_normalize.py.
Aceptación: errores de un dígito/acento se detectan; tasa global mantiene denominadores; runs incompletos no rankeados; informe CPU repetible.

## P2 — Casos y derechos

Depende P0.
- [x] Escribir pools y plantillas DE/FR originales, matriz 180 casos. — evidencia: corpus/pools.py; 180 escenarios.
- [x] Split 60 dev/120 test sin overlap de familia/valores equivalentes. — evidencia: corpus validate sin errores; test_corpus.py.
- [x] Manifest de fuentes y checklist de derechos por asset. — evidencia: rights_registry.jsonl.
- [x] Export de inputs sin gold y IDs opacos. — evidencia: data/inputs (ids opacos, orden por input_id).
Aceptación: counts exactos, equilibrio de dificultad y voz, validación semántica de correcciones, ninguna fecha de desarrollo añadida.

## P3 — Síntesis y QA

Depende P2.
- [x] Resolver Qwen y speaker IDs; smoke test por idioma/voz. — evidencia: scripts/smoke_tts.py; data/smoke_tts/report*.json.
- [x] Generador reanudable, provenance, hashes y registros de intentos. — evidencia: synthesis.jsonl + synthesis_prev_attempts.jsonl.
- [ ] QA automática, revisión de audio disponible y flujo de exclusiones. — QA automática y flujo de exclusiones listos (`review_package.py apply`: veredicto con motivo, clip limpio + telefónico excluidos del scoring, gold intacto); falta la escucha humana en sí.
- [x] Paquete de revisión para casos pending. — evidencia: `scripts/review_package.py build` (review/index.html + review.csv, 180 clips limpios, sin transcripciones ASR).
Aceptación: 180 clean accepted para verified o estado provisional explícito; errores TTS no etiquetados como errores ASR; ningún filtro basado en resultados del modelo evaluado.

## P4 — Canal

Depende P3.
- [x] Implementar recipe fija, ruido seed, codec y checks de audio. — evidencia: audio/channel.py tel-1; test_channel.py.
- [x] Generar 180 pares y verificar relaciones. — evidencia: 360/360 QA accepted (qa.jsonl).
Aceptación: 360 archivos válidos cuando P3 completo; sample rates y hashes coinciden; test de banda/SNR sin asumir latencia real.

## P5 — Baselines y runner

Depende P1/P4.
- [x] Doctor Kaggle/HF; locks y smoke tests por backend. — evidencia: doctor.py perfiles hf/kaggle.
- [x] Adaptadores Whisper y Voxtral; resume, timeouts y cache. — evidencia: adapters/whisper.py, voxtral.py.
- [x] Extractor común y control gold→extractor. — evidencia: rex-3; techo hablado 100% y escrito 90.8% (test).
- [x] Corridas completas con inputs aislados. — evidencia: whisper 360/360, voxtral 360/360.
Aceptación: al menos dos familias ASR realmente ejecutadas; artefactos por clip; comparación con misma cohorte; OOM/error no oculto.

## P6 — Slots persistidos y voice-evals

Depende P5.
- [x] Agente de referencia y storage instrumentado. — evidencia: adapters/agent.py; tests/integration/test_agent.py.
- [x] Corrección dentro del turno; control negativo stale-value. — evidencia: tests/integration/test_agent.py.
- [x] Export fixtures separados por voz/condición y conversión explícita 8→16 kHz. — evidencia: adapters/voice_evals_export.py (8→16 kHz explícito).
- [x] Contract test con versión fijada de voice-evals. — evidencia: tests/contract/test_voice_evals.py (commit 3f6f9dd).
Aceptación: scorer lee estado final real; replay no inventa timings; texto duplicado no sobrescribe audio; core funciona sin voice-evals instalado.

## P7 — Control humano y sensibilidad

Depende P1/P5.
- [x] Descarga FLEURS selectiva por revisión, IDs y atribución. — evidencia: data/human_control/attribution.json.
- [x] Muestreo determinista 50 por idioma y versiones acústicas. — evidencia: human_control_manifest.jsonl.
- [x] Evaluación WER/CER separada. — evidencia: runs/scored/human_control_wer.json.
- [x] Investigar/implementar segundo sintetizador solo si derechos resueltos; reportar gate. — evidencia: research/second-tts-gate.md (Piper thorsten CC0 + siwis CC-BY 4.0, revisión fijada; estado condicional, no ejecutado).
Aceptación: control humano ejecutado o bloqueo verificable sin falso reclutamiento; todas las tablas distinguen corpus; alternativa TTS no bloquea release core.

## P8 — Informes y demo

Depende P5/P6; integrar P7 cuando disponible.
- [x] Tablas, bootstrap, taxonomía de errores y reporte en inglés. — evidencia: reports/report.md.
- [x] Space CPU de resultados precalculados. — evidencia: space/app.py + scripts/build_space_data.py (no desplegado).
- [x] Notebooks de generación, evaluación y reproducción. — evidencia: notebooks/*; reproduce verificado idéntico al bundle.
Aceptación: demo reproduce números del reporte, audio correcto por ID, ningún placeholder numérico presentado como hallazgo.

## P9 — Entrega publicable

Depende P8.
- [x] Licencias oficiales, notices, dataset card, README y CONTRIBUTING. — evidencia: LICENSE, DATA_LICENSE.md, THIRD_PARTY_NOTICES.md, dataset_card/, CONTRIBUTING.md.
- [x] Bundle con checksums, manifiesto y controles de release. — evidencia: release.py build_bundle; `release validate` ok; test_release.py.
- [x] Comandos de publicación y borradores de comunicación. — evidencia: PUBLISHING.md (gates, comandos `gh`/`hf` verificados contra la CLI instalada, borradores; nada ejecutado) y space/README.md (metadatos HF).
- [x] Actualizar IMPLEMENTATION_STATUS con comandos ejecutados/evidencias. — evidencia: IMPLEMENTATION_STATUS.md.
Aceptación: fresh-environment scoring offline idéntico, ninguna credencial, derechos resueltos para assets publicados, nombres y claims coherentes.

## Extensiones después del núcleo

- [ ] Dos proveedores de voz con acceso y presupuesto, estado final verificable. — bloqueado: requiere proveedor y presupuesto explícitos.
- [x] Correcciones entre turnos y code-switching. — evidencia: reports/ext-multiturn/report.md, reports/ext-codeswitch/report.md (suites propias en data/ext/).
- [ ] Español y nueva versión de corpus.
- [x] Más voces/casos si análisis revela cobertura insuficiente. — evidencia: análisis de cobertura (efecto voz confundido con escenario) → reports/ext-voices/report.md; además segunda familia TTS en reports/ext-piper/report.md.

Cada extensión tiene suite propia. No inflar tamaño del corpus principal ni completar casillas con mocks.
