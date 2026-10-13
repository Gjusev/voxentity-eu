# Evaluación y metodología

## Tracks separados

A. ASR: Whisper turbo y Voxtral Mini sobre audio idéntico; transcripción sin hints de entidades. Idioma explícito para ambos. Reportar WER de corpus (suma errores / suma palabras) y CER, incluyendo variantes verbales conservadoras. No confundir con promedio por clip de voice-evals.

B. ASR → slots: mismo extractor fijo para ambas transcripciones. Ejecutarlo además sobre la transcripción gold: estima techo del extractor. Un extractor fallido sobre gold es fallo del sistema de evaluación, no del ASR.

C. Audio → slots: opcional, modelo capaz de recibir audio e instrucciones; no compararlo como si fuera ASR idéntico.

D. Agent slots: agente recibe audio y solicitud del campo, persiste valor mediante store_slot. Evaluar el estado final leído de su almacenamiento y eventos; palabras dichas por el agente no prueban persistencia.

Implementar extractor de referencia basado en reglas limitadas y publicadas. Para nombres/direcciones usar gramática del dominio y límites de frase, sin lista gold. Añadir extractor LLM opcional con prompt/modelo fijo, temperatura y salida JSON controlada. Reportar cada sistema como combinación ASR+extractor, no atribuir sus fallos solo a ASR.

## Métricas primarias

Para N ejemplos elegibles con una entidad:
- Exactitud de slot = ejemplos con valor correcto / N. error/timeout/vacío/no persistido cuentan incorrectos.
- Cobertura operacional = inferencias completadas / N.
- Exactitud condicional = correctos / completados, secundaria junto a cobertura.
- Omisión = objetivo sin predicción / N.
- Sustitución = objetivo presente con valor equivocado / N.
- Salida extra = ejemplos con slots no solicitados o duplicados / N.
- En casos de corrección, stale-value rate = estado final conserva valor previo / casos con corrección.

Para suites multi-slot futuras: TP con matching uno-a-uno, FP extras y valores erróneos, FN objetivos no recuperados; publicar precision/recall/F1 y exactitud de todos los slots por caso. No llamar 'alucinación' a toda sustitución: la fuente del error no se conoce solo por mismatch.

## Resúmenes

Publicar conteos y scores por idioma, entidad, condición, voz, sintetizador y tipo de dificultad. Macro principal: promedio de las 12 celdas idioma×entidad, por condición. Micro y pesos disponibles. No ranking agregado entre suites o tracks incompatibles.

Degradación pareada = accuracy_clean - accuracy_telephone, en puntos porcentuales. Mostrar pares fail→pass, pass→fail, pass→pass y fail→fail. Usar misma lista de escenarios para cada comparación.

Intervalos bootstrap percentil 95%, 2000 réplicas con seed, remuestreo por scenario_id incluyendo sus variantes y modelos; estratificado por idioma×entidad. Para diferencias entre sistemas, remuestrear los mismos clusters. En control humano, cluster por speaker si disponible y avisar si solo puede hacerse por utterance.

El CI refleja variación entre casos del corpus, no diversidad de hablantes humanos ni incertidumbre de generación. No afirmar diferencias significativas por rankings mínimos o celdas pequeñas. Reportar ausencia de diferencia concluyente.

## Fallos y QA

Elegibilidad se congela antes de inferencia. No excluir casos basándose en desempeño. Publicar generated/accepted/excluded y motivos QA. Mismos audios elegibles para todos los modelos; unsupported cuenta como fallo en suite requerida y se muestra como tal.

Reportes de runs incompletos deben llevar incomplete=true y no participar del ranking de ejecución completa. Reintentos guardan resultados previos; política máximo 2 reintentos de errores transitorios, nunca buscar una respuesta correcta por ensayo repetido.

## Experimentos obligatorios

E1 dos baselines ASR en corpus principal.
E2 ambos ASR con extractor compartido y baseline gold→extractor.
E3 agente de referencia con captura final, incluyendo correcciones y control negativo que retiene valor previo.
E4 control FLEURS: WER/CER limpio vs canal, separado de entidad.
E5 segundo TTS sobre subconjunto estratificado de 60 casos (5 por celda), si cadena de derechos/ejecución resuelta. Si no, limitación explícita de familia única y perfil preparado.

Para agentes de proveedores reales: adaptadores condicionales con mismo contrato final, audio, preguntas y políticas. Dos configuraciones del mismo reference agent no se presentan como dos proveedores.

## Informe de errores

Clasificar digit_swap, missing_prefix, spelling_loss, accent_loss, correction_ignored, address_component_loss, format_only, extra_slot, timeout, synthesis_issue. Clasificación automática es heurística y revisable. Publicar todos los casos, con selección determinista para demo, sin escoger solo errores que favorezcan el titular.
