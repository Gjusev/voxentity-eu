# Backlog de implementación

Orden por dependencias, sin calendario. Las casillas están pendientes; escribir documentación no significa haber implementado funcionalidad.

## P0 — Fundaciones

- [ ] Crear pyproject, paquete, CLI y extras separados; escoger lock tool y registrar decisión.
- [ ] Implementar schemas y validar ejemplos.
- [ ] Crear tests de IDs, rutas, tipos, duplicados y aislamiento de gold.
- [ ] Añadir CI CPU offline, lint y validación de links internos.
Aceptación: instalación limpia, import sin torch/GPU/red; CLI help y ejemplos parseables; tests adversariales pasan.

## P1 — Scorer

Depende P0.
- [ ] Normalización por entidad con literal/canonical separados.
- [ ] Scoring con fallos, omisión, sustitución, extras y correcciones.
- [ ] Agregación, comparación pareada e intervalos por cluster.
- [ ] Fixtures con resultados calculados a mano y controles negativos.
Aceptación: errores de un dígito/acento se detectan; tasa global mantiene denominadores; runs incompletos no rankeados; informe CPU repetible.

## P2 — Casos y derechos

Depende P0.
- [ ] Escribir pools y plantillas DE/FR originales, matriz 180 casos.
- [ ] Split 60 dev/120 test sin overlap de familia/valores equivalentes.
- [ ] Manifest de fuentes y checklist de derechos por asset.
- [ ] Export de inputs sin gold y IDs opacos.
Aceptación: counts exactos, equilibrio de dificultad y voz, validación semántica de correcciones, ninguna fecha de desarrollo añadida.

## P3 — Síntesis y QA

Depende P2.
- [ ] Resolver Qwen y speaker IDs; smoke test por idioma/voz.
- [ ] Generador reanudable, provenance, hashes y registros de intentos.
- [ ] QA automática, revisión de audio disponible y flujo de exclusiones.
- [ ] Paquete de revisión para casos pending.
Aceptación: 180 clean accepted para verified o estado provisional explícito; errores TTS no etiquetados como errores ASR; ningún filtro basado en resultados del modelo evaluado.

## P4 — Canal

Depende P3.
- [ ] Implementar recipe fija, ruido seed, codec y checks de audio.
- [ ] Generar 180 pares y verificar relaciones.
Aceptación: 360 archivos válidos cuando P3 completo; sample rates y hashes coinciden; test de banda/SNR sin asumir latencia real.

## P5 — Baselines y runner

Depende P1/P4.
- [ ] Doctor Kaggle/HF; locks y smoke tests por backend.
- [ ] Adaptadores Whisper y Voxtral; resume, timeouts y cache.
- [ ] Extractor común y control gold→extractor.
- [ ] Corridas completas con inputs aislados.
Aceptación: al menos dos familias ASR realmente ejecutadas; artefactos por clip; comparación con misma cohorte; OOM/error no oculto.

## P6 — Slots persistidos y voice-evals

Depende P5.
- [ ] Agente de referencia y storage instrumentado.
- [ ] Corrección dentro del turno; control negativo stale-value.
- [ ] Export fixtures separados por voz/condición y conversión explícita 8→16 kHz.
- [ ] Contract test con versión fijada de voice-evals.
Aceptación: scorer lee estado final real; replay no inventa timings; texto duplicado no sobrescribe audio; core funciona sin voice-evals instalado.

## P7 — Control humano y sensibilidad

Depende P1/P5.
- [ ] Descarga FLEURS selectiva por revisión, IDs y atribución.
- [ ] Muestreo determinista 50 por idioma y versiones acústicas.
- [ ] Evaluación WER/CER separada.
- [ ] Investigar/implementar segundo sintetizador solo si derechos resueltos; reportar gate.
Aceptación: control humano ejecutado o bloqueo verificable sin falso reclutamiento; todas las tablas distinguen corpus; alternativa TTS no bloquea release core.

## P8 — Informes y demo

Depende P5/P6; integrar P7 cuando disponible.
- [ ] Tablas, bootstrap, taxonomía de errores y reporte en inglés.
- [ ] Space CPU de resultados precalculados.
- [ ] Notebooks de generación, evaluación y reproducción.
Aceptación: demo reproduce números del reporte, audio correcto por ID, ningún placeholder numérico presentado como hallazgo.

## P9 — Entrega publicable

Depende P8.
- [ ] Licencias oficiales, notices, dataset card, README y CONTRIBUTING.
- [ ] Bundle con checksums, manifiesto y controles de release.
- [ ] Comandos de publicación y borradores de comunicación.
- [ ] Actualizar IMPLEMENTATION_STATUS con comandos ejecutados/evidencias.
Aceptación: fresh-environment scoring offline idéntico, ninguna credencial, derechos resueltos para assets publicados, nombres y claims coherentes.

## Extensiones después del núcleo

- [ ] Dos proveedores de voz con acceso y presupuesto, estado final verificable.
- [ ] Correcciones entre turnos y code-switching.
- [ ] Español y nueva versión de corpus.
- [ ] Más voces/casos si análisis revela cobertura insuficiente.

Cada extensión tiene suite propia. No inflar tamaño del corpus principal ni completar casillas con mocks.
