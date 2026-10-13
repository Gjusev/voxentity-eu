# Estado de implementación

Registro por fase con evidencia real. Nada aquí se marca por anticipado; una
casilla sin evidencia es una deuda, no un resultado. Todo lo ejecutado es
reproducible con los comandos listados.

## Convenciones

- `.venv` (Python 3.11, CPU): scoring, contratos, corpus, informes.
- `.venv-gpu` (torch 2.5.1+cu121): síntesis Qwen y Whisper local (GTX 1080).
- Kaggle (T4, usuario gjusev): Voxtral Mini; credencial solo en variables de
  entorno, nunca en el repo.
- SoX requerido en PATH para `qwen-tts`.

## P0 — Fundaciones: COMPLETADO

- Paquete instalable, CLI completa (exit 0/1/2/3), contratos Pydantic con
  validación adversarial, 79 tests offline verdes, ruff limpio.
- Evidencia: `python -m pytest -q` → 79 passed.

## P1 — Scorer: COMPLETADO (norm-2)

- `norm-1` congelada antes de inferir; tras la auditoría adversa se publicó
  `norm-2` con cambios explícitos: allowlist de abreviaturas de calle (claves
  de locale corregidas), sufijos bis/ter en direcciones FR número-primero, y
  forma internacional con cero troncal repetido («+49 (0)…»).
- Métricas con denominadores explícitos; comparaciones pareadas por
  (scenario_id, condition) — se corrigió el colapso por scenario_id que
  descartaba la mitad de las filas.
- Evidencia: tests de scorering + `scripts/score_all.py`.

## P2 — Casos y derechos: COMPLETADO (corpus provisional)

- 180 escenarios; validate sin errores; exportación de inputs sin gold con
  ids opacos y **orden por input_id** (la auditoría detectó que el orden por
  audio_id filtraba split/dificultad; corregido y con test de regresión).
- Auditoría: frame duplicado dev/test en refs corregido (1 clip dev
  regenerado); ordinales alemanes irregulares (ersten/dritten/siebten)
  corregidos (1 clip test regenerado y reevaluado).
- Estado del corpus: automated-QA/provisional (sin escucha humana).

## P3 — Síntesis y QA: COMPLETADO

- 180 masters Qwen3-TTS fp32/sdpa GTX 1080 (~9 s/clip), 0 fallos; voces
  serena/dylan 8/7 por celda, alternadas por índice (no por dificultad).
- 1 clip truncado por QA (0.96 s) regenerado con éxito (intento 2 registrado
  en `synthesis_prev_attempts.jsonl`).
- Extractor de referencia: `rex-1` congelado antes de inferir; tras la
  regeneración del corpus se publicó `rex-2` (radicales de ordinales).
  Techo sobre synthesis_text gold: **180/180** (dev 60/60, test 120/120).

## P4 — Canal: COMPLETADO

- 360/360 archivos aceptados por QA automática (180 clean 16 kHz + 180
  telephone 8 kHz); receta tel-1 con hashes por archivo.

## P5 — Baselines y runner: COMPLETADO

- Whisper large-v3-turbo (fp16, GTX 1080): 360/360 sintéticos completos, 0
  fallos; además 200/200 del control humano. Se corrigió el mapeo de idioma
  (Whisper espera 'german'/'french'); caché invalidada y re-ejecutada.
- Voxtral Mini 3B (bf16, Kaggle T4): kernel autocontenido (paquete embebido
  base64 + dataset de inputs). Tras diagnosticar el layout nuevo de mounts
  (`/kaggle/input/datasets/gjusev/...`), versión 8 en ejecución.
- Manifiestos de run con hashes reales (o gaps de procedencia explícitos).

## P6 — Agente y voice-evals: COMPLETADO

- Agente de referencia sobre 360 inputs (transcripciones Whisper
  congeladas): 360/360 con estado final observable; tests de stale-value y
  dice-pero-no-guarda en verde.
- Exportador voice-evals con rechazo de duplicados; contract test contra el
  checkout local fijado (commit 3f6f9dd).

## P7 — Control humano: COMPLETADO

- FLEURS vía exportación oficial parquet (commit resuelto y registrado; sin
  ejecutar scripts del dataset). 50+50 filas únicas por hash de path;
  300 archivos (originales preservados + clean + telephone); atribución
  CC-BY-4.0 con modificaciones señaladas.
- Whisper sobre control humano: WER clean 0.115 vs telephone 0.221
  (el canal telefónico casi duplica el WER en habla humana; denominadores
  2172 palabras, 100 utterances por condición).

## P8 — Informes y demo: COMPLETADO (con resultados medidos)

Ver `reports/report.md` (regenerable offline). Números medidos actuales
(test split, n=240 por sistema, extractor rex-2, norm-2):

| sistema | exactitud slots | IC 95% | cobertura |
| --- | --- | --- | --- |
| gold→extractor (techo) | 100% | [100, 100] | 100% |
| whisper-turbo→slots | 20.8% | [15.4, 26.2] | 100% |
| reference-agent (estado final) | 20.8% | [15.4, 26.2] | 100% |

Hallazgo principal hasta ahora: el cuello de botella está en la capa ASR
(techo del extractor 100% vs 20.8% a través de Whisper), con WER sintético
0.706 contra el texto verbalizado (nota: esta cifra mezcla normalización de
números con errores; el WER del control humano es la medida limpia).
Voxtral pendiente de la corrida Kaggle.

## P9 — Entrega: ESTRUCTURA COMPLETADA

- LICENSE Apache-2.0 oficial, DATA_LICENSE, THIRD_PARTY_NOTICES, dataset
  card, CONTRIBUTING, validador de bundle (secretos + checksums + derechos).
- Publicación externa NO ejecutada (pendiente de autorización): comandos
  preparados en README y scripts.

## Auditoría adversa

Workflow de 26 agentes (4 dimensiones × verificación de refutación): 22
hallazgos confirmados, todos corregidos en commits etiquetados «audit fixes»
y «rex-2». Los hallazgos y su resolución están en el historial git.

## Bloqueos y limitaciones

- Escucha humana del corpus: pendiente → corpus «provisional», no «verified».
- Derechos del audio sintético: condicionales (ver DATA_LICENSE.md).
- Voxtral: kernel v8 en ejecución en Kaggle al cierre de este estado.
- Space y dataset HF: artefactos locales listos; publicación externa
  requiere autorización explícita.
