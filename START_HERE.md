# Encargo para el siguiente agente

Implementa VoxEntity-EU a partir de esta especificación. El objetivo es un proyecto público independiente que muestre capacidad de ingeniería de evaluación y resultados reproducibles sobre entidades habladas DE/FR.

## Orden de lectura

1. README.md y AGENTS.md.
2. docs/01-product.md y docs/02-research.md.
3. docs/03-data.md a docs/07-compute.md.
4. docs/08-publication.md a docs/11-decisions.md.
5. research/artifacts.json y los ejemplos en examples/.

Los enlaces a internet justifican capacidades existentes. Las decisiones de diseño y umbrales de aceptación son decisiones de este proyecto, no resultados empíricos.

## Primera acción de implementación

Comprobar git status, crear el paquete Python mínimo, contratos tipados y tests del scorer. Crear un conjunto diminuto de fixtures textuales con resultados calculados a mano. No descargar un corpus completo ni iniciar GPU antes de validar contratos, aislamiento del gold y smoke tests.

## Secuencia

Contratos y scorer → casos → generación y QA → transformaciones acústicas → baselines → agente con slots → control humano → informes → Space/notebooks → preparación de publicación.

Si no hay GPU o credenciales, continuar con todo el trabajo offline y preparar jobs reanudables. Registrar lo pendiente en IMPLEMENTATION_STATUS.md. No inventar resultados para dar por terminada una fase.

## Definición de finalización

Un tercero puede obtener el dataset publicado, ejecutar scoring offline sobre predicciones verificables, reproducir al menos dos baselines abiertos, escuchar errores en el Space y entender exactamente qué mide cada tabla. Las referencias públicas deben existir y abrirse antes de declararlas publicadas.

El alcance obligatorio incluye un agente de referencia que persiste slots observables. Dos proveedores comerciales son una ampliación condicionada a acceso y presupuesto; no bloquean la versión abierta.

## Prompt de continuación sugerido

> Lee AGENTS.md y START_HERE.md. Implementa el backlog de docs/09-implementation.md en orden, respetando sus criterios de aceptación y docs/10-validation.md. Mantén el alcance DE/FR y los resultados sintéticos separados del control humano. Usa los recursos de HF/Kaggle cuando estén configurados y deja trazabilidad de cualquier bloqueo externo. No añadas fechas ni estimaciones de duración.
