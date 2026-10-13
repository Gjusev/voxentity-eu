# Estado de implementación

Registro por fase con evidencia real. Nada aquí se marca por anticipado; una
casilla sin evidencia es una deuda, no un resultado.

## Convenciones

- Comandos: `.venv/Scripts/python.exe` (core CPU) y `.venv-gpu/Scripts/python.exe`
  (perfil GPU con torch/qwen-tts). SoX en PATH para qwen-tts.
- Todo el scoring es offline y determinista; la inferencia usa solo los inputs
  exportados sin gold (ids opacos).

## P0 — Fundaciones: COMPLETADO

- Paquete `src/voxentity_eu` instalable, CLI `voxentity` completa (exit 0/1/2/3).
- Contratos Pydantic (Scenario/Entity/Audio/Synthesis/Transform/Prediction/
  RunManifest) con validación adversarial. Schemas de ejemplo validados.
- 87 tests offline (unit + integration + contract) en verde; ruff limpio.
- Locks: `uv-core.lock` (uv 0.9.21, Python 3.11). Perfil GPU aparte
  (`.venv-gpu`, torch 2.5.1+cu121) porque la 1080 no soporta builds recientes.
- Evidencia: `python -m pytest -q` → 87 passed; `python -m voxentity_eu.cli --help`.

## P1 — Scorer: COMPLETADO

- Normalización versionada `norm-1` (literal vs canónica por tipo, regla
  troncal por locale, ß≠ss, é≠e, O≠0, sin inferencia de año).
- Métricas con denominadores explícitos, omisión/sustitución/extra/stale,
  macro de 12 celdas, degradación pareada con matriz de transiciones,
  bootstrap clusterizado por scenario_id (misma semilla → mismo intervalo).
- Fixtures calculadas a mano cubren la matriz adversativa de docs/10.
- Evidencia: tests `test_normalize.py`; `scripts/extractor_ceiling.py`.

## P2 — Casos y derechos: COMPLETADO (corpus provisional hasta revisión auditiva)

- 180 escenarios DE/FR (12 celdas × 15; 5 directos / 4 difíciles / 3
  segmentados / 3 correcciones), split 60/120 sin solapamiento de valores ni
  familias; export de inputs sin gold con ids opacos sha256/16.
- `corpus validate` pasa sin errores; hash del corpus
  `b7513367297700f3cd89df1e781af5a636f44beec320defbbd64234e2e1dde4b`.
- Registro de derechos con 5 fuentes y estado de revisión por asset.
- Pendiente: escucha humana para «verified» (hoy: automated-QA/provisional).

## P3 — Síntesis y QA: EN EJECUCIÓN

- Smoke test Qwen3-TTS en GTX 1080: fp32+sdpa obligatorio (fp16/bf16 fallan en
  Pascal); idiomas en minúsculas; salida 24 kHz. Voces candidatas serena y
  dylan generan DE y FR correctamente (data/smoke_tts/report4.json).
- Generador reanudable con checkpoint cada 20 clips en ejecución (180 masters).
- QA automática implementada (qa.py) y aplicada tras síntesis.
- Extracción de referencia `rex-1`: techo sobre synthesis_text gold =
  180/180 (dev 60/60, test 120/120) — congelada antes de cualquier inferencia.

## P4 — Canal: COMPLETADO (aplicación sobre 360 audios tras síntesis)

- Receta `tel-1` fijada: Butterworth-6 SOS 300–3400 Hz, 8 kHz, ruido gaussiano
  con seed a 20 dB SNR de habla activa, G.711 A-law ida/vuelta, regla común
  -6 dBFS. 9 tests de banda/SNR/codec/determinismo.

## P5 — Baselines y runner: EN PREPARACIÓN

- Runner con caché por clip (hash audio+sistema+decoding) y resume.
- Whisper turbo: adaptador listo (fp16 local). Voxtral Mini: kernel de Kaggle
  preparado (scripts/kaggle/) con T4; depende de inputs congelados.

## P6 — Slots persistidos y voice-evals: IMPLEMENTADO (evidencia tras audio)

- Agente de referencia con AgentStore (eventos JSONL + estado final congelado);
  store_slot reemplaza; control negativo stale cubierto en tests.
- Exportador voice-evals por voz×condición con rechazo de duplicados y copia
  16 kHz explícita; contract test contra el checkout local fijado.

## P7 — Control humano: IMPLEMENTADO, descarga pendiente de ejecución

- Selección determinista por sha256 de ID, 50/idioma, par clean/telephone,
  atribución CC-BY-4.0 con modificaciones señaladas. Requiere ejecutar
  `human-control` (token HF presente).

## P8 — Informes y demo: IMPLEMENTADO (se llena con resultados medidos)

- Taxonomía de errores, tablas con CI, render markdown, Space CPU con estado
  vacío explícito y descargas; notebooks finos generate/evaluate/reproduce.

## P9 — Entrega: ESTRUCTURA LISTA

- LICENSE (Apache-2.0 oficial), DATA_LICENSE, THIRD_PARTY_NOTICES, dataset
  card, CONTRIBUTING, validador de bundle con chequeo de secretos y checksums.

## Bloqueos y limitaciones actuales

- Kaggle: autenticada vía MCP/CLI (usuario gjusev); credencial NO se versiona.
- Voxtral local imposible (8 GB VRAM compartida con display) → kernel T4.
- Estado del corpus: automated-QA/provisional hasta revisión auditiva humana.
- Derechos del audio sintético: condicionales a los términos de salida del
  modelo TTS (ver DATA_LICENSE); los scripts y metadata siempre son públicos.
