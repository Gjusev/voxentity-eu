# HF PRO, Kaggle y reproducibilidad

## Preflight obligatorio

Comprobar identidad de cuenta, acceso a modelos, cuota GPU real, disco/RAM, GPU/VRAM/CUDA, acceso a internet y secreto disponible. Imprimir solo nombres de variables y estado presente/ausente. No asumir que una suscripción está autenticada en esta máquina.

No usar cifras fijas de créditos o horas. HF PRO no equivale a inference endpoints dedicados gratis (S07). Kaggle asigna recursos sujetos a disponibilidad; no prometer dos GPUs ni ejecución ininterrumpida.

## Reparto

- Local CPU: generación de casos, contratos, transformaciones, scorer, informes y Space con resultados guardados.
- Kaggle GPU: síntesis y baselines secuenciales, un modelo a la vez, batch inicial 1.
- HF Dataset: distribución versionada; HF Space CPU: exploración de audio y errores.
- ZeroGPU: extensión opcional interactiva, nunca dependencia para reproducir el resultado publicado.

Si Voxtral no cabe: medir pico, bajar batch y usar offload documentado; evaluar cuantización como sistema distinto con configuración explícita. No cambiar silenciosamente de modelo. Si sigue bloqueado, dejar sistema pending, mantener resultados del disponible y no declarar comparación de dos modelos completada.

## Notebooks requeridos

generate: instalar entorno fijado, cargar plantillas, verificar derechos, generar lotes, guardar QA/provenance y checkpoint por clip.
evaluate: recibir audio congelado, descargar pesos por SHA, transcribir por modelo y guardar predicciones; gold solo se monta en etapa de scoring separada.
reproduce: CPU y sin internet con bundle preparado; verificar hashes y regenerar todas las tablas a partir de predicciones incluidas.

Código fuente en scripts importables y notebook fino; evitar lógica duplicada en celdas. Dataset de entrada Kaggle privado durante preparación, público solo cuando rights/release gates pasan. Todo output debe sobrevivir reinicio a partir del bundle versionado, no del disco efímero.

## Dependencias y artefactos

Resolver versiones desde docs oficiales y verificar instalación; crear locks por perfil core/tts/asr1/asr2/space. Registrar Python, torch, CUDA, hardware y precisión. No usar latest/main en corridas de release.

Bundle: manifests, gold, inputs, licencias, checksums, scripts/notebooks, locks, predicciones completas, reporte y dataset card. Pesos no se redistribuyen por defecto; indicar descargas oficiales fijadas. Datos humanos como IDs/receta o audio con atribución conforme a derechos.

## Cuentas y gasto

Usar HF_TOKEN con permisos mínimos y Kaggle Secrets para jobs. No almacenar kaggle.json o tokens en notebooks/salidas. No lanzar jobs de pago ni autoampliar cuota por defecto. Config max_paid_spend=0; implementador puede completar núcleo con cómputo disponible y preparar adaptadores pagos desactivados.

Faltan autenticación o recursos: documentar diagnóstico exacto, comandos preparados y siguiente paso; seguir trabajo local independiente. No solicitar claves por chat ni inferir crédito de otras cuentas.

## Reproducción

Nivel 1 obligatorio: scoring idéntico desde predicciones congeladas en CPU.
Nivel 2 obligatorio: nueva inferencia con mismos pesos/config, admitiendo diferencias GPU documentadas.
Nivel 3 informativo: resíntesis desde recipe, sin prometer igualdad de bytes.

Las cifras de latencia de Kaggle solo describen ese entorno, no rendimiento de llamadas de usuarios.
