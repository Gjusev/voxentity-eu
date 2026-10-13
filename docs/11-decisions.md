# Decisiones y límites

## Fijas

D01 Repo independiente voxentity-eu, sin ELO.
D02 Núcleo sintético DE/FR y control humano público separado.
D03 No reclutamiento, clonación personalizada ni scraping de audio sin licencia.
D04 Qwen CustomVoice como candidato principal; revisión registrada, ejecución pendiente.
D05 Whisper turbo y Voxtral Mini como baselines candidatos concretos.
D06 Evaluar persistencia final además de texto.
D07 CPU Space y scoring offline; Kaggle para batch GPU.
D08 Gold aislado de sistemas evaluados.
D09 180 escenarios/360 archivos como alcance inicial; diferencias por QA se informan.
D10 Fechas y estimaciones de desarrollo ausentes; se permiten magnitudes técnicas de audio y referencias a modelos cuyo nombre contiene números.

## Condicionales ya resueltas por política

Sin voz válida: seleccionar otra voz predefinida del mismo modelo y repetir QA, sin clonación.
Sin derechos resueltos: bloquear redistribución del asset, continuar implementación.
Sin FLEURS accesible: dejar control humano pendiente con evidencia, no sustituir por TTS etiquetado humano.
Sin segundo modelo ejecutable: reportar baseline único parcial, no declarar comparación completa.
Sin acceso a proveedor: reference agent y baselines abiertos; adaptador preparado desactivado.
Sin revisión auditiva: corpus provisional claramente etiquetado.
Sin segunda familia TTS: análisis principal permitido con limitación explícita.
Sin permiso de publicación externa en encargo siguiente: bundle y comandos preparados localmente.

## Aspectos que el implementador debe resolver mediante pruebas

Versiones exactas de dependencias; speaker IDs; memoria GPU y precisión; backend Voxtral; hash de voces alternativas; formato físico más compatible de FLEURS; calidad efectiva de pronunciación DE/FR.

No requieren volver a preguntar preferencias: ejecutar smoke tests, documentar decisión y continuar. Solo los límites de cuenta, acceso, presupuesto o derechos que no se puedan resolver localmente justifican bloqueo externo.
