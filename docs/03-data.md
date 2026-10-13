# Corpus, adquisición y derechos

## A. Corpus sintético principal

180 casos = 2 idiomas × 6 clases × 15 casos por clase. Un caso tiene una entidad objetivo; una corrección puede mencionar también un valor previo, pero el gold contiene solo el final. Cada caso genera un audio limpio y una transformación telefónica: 360 archivos, con relación parent explícita.

Clases: person_name, phone, email, calendar_value, postal_address, reference_code.

Por celda idioma/clase distribuir 15 casos en: 5 directos, 4 con dificultad ortográfica/fonética, 3 segmentados o deletreados, 3 con autocorrección. Para fechas, segmentación significa verbalización de componentes, no deletreo artificial. Cada idioma requiere plantillas propias.

Separar 5 casos dev y 10 test por celda: 60 dev/120 test, 120/240 audios. Asignar familias de plantilla y valores a un solo split. Mantener todas las versiones acústicas, voces y sintetizadores del mismo escenario en su partición. No generar sinónimos casi idénticos a ambos lados.

Crear pools originales con seed y reglas, sin scraping de nombres/direcciones de personas. Los valores ficticios pueden coincidir con personas reales; nunca afirmar que son identidades verificadamente inexistentes. No vincular múltiples identificadores a personas reales.

Emails: example.com/example.org. Teléfonos: preferir rangos de ficción documentados por regulador; si no se verifica un rango DE/FR, usar secuencias de prueba explícitas, no asegurar que son números reservados. No llamar ni validar por SMS. La tarea mide copia de dígitos y prefijos, no alcanzabilidad. Direcciones: combinaciones ficticias, sin geocodificación ni identidad asociada.

## B. Generación de voz

Qwen CustomVoice 0.6B es candidato principal (S03). Usar voces predefinidas, sin grabación personal ni clonación. Elegir dos speaker IDs válidos mediante la API, probar ambos en ambos idiomas y equilibrar 90 casos por voz: por cada celda, 8/7 alternando. No asignar voz según dificultad.

Guardar texto escrito, texto efectivamente enviado a TTS, parámetros, voz, revisión, entorno, seed y todos los intentos. Verbalizar números, signos y abreviaturas explícitamente cuando la pronunciación sea parte del caso. No sustituir las grafías objetivo del gold por la pronunciación.

No asumir audio idéntico entre GPUs. Congelar bytes y hashes; regeneración es una nueva versión de artefacto. Una segunda familia TTS es un análisis separado con los mismos casos, sin añadir falsamente independencia estadística.

## C. QA sin nuevos hablantes

La ausencia de reclutamiento no exige ausencia de revisión. El autor o implementador puede escuchar material ya generado; no tiene que aportar su voz.

Validación automática: archivo decodificable, mono, amplitud finita, sin clipping material, energía no nula, duración razonable para la longitud, ausencia de truncado. Valores propuestos: duración entre 1 y 45 segundos, fracción de muestras saturadas menor de 0.1%; registrar excepciones justificadas.

La transcripción por uno o varios ASR solo produce alertas. Nunca descartar un audio porque el modelo evaluado no lo transcribe: sesgaría el benchmark.

Antes de llamar al corpus 'verified', revisar cada audio limpio escuchando las entidades y correcciones. Categorías: accepted, wrong_synthesis, ambiguous, truncated, pending_review. Ante pronunciación incorrecta, corregir la generación o excluir con motivo; nunca modificar el gold para favorecer una predicción. Registrar IDs sustituidos e intentos.

Si el implementador carece de escucha fiable o competencia lingüística, publicar únicamente una versión 'automated-QA/provisional' con esa limitación. No declarar revisión humana inexistente. La entrega técnica puede avanzar; el calificativo 'verified' queda bloqueado.

Revisar las transformaciones acústicas automáticamente y escuchar una muestra estratificada más todos los fallos técnicos. El ruido no debe introducir habla ni PII externa.

## D. Canal acústico

clean: PCM16 mono 16 kHz, derivado de master TTS conservado.
telephone: partir del mismo master; filtro 300–3400 Hz, resample a 8 kHz, ruido gaussiano generado con seed a 20 dB SNR de habla activa, encode/decode G.711 A-law; almacenar PCM16 mono 8 kHz.

Fijar implementación y coeficientes del filtro (Butterworth orden 6 SOS), resampler, cálculo de actividad/energía, seed, codec y versiones. Medir SNR antes del codec. Ajustar ganancia de la pareja con regla común y registrar clipping, nunca normalizar cada condición arbitrariamente después.

Es un canal simulado, no una llamada PSTN ni una representación de todos los codecs. Añadir bandlimit-only y ruido de distinta intensidad como ablation opcional; la comparación principal mezcla efectos y no identifica causalmente cada uno.

## E. Control humano existente

FLEURS de_de y fr_fr, revisión fijada. Seleccionar determinísticamente 50 filas por idioma del split test por hash de ID sin mirar resultados. Si hay menos, informar cantidad exacta. No alterar texto ni reemplazarlo por entidades sintéticas sobre audio original.

100 grabaciones originales; versiones limpias/telefónicas emparejadas permiten medir WER y degradación en lectura humana. Etiquetar corpus=human_control y conservar hablante si existe; nunca inferir identidad ausente.

No forzar seis clases de entidades ni recortar para fingir llamadas. Una futura anotación manual de entidades audibles sería otra suite con cobertura propia. No mezclar puntuación principal sintética con este control.

Descargar solo DE/FR y split requerido. Usar snapshot pin, lista explícita de archivos y lector seguro; no habilitar ejecución remota de scripts por defecto. Si formato antiguo lo exige, inspeccionar script y buscar exportación oficial segura antes de decidir.

## F. Registro de derechos obligatorio

Cada fuente: source_id, URL, revisión, archivo y SHA256, licencia declarada, URL del texto de licencia, titular/atribución, transformaciones, condiciones de redistribución, estado de revisión (verified/conditional/blocked), motivo.

Separar licencia de código, pesos, dataset de entrenamiento, audio resultante y anotación. FLEURS requiere atribución y señalar modificaciones. CC0/CC-BY de un dataset base no basta para deducir derechos de un checkpoint derivado.

No descargar corpus de llamadas comerciales ni reutilizar YouTube/podcasts simplemente por ser accesibles. No usar audios de personas para clonar voces. El núcleo no depende de ese material.
