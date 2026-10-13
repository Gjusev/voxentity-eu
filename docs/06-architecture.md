# Arquitectura y contratos de ejecución

Python 3.11 como entorno base propuesto. Paquete src/voxentity_eu, CLI voxentity. Core: Pydantic, NumPy, SciPy, soundfile, jiwer; visualización/Parquet/HF en extras. PyTorch y cada backend en entornos separados si sus versiones chocan. Resolver locks reales durante implementación.

## Árbol objetivo

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
- data/manifest y gold pequeños versionados; audio y resultados grandes fuera de Git.

## Interfaces

Synthesizer.generate(text, locale, voice_id, config) → master audio + provenance.
ASR.transcribe(audio, locale, config) → transcript/status; sin parámetros de gold.
SlotExtractor.extract(transcript, requested_type, locale) → slots/status.
Agent.evaluate(audio, requested_type, locale) → transcript, eventos y estado final observable.
Scorer.score(gold, predictions, policy) → detalles deterministas.
Runner no importa scorer ni monta gold. Scorer no llama red.

## CLI a implementar

Estos comandos son especificación futura; todavía no funcionan:

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

Exit: 0 operación completada, 1 gate de calidad fallido, 2 entrada/config inválida, 3 dependencia o recurso ausente. Runs parciales con errores producen reporte pero exit no cero. stdout JSON con --json; logs en stderr.

## Reanudación y caché

Clave incluye hash audio, sistema, prompt, modelo, normalización aplicable y entorno. Escribir atomicamente por clip; verificar checksum antes de reutilizar. Cambios en política invalidan caché relevante. No sobrescribir corridas distintas con mismo ID. Guardar índice de éxitos/fallos y parámetros, no solo tabla final.

## Agente de referencia

Servidor/proceso local con interfaz audio, transcripción, extractor y sqlite o JSONL de eventos store_slot. session_id por caso, reset estricto; finalizar, leer estado mediante API independiente y exportarlo. Corrección reemplaza valor anterior. Test negativo conserva primero, test positivo conserva último. No necesita llamadas de teléfono ni cuentas externas.

Una sesión grabada prueba la persistencia observada; no implica comportamiento de otro proveedor. Adaptadores externos tienen que proporcionar observación equivalente o usar track separado de respuesta declarada.

## Extractor determinista de referencia

Crear parsers DE/FR por tipo solicitado: números cardinales y secuencias de dígitos; palabras de símbolos de email; meses y componentes de calendario; alfabeto deletreado y bloques de referencia. Separar extracción de texto de canonicalización de valores. Para nombres y direcciones, admitir las construcciones lingüísticas documentadas y devolver unsupported_parse si no son interpretables, sin recurrir a lookup del gold.

Detectar marcadores de corrección ('pardon', 'je corrige', 'Entschuldigung', 'ich korrigiere') con reglas de ámbito: reemplazan la entidad correspondiente, no cualquier número anterior. Versionar reglas y testear negación, varias menciones y prefijos de cortesía. Estos son ejemplos de diseño, no una lista lingüística exhaustiva.

La gramática puede conocer estructura de la tarea, pero no template_id ni entidades canónicas del caso. Templates de test pertenecen a familias reservadas; congelar parsers usando dev. Evaluar gold→parser por celda antes de las comparaciones y reportar su techo, incluso si es bajo. Una mejora basada en test exige una nueva versión y explicitar reutilización del test.

## Integración voice-evals verificada

Código local inspeccionado: C:/Code Main/voice-evals, commit en research/artifacts.json. FixtureCallerVoice indexa clips por texto exacto: dos audios del mismo texto colisionarían. Crear un manifest separado por voz×condición y rechazar duplicados dentro de cada manifest.

Shape: format={sample_rate,channels,sample_width,encoding}, clips=[{text,file,sha256,provenance}], note. WAV/PCM admitidos; no hace resampling silencioso. Exportar audio telefónico derivado explícitamente a 16 kHz para transporte compatible, manteniendo original 8 kHz y ambos hashes. Upsampling no restaura banda ancha.

Replay usa id, scenario{name,expected_outcome}, ground_truth_transcript y observaciones disponibles. Exportar outcome solo cuando se leyó estado; no fabricar timings. required_facts por substring no sustituye nuestro scorer de entidades. Entregar resultados de VoxEntity en sidecar.

El repo nuevo conserva independencia; voice-evals es integración opcional, con versión fijada y contract test real.
