# Sistema CTP Industrial Configurable + IA Local (SQLite + FastAPI)

Backend completo agnóstico al sector (preconfigurado con el caso Grupo Tatoma - Planta de Armentera) con soporte para:
- Base de datos relacional **SQLite** (`tatoma_ctp.db`) gestionada con SQLAlchemy 2.0.
- Flujo de trabajo (`workflow`), áreas y puestos 100% configurables (añadir, quitar o saltar fases como pintura o montaje).
- Motor matemático de planificación hacia atrás (Backward Scheduling), validación estricta de plazos previos (Lead Time), unidades por turno (`unitsPerShift`), vacaciones individuales y matriz de habilidades (`skills`).
- 5 Estrategias heurísticas con evaluación económica de subcontratación vs. horas extra.
- Integración con **IA Local (Ollama)** con fallback determinista automático si Ollama no está corriendo.
- Notificaciones en tiempo real mediante **WebSockets** (`/api/v1/ws/plant` y `/ws/plant`).

## Credenciales por defecto (Seed SQLite)
- **Administrador:** `usuario: admin` | `password: admin123`
- **Planificador:** `usuario: planner` | `password: planner123`
- **Visualizador:** `usuario: viewer` | `password: viewer123`
