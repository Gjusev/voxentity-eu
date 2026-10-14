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
  validación adversarial, 92 tests offline verdes, ruff limpio.
- Evidencia: `python -m pytest -q` → 92 passed (79 antes de rex-3).

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
- Revisión humana preparada: `python scripts/review_package.py build` genera
  review/index.html (reproductor + texto objetivo, sin salidas ASR) y
  review/review.csv; `apply --reviewer NOMBRE` valida veredictos
  (accepted/wrong_synthesis/ambiguous/truncated, motivo obligatorio si no
  accepted), escribe data/generated/human_review.jsonl y excluye del scoring
  el clip limpio y su versión telefónica. «verified» sólo con 180/180.

## P3 — Síntesis y QA: COMPLETADO

- 180 masters Qwen3-TTS fp32/sdpa GTX 1080 (~9 s/clip), 0 fallos; voces
  serena/dylan 8/7 por celda, alternadas por índice (no por dificultad).
- 1 clip truncado por QA (0.96 s) regenerado con éxito (intento 2 registrado
  en `synthesis_prev_attempts.jsonl`).
- Extractor de referencia: `rex-1` congelado antes de inferir; tras la
  regeneración del corpus se publicó `rex-2` (radicales de ordinales) y,
  tras revisión, `rex-3` (forma escrita; ver «Retractación rex-2»).
  Techo rex-3 sobre gold: synthesis_text 180/180; written_text dev 60/60,
  test 109/120 (90.8%).

## P4 — Canal: COMPLETADO

- 360/360 archivos aceptados por QA automática (180 clean 16 kHz + 180
  telephone 8 kHz); receta tel-1 con hashes por archivo.

## P5 — Baselines y runner: COMPLETADO

- Whisper large-v3-turbo (fp16, GTX 1080): 360/360 sintéticos completos, 0
  fallos; además 200/200 del control humano. Se corrigió el mapeo de idioma
  (Whisper espera 'german'/'french'); caché invalidada y re-ejecutada.
- Voxtral Mini 3B (bf16, Kaggle T4, kernel autocontenido con paquete
  embebido): **360/360 completos, 0 fallos**. Se corrigió la ruta de API
  (transcripción vía `apply_transcription_request`, no chat template) y el
  layout nuevo de mounts (`/kaggle/input/datasets/gjusev/...`); las
  iteraciones fallidas del kernel quedan versionadas en Kaggle (v1-v8).
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

## P8 — Informes y demo: COMPLETADO (con resultados medidos, rex-3)

Ver `reports/report.md` (regenerable offline: `python scripts/run_tracks.py`
→ `python scripts/score_all.py` → `voxentity compare …` → `voxentity report`).
Números medidos actuales (test split, n=240 escenario×condición por sistema,
extractor rex-3, norm-2):

| sistema | exactitud slots | IC 95% | macro12 clean / tel |
| --- | --- | --- | --- |
| gold hablado→extractor (sanity) | 100% | [100, 100] | 100 / 100 |
| gold escrito→extractor (techo relevante) | 90.8% | [87.5, 94.2] | 90.8 / 90.8 |
| voxtral-mini→slots | 37.1% | [30.0, 43.8] | 39.2 / 35.0 |
| whisper-turbo→slots | 34.2% | [28.3, 40.4] | 36.7 / 31.7 |
| reference-agent (estado final) | 34.2% | [28.3, 40.4] | 36.7 / 31.7 |

El agente reprocesa las transcripciones Whisper congeladas, así que coincide
con whisper→slots por construcción; mide persistencia de estado, no ASR.

Comparación pareada whisper − voxtral (n=240, bootstrap estratificado, 2000
réplicas): −2.9 pp, IC 95% [−7.1, +1.3]; voxtral mejor en 17 pares, whisper
en 10 — **sin diferencia concluyente**; resultado nulo publicado como tal.

Canal telefónico pareado por escenario (clean − telephone, bootstrap 95%):
whisper +5.0 pp [+0.8, +10.0] (degradación detectable), voxtral +4.2 pp
[−0.8, +9.2] (no concluyente). Figuras SVG en reports/figures/ (precisión
por celda con techo escrito; diferencias pareadas con IC).

Space (space/app.py) verificado en navegador con gradio 6.17: se corrigieron
4 fallos que impedían su uso (audio limpio sobrescrito por el telefónico,
rutas de audio inexistentes, case_id duplicados entre condiciones,
transcripciones ausentes) y se cablearon los botones de ejemplo
determinista de docs/08. No desplegado.

Lectura: con el techo escrito en ~91%, ambas familias ASR quedan en ~34–37%;
el hueco restante sí es mayoritariamente ASR (emails dictados/deletreados,
teléfonos, nombres, códigos). Celdas más débiles: email (0–20%), teléfono
(10–25%), direcciones DE en whisper (0%). Excepción: FR postal_address tiene
techo escrito de solo 20% en test (familias de plantilla de test no cubiertas
por reglas afinadas en dev); esa celda sigue limitada por el extractor y no
debe leerse como fallo ASR. Canal telefónico: −4 a −5 pp en sintético; en
habla humana el WER casi se duplica (0.115 → 0.221). Corpus provisional
(QA automática, sin escucha humana).

WER sintético (0.706 whisper / 0.644 voxtral) se calcula contra la forma
hablada (synthesis_text) y cuenta sobre todo diferencias de formato
(«einhundertdreiundvierzig» vs «143»); contra la forma escrita falla al
revés (un deletreo = 1 token). No es métrica de reconocimiento ni comparable
con el WER del control humano; no se usa como hallazgo.

### Retractación rex-2

La versión anterior de este documento afirmaba «el cuello de botella está en
la capa ASR» con ~21% (whisper 20.8%, voxtral 21.2%) frente a un techo del
100%. Era incorrecto: el techo se medía sólo sobre synthesis_text (forma
hablada), mientras que los ASR emiten forma escrita. rex-2 sobre written_text
de test daba 26/120 (21.7%), igual que los ASR: se medía la cobertura del
extractor (tokenizer que descartaba `+` y `@`, fechas numéricas,
«11. Dezember», códigos «MMJ-0105», «55a», orden FR calle-número). rex-3 lo
corrige; los números rex-2 quedan en el historial git.

Disciplina dev/test: las reglas rex-3 se derivaron de fallos de dev
(written_text y transcripciones ASR dev). Durante el diagnóstico se
inspeccionaron ~15 transcripciones Whisper de test; dos reglas se vieron allí
primero (código postal sin coma «Weg 61 37672 Ort» y puntos junto a «at»),
aunque son convenciones generales de escritura. Los números test de rex-3
tienen por tanto exposición limitada a test y así se declaran.

## P9 — Entrega: ESTRUCTURA COMPLETADA

- PUBLISHING.md: gates previos, comandos `gh`/`hf` (sintaxis verificada contra
  la CLI instalada) y borradores de comunicación; nada ejecutado ni enviado.
- Gate de reproducción: run_tracks → score_all → compare → report deja
  reports/ idéntico al commit.
- Segundo sintetizador: research/second-tts-gate.md (Piper, condicional).

- LICENSE Apache-2.0 oficial, DATA_LICENSE, THIRD_PARTY_NOTICES, dataset
  card, CONTRIBUTING, validador de bundle (secretos + checksums + derechos).
- Publicación externa NO ejecutada (pendiente de autorización): comandos
  preparados en README y scripts.

## Auditoría adversa

Workflow de 26 agentes (4 dimensiones × verificación de refutación): 22
hallazgos confirmados, todos corregidos en commits etiquetados «audit fixes»
y «rex-2». Una revisión posterior detectó que el techo rex-2 era circular
(ver «Retractación rex-2»); corregido en rex-3. Los hallazgos y su resolución están en el historial git.

## Bloqueos y limitaciones

- Escucha humana del corpus: pendiente → corpus «provisional», no «verified».
- Derechos del audio sintético: condicionales (ver DATA_LICENSE.md).
- Transcripciones totalmente ajenas al texto (p.ej. emails FR convertidos en
  frases sin relación) no permiten distinguir fallo TTS de fallo ASR sin
  escucha; se requiere escucha humana de una muestra.
- Voxtral: completado y puntuado; el bundle local `release_bundle/` pasa
  `release validate` (sin credenciales, checksums verificados).
- Space y dataset HF: artefactos locales listos; publicación externa
  requiere autorización explícita.


## Extensiones (suites separadas; nunca mezcladas con las tablas del núcleo)

Todas: habla sintética, canal telefónico simulado, sólo QA automática,
Whisper large-v3-turbo → extractor rex-4 (congelado antes de puntuar ASR en
cada suite; sus reglas salen de dev). Datos en `data/ext/<suite>/`, informes
en `reports/ext-<suite>/`, scoring CPU con `python scripts/ext_suites.py <suite>`.

### Code-switching (`codeswitch`): COMPLETADO

- 56 escenarios DE/FR (16 dev / 40 test) con separadores y dígitos en inglés,
  alfabeto OTAN en alemán y nombres no DE/FR; valores disjuntos del núcleo.
- rex-3 congelado fallaba 16/56 sobre el texto escrito correcto; rex-4 corrige
  los fallos de dev (marcadores de corrección por palabra completa: «manon»
  se cortaba en «non»; dot/underscore/dash y dígitos en inglés; apellidos O';
  «double vé»/«i grec»). Núcleo: 0 cambios en 720 predicciones.
- Test: whisper 31.2% [22.5, 38.8] frente a techo escrito 65.0% [55.0, 75.0];
  teléfonos con dígitos en inglés 70%; email y nombres limitados por el
  extractor (techo 20-40%).

### Correcciones entre turnos (`multiturn`): COMPLETADO

- 48 casos DE/FR x 2 turnos (misma voz): corrección (valor casi idéntico),
  confirmación, repetición; 96 clips, 0 fallos; whisper 192/192.
- Test (n=64): estado final 42.2% [29.7, 54.7]; techo con texto gold 100%.
  0 valores obsoletos; 19/19 correcto cuando ambos turnos se extraen bien:
  la persistencia funciona y la pérdida es percepción. 2 cambios espurios
  reales (una repetición mal oída sobrescribió un valor correcto).
- Regla de resultado corregida antes de publicar: un turno 1 mal oído que el
  turno 2 no toca es valor erróneo, no cambio espurio (la primera pasada
  etiquetó 8 mal); test que fija la regla.

### Más voces (`voices`): COMPLETADO

- Motivo (análisis de cobertura): en el núcleo dylan supera a serena en ~10 pp
  con ambos ASR, pero voz y escenario estaban confundidos.
- Los 120 escenarios test con vivian y ryan (240 clips, 0 fallos, 480 QA ok,
  whisper 480/480). vivian − ryan pareado +0.8 pp [−3.3, +5.0]. El hueco
  serena/dylan se reparte en ~3 pp de dificultad de escenario y ~7 pp de voz.

### Segunda familia TTS (`piper`): COMPLETADO

- Gate: research/second-tts-gate.md. Voces Piper fijadas (thorsten CC0,
  siwis CC BY 4.0 verificada en la licencia del dataset); runtime GPL en venv
  aislado, no dependencia del paquete. 120/120 sintetizados, 240 QA ok,
  whisper 240/240.
- Qwen − Piper pareado −10.0 pp [−15.4, −4.2] (Piper 44.2% vs 34.2%);
  teléfonos 15% → 70% (DE) y 55% (FR); emails ~0% con ambos. Las cifras
  absolutas del núcleo dependen del sintetizador (advertido en README).

### Español (`es`): COMPLETADO

- Suite de 90 escenarios (30 dev / 60 test) en `data/ext/es/generated/`,
  hash `fd8762328c78df8fe8aa5f598be7c9482f36c16a35fff6fad407c1bdaf345701`.
  Fase texto hecha en rama ext-es por la otra instancia y verificada aquí de
  forma independiente (suite verde; 0 cambios en 720 predicciones del núcleo
  y 0/112 de code-switching con su extractor); fusionada fast-forward.
- Smoke Qwen3-TTS español superado (serena y dylan; ida y vuelta Whisper
  exacta). 90/90 sintetizados, 180 clips QA ok, whisper (language
  'spanish') 180/180.
- Test (60 escenarios x 2 condiciones): whisper 50.8% [41.7, 60.0] frente a
  techo escrito 96.7% [91.7, 100.0] y hablado 95.0%. Celdas: fechas 90%,
  códigos 75%, nombres 60%, teléfonos 60%, direcciones 20%, emails 0%.
  Limpio − teléfono +8.3 pp. No comparable directamente con DE/FR (34.2%):
  escenarios y plantillas distintos; sólo coincide el patrón (emails 0% en
  los tres idiomas).

### Proveedores comerciales: BLOQUEADO

- Requiere proveedor y presupuesto explícitos (AGENTS.md: este encargo no
  autoriza inferencia de pago). No iniciado.
