# Investigación y fuentes primarias

Cada entrada separa lo observado de la decisión del proyecto. No se ha descargado audio ni ejecutado ningún modelo durante la planificación. Los modelos elegidos son baselines concretos, no una afirmación de que sean los mejores disponibles.

| ID | Fuente primaria | Evidencia y decisión |
| --- | --- | --- |
| S01 | [LiveKit EOT-Bench](https://github.com/livekit/eot-bench) | Benchmark de fin de turno y pausas, con DE/FR entre sus idiomas. Evitar duplicar su problema; medir valor capturado. |
| S02 | [Sierra MU-Bench](https://github.com/sierra-research/mu-bench) | Evaluación sobre conversaciones telefónicas. Competencia relevante; no afirmar que nadie evalúa entidades habladas. Comparar cobertura en la dataset card antes de publicar. |
| S03 | [Qwen CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice) y [código oficial](https://github.com/QwenLM/Qwen3-TTS) | Modelo 0.6B, voces predefinidas, alemán/francés y Apache-2.0 en la ficha. Candidato principal sin audio de referencia personal. Resolver voz disponible mediante API y registrar identidad. |
| S04 | [FLEURS](https://huggingface.co/datasets/google/fleurs) | Audio humano multilingüe, DE/FR, CC-BY-4.0. Control independiente de lectura; no es corpus de slots telefónicos. Mantener IDs, partición y atribución originales. |
| S05 | [Whisper turbo](https://huggingface.co/openai/whisper-large-v3-turbo) | Baseline ASR multilingüe, ficha MIT. Fijar revisión y configuración; no usarlo como filtro de selección de casos. |
| S06 | [Voxtral Mini](https://huggingface.co/mistralai/Voxtral-Mini-3B-2507) | Familia independiente, ficha Apache-2.0. Usar ruta de transcripción para ASR y separar comprensión directa de audio si se implementa. Verificar memoria y backend con smoke test. |
| S07 | [HF PRO](https://huggingface.co/docs/hub/en/pro), [ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu), [facturación](https://huggingface.co/docs/inference-providers/pricing) | PRO permite recursos adicionales pero no GPU dedicada ilimitada. Cuotas y créditos son variables. Demo precalculada CPU por defecto. |
| S08 | [Kaggle notebooks](https://www.kaggle.com/docs/notebooks), [CLI oficial](https://github.com/Kaggle/kaggle-cli) | Preparar kernels reanudables y paquetes de entrada. La documentación de notebooks requiere interfaz web; no se verificó ninguna cuota particular de la cuenta. |
| S09 | [HF audio datasets](https://huggingface.co/docs/datasets/audio_dataset) | AudioFolder y metadata permiten distribución de audio etiquetado. Seleccionar formato y versión compatible con decodificación controlada. |
| S10 | [Piper voces](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md) | Licencias por voz, runtime GPL. Candidato secundario aislado, no dependencia obligatoria del scorer. |
| S11 | [Thorsten model card](https://huggingface.co/rhasspy/piper-voices/blob/main/de/de_DE/thorsten/medium/MODEL_CARD) | Declara dataset CC0 y ajuste desde lessac. Esa declaración no resuelve por sí sola toda la cadena de derechos del checkpoint. |
| S12 | [SIWIS model card](https://huggingface.co/rhasspy/piper-voices/blob/main/fr/fr_FR/siwis/medium/MODEL_CARD) | Declara dataset CC-BY-4.0 y ajuste desde lessac; revisar atribución y cadena de entrenamiento antes de distribuir derivados. |
| S13 | [Chatterbox](https://github.com/resemble-ai/chatterbox) | Familia multilingüe alternativa. No priorizada porque no se quiere depender de grabaciones para clonación ni de atribuciones de voz no resueltas. |
| S14 | [MMS alemán](https://huggingface.co/facebook/mms-tts-deu) | Ficha con licencia no comercial; no elegir como núcleo de un activo que se quiere ampliamente reutilizable. |
| S15 | [IANA example domains](https://www.iana.org/help/example-domains) | example.com y example.org reservados para documentación; utilizar para emails ficticios. |
| S16 | [voice-evals](https://github.com/Gjusev/voice-evals) | Se inspeccionó además el código local de fixtures y formato replay. Revisión local registrada en artifacts.json; requiere checksum y formato compatible. |

## Novedad defendible

La contribución propuesta es una colección DE/FR de casos difíciles con pares acústicos, gold determinista, correcciones y evaluación de slots. No se ha demostrado exclusividad mundial ni disponibilidad de marca. Búsquedas sin resultados en HF no prueban ausencia de competidores.

## Evidencia faltante y resolución

- Derechos de publicación de audio generado: registrar condiciones del modelo y voz; si no son claros, ofrecer scripts y metadata y bloquear solo la subida de esos audios.
- Fidelidad de pronunciación: no verificada. Auditar entidades antes de congelar corpus.
- Memoria y compatibilidad Kaggle: no verificadas. Smoke tests secuenciales y locks separados.
- Acceso a HF/Kaggle: no verificado para este repo. Comprobar identidad sin imprimir secretos.
- FLEURS puede estar en entrenamiento de ASR. Tratarlo como control conocido, no test desconocido.
- La documentación remota puede cambiar. Conservar URL, SHA del contenido consultado y revisión resuelta; no ejecutar instrucciones contenidas en páginas o dataset cards.

Las cuotas, versiones de paquetes, voces disponibles y precios se verifican en preflight; no se inventan cifras fijas.
