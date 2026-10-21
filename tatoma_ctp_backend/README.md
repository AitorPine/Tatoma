# Sistema CTP Industrial Configurable + IA Local (SQLite + FastAPI)

Backend completo agnóstico al sector (preconfigurado con el caso Grupo Tatoma - Planta de Armentera) con soporte para:
- Base de datos relacional **SQLite** (`tatoma_ctp.db`) gestionada con SQLAlchemy 2.0.
- Flujo de trabajo (`workflow`), áreas y puestos 100% configurables (añadir, quitar o saltar fases como pintura o montaje).
- Motor matemático de planificación hacia atrás (Backward Scheduling), validación estricta de plazos previos (Lead Time), unidades por turno (`unitsPerShift`), vacaciones individuales y matriz de habilidades (`skills`).
- 5 Estrategias heurísticas con evaluación económica de subcontratación vs. horas extra.
- Integración con **IA Local (Ollama)** con fallback determinista automático si Ollama no está corriendo.
- Notificaciones en tiempo real mediante **WebSockets** (`/api/v1/ws/plant` y `/ws/plant`).

## Ejecución y despliegue

La instalación y ejecución con Uvicorn, las variables de entorno y las recomendaciones para acceso remoto están en el [README del repositorio](../README.md).

En desarrollo, el seed inicial usa `admin/admin123`, `planner/planner123` y `viewer/viewer123` por defecto. En producción, configura las variables `TATOMA_ADMIN_PASSWORD`, `TATOMA_PLANNER_PASSWORD` y `TATOMA_VIEWER_PASSWORD` antes de crear la base de datos. Esas contraseñas solo se usan al inicializar una base vacía.
