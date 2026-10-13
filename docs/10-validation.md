# Validación y gates

## Tests críticos

| Área | Caso | Esperado |
| --- | --- | --- |
| Normalización | teléfono pierde cero inicial | incorrecto |
| Normalización | ß vs ss, é vs e | distinto salvo variante prefijada |
| Normalización | código O vs 0 | incorrecto |
| Email | cambio de dominio/carácter | incorrecto |
| Corrección | devuelve primera mención | stale e incorrecto |
| Calendar | falta componente solicitado | incorrecto; sin inferencia gold |
| Address | calle bien, número mal | slot incorrecto |
| Integridad | fila duplicada/ID ajeno | error de run |
| Integridad | timeout con ID válido | participa como fallo |
| Integridad | predicción ausente | run incompleto, sin ranking |
| Gold | nombre de archivo incluye respuesta | rechazo de inputs |
| Split | pareja en dev y test | rechazo del corpus |
| Audio | master/teléfono sin parent válido | rechazo |
| Audio | extensión correcta pero bytes corruptos | rechazo |
| Estadística | variantes duplicadas | no aumenta N independiente |
| Bootstrap | mismo seed/datos | mismo resultado |
| Resumption | cambio modelo/prompt/hash | cache no reutilizado |
| Agent | dice valor correcto pero no lo guarda | fracaso agent_slots |
| voice-evals | textos repetidos en mismo manifest | rechazo |
| Space | tabla y audio diferentes | test falla |
| Publicación | modelo/licencia/QA sin resolver | asset bloqueado o provisional explícito |

No probar ASR contra una respuesta garantizada: las regresiones de software usan fixtures; los modelos reales producen resultados medidos, no un gate arbitrario de accuracy.

## Gates de entrega

G1 Contratos: schemas/exemplos/tests y semántica acordes.
G2 Derechos: registro completo y assets autorizados según evidencia; pendientes excluidos de bundle publicable.
G3 Corpus: counts, splits, hashes, parejas, voces, QA y exclusiones visibles.
G4 Evaluación: dos baselines, extractor gold, estados de agente observados; cada run con cohorte y failures.
G5 Honestidad: synthetic/provisional/control humano/mock diferenciados en todos los medios.
G6 Reproducción: tablas regeneradas sin internet desde resultados congelados.
G7 Producto: Space CPU abre, filtros/audio/descargas funcionan.
G8 Publicación: links reales, notices y dataset card corresponden al bundle.

Para cada gate guardar comando, resumen de salida y rutas de artefactos. Gate fallido no obliga a borrar trabajo; bloquea la afirmación correspondiente.

## Riesgos y decisiones de contingencia

- TTS pronunciación inválida: corregir receta y volver a QA; conservar exclusión e intento.
- Falta escucha competente: release provisional, no verified.
- Solo una familia TTS: declarar limitación; no extrapolar a humanos.
- FLEURS conocido por modelos: usar como control, no ranking de generalización.
- No GPU: completar scorer, UI y notebooks; inference pendiente explícita.
- No credenciales externas: resultados abiertos primero, proveedores opcionales pendientes.
- Derechos inciertos: no distribuir audio afectado; preparar scripts/datos propios y registrar bloqueo.
- Resultados sin diferencias: publicar resultados nulos; no cambiar test para fabricar fallo.
- Pocos casos por celda: CI, conteos y análisis exploratorio, sin afirmaciones universales.
- Desacuerdo de normalización: publicar literal y canonical, congelar política antes de inferencia.
