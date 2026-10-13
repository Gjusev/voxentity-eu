# Publicación y evidencia profesional

## README público final

Explicar en una frase tarea y corpus sintético; mostrar ejemplo audible y tabla medida con N y CI; dar comando CPU reproducible; enlazar dataset, notebook y demo reales. Indicar qué se implementó y qué es extensión. Sustituir enlaces placeholder solo después de publicación comprobada.

## Hugging Face Dataset

Namespace del usuario verificado durante preflight; nombre propuesto voxentity-eu. Configs synthetic_core y human_control independientes; splits dev/test y columna condition. No crear train artificial. Audio PCM publicado como WAV/FLAC con sampling rate explícito y hashes del fichero servido.

Dataset card: composición, fuente, labels, generación, voces, versiones, transformación, QA, splits, licencias, limitaciones y usos no soportados. Explicar que referencias públicas de test pueden contaminar futuros modelos.

Publicar pesos nunca es necesario. Versionar release con SHA del manifest y lista de checksums. Mantener histórico de correcciones de labels.

## Space CPU

Interfaz inglesa: selector idioma, entidad, condición, sistema y tipo de error; reproductores clean/telephone sincronizados por caso; gold, transcripción, slot capturado y puntuación. Mostrar estado de QA y fuente sintética/humana cerca del audio.

Cargar tabla de resultados congelados, paginar, ofrecer CSV/JSON descargables y enlace exacto al caso. Botón para ejemplo correcto y error, selección determinista. No mostrar valores inventados si no hay resultados: estado vacío explícito. No formularios con datos de usuarios ni generación abierta necesaria.

Pruebas: carga sin GPU/token, filtros coherentes, navegación por teclado, transcript accesible, nombres legibles, fallo de audio visible, rutas restringidas al bundle.

## Informe técnico

Preguntas: cuánto cambia exactitud por condición; qué entidades fallan; cuánto error añade extracción; si correcciones llegan al estado guardado; si la degradación de ASR aparece también en control humano.

Gráficas: accuracy por entidad/idioma con N; delta pareado y CI; matriz pass/fail de clean→telephone. Una gráfica de WER vs slot accuracy ilustra discrepancias si los datos lo permiten.

Incluir corpus/modelos/configs, prompts, fallos operacionales, exclusiones QA, intervalos y limitaciones. Separar hipótesis de hallazgos. No atribuir un error al idioma, género o acento de personas reales a partir de voces sintéticas.

## Revisión de release

Ejecutar checklist de docs/10-validation.md. Preparar comandos/scripts para GitHub/HF/Kaggle y crear release bundle local. El encargo actual crea un repo local y plan; la publicación externa efectiva requiere que el encargo de implementación la incluya. No enviar mensajes a terceros automáticamente.

Confirmar que un visitante sin cuenta ve archivos permitidos y puede cargar notebook/Space. Almacenar release URLs verificadas en RELEASE_MANIFEST.json.

## Uso para búsqueda de trabajo

Preparar un caso técnico público y demo breve apoyados en resultados reales. CV template sin cifras ficticias:
'Built VoxEntity-EU, an open German/French spoken-entity benchmark; evaluated [systems] across [independent scenarios] with paired telephone-channel simulations, publishing reproducible results and final-slot failure analysis.'

Redactar mensajes opcionales para equipos de voz con hallazgo, impacto y enlace reproducible; guardarlos como borradores. Priorizar evidencia comprobable y claridad de límites. No asegurar entrevistas, puntuar impacto laboral como ciencia ni usar estrellas como métrica de éxito.

## Documentación adicional

CONTRIBUTING: añadir modelos sin ver gold, casos con licencia, correcciones y ejecución de tests.
DATA_LICENSE: derechos por componente y notices.
REPORT: resultados reales únicamente.
MODEL_ADAPTERS: capacidades, limitaciones y formato.
IMPLEMENTATION_STATUS: completo/bloqueado/no iniciado y evidencias.
