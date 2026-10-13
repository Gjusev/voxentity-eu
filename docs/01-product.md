# Producto y alcance

## Pregunta

¿Conserva un sistema el valor exacto que comunica un usuario en alemán o francés, incluyendo una corrección, cuando el audio pasa por un canal telefónico simulado?

Tres resultados distintos: transcripción; extracción de entidades a partir del texto; estado final realmente guardado por un agente. Ninguno sustituye a los otros.

## Público

Ingenieros de voice agents y equipos que reciben reservas, direcciones de entrega o referencias de soporte. Para contratación, el activo muestra diseño experimental, datos, adaptación de modelos y depuración de fallos observables.

## Entregables obligatorios

- Paquete instalable y CLI con scoring offline.
- Dataset principal sintético: 180 escenarios, dos condiciones, 360 audios.
- Gold, metadata y procedencia en JSONL/Parquet.
- Dos baselines ASR abiertos de familias distintas.
- Extracción compartida sobre transcripciones gold y predichas.
- Agente de referencia con almacenamiento local de slots e instrumentación.
- Exportador para fixtures de voice-evals, sin modificar ese proyecto.
- Control humano independiente con FLEURS o explicación verificable de su bloqueo.
- Notebook Kaggle de generación; notebook de evaluación; notebook CPU de reproducción.
- Space CPU de errores precalculados.
- Informe con incertidumbre, denominadores, fallos y ejemplos audibles.
- Dataset card, reporte de derechos y comandos de publicación.

## Alcance ampliado explícito

Otra familia TTS para sensibilidad al sintetizador; hasta dos adaptadores de proveedores accesibles; correcciones entre turnos; code-switching DE/EN o FR/EN; español. Solo después del núcleo, en suites separadas con IDs y resultados propios.

La versión inicial ya incluye correcciones dentro de una emisión. No mide interrupciones ni detección de fin de turno. Una política programada de referencia no se presenta como agente comercial ni se rankea junto a ellos sin indicar su naturaleza.

## Tamaño y afirmaciones

Los 360 archivos representan 180 casos emparejados, no 360 observaciones independientes. Cada celda idioma × entidad tiene 15 escenarios. Es un diagnóstico pequeño, sin poder garantizado para diferencias reducidas.

No hay garantía de que un modelo falle más en una condición. Un resultado nulo también se publica. No se fijan titulares antes de medir.

## Licencias objetivo

Código original: Apache-2.0. Anotaciones originales: CC-BY-4.0. Audio: licencia por fuente y derechos comprobados; no aplicar automáticamente la licencia del código a los audios. Preparar LICENSE, DATA_LICENSE.md y THIRD_PARTY_NOTICES durante implementación con textos oficiales.
