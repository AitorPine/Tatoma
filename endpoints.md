API Reference - Tatoma Manufacturing Planner

Base URL: /api/v1

Autenticación: JWT Bearer Token (Authorization: Bearer <token>)

1. Autenticación

POST /auth/login

Body: { "email": "...", "password": "..." }

Response (200): Devuelve JWT y objeto de usuario { "token": "...", "user": { "id": 1, "role": "admin" } }

POST /auth/refresh

Response (200): Nuevo JWT.

POST /auth/logout

Response (200): Invalida sesión actual.

GET /me

Response (200): Datos del usuario autenticado.

2. Usuarios y Trabajadores (Admin / Planner)

GET /users | POST /users

Gestión de usuarios del sistema. Roles: admin, planner, viewer.

PATCH /users/:id | DELETE /users/:id

GET /workers | POST /workers

Gestión de operarios físicos en planta.

Atributos clave: name, station_id (puesto asignado), skills (ej. ["tig_welding", "mig_welding"]).

PATCH /workers/:id | DELETE /workers/:id

PUT /workers/:id/absences

Descripción: Configura vacaciones y bajas por semanas (afecta al recálculo de capacidad).

Body: [ { "week": "2026-W08", "type": "vacation|sick_leave" } ]

3. Planta, Áreas y Puestos (Estaciones)

GET /plants/:id

Devuelve configuración general de la planta.

PUT /plants/:id/layout

Body: { "grid": { "cols": 20, "rows": 15 }, "stations_layout": [ { "station_id": 1, "x": 2, "y": 4 } ] }

GET /stations | POST /stations

Body (POST): { "name": "Soldadura 1", "area": "soldadura", "x": 0, "y": 0, "w": 2, "h": 2, "workers": 2, "shifts": 1, "hoursPerShift": 8, "unitsPerShift": null, "status": "active" }

PATCH /stations/:id | DELETE /stations/:id

PUT /stations/:id/skills

Body: { "allowed_skills": ["heavy_welding"] } (Para restringir qué trabajos entran en esta línea).

GET /areas | PUT /areas

Gestiona las áreas principales (soldadura, pintura, montaje).

GET /workflow | PUT /workflow

Secuencia lógica de producción (ej. soldadura -> pintura -> montaje).

4. Capacidad y Disponibilidad

GET /capacity

Query: ?from=2026-W01&to=2026-W10

Response: Capacidad total y disponible por semana, área y puesto.

GET /capacity/adjustments | PUT /capacity/adjustments

Body (PUT): { "target_type": "station", "target_id": 1, "week": "2026-W08", "hours_deducted": 16, "reason": "breakdown" }

PATCH /stations/:id/status

Body: { "status": "active|stopped|maintenance" } (Actualiza el punto de estado en el plano).

5. Pedidos (Órdenes de Fabricación)

GET /orders | POST /orders

Body (POST): { "client": "...", "project": "...", "quantity": 10, "delivery_week": "2026-W12", "lead_time_weeks": 2, "hours_per_unit": { "welding": 4, "painting": 1, "assembly": 2 } }

GET /orders/:id | PATCH /orders/:id | DELETE /orders/:id

POST /orders/import

Content-Type: multipart/form-data (Excel).

Response (202): Devuelve un pre-análisis de las filas importadas (validando "serie" y "restante") antes de confirmar.

POST /orders/:id/confirm

Fija el pedido en el calendario y resta la capacidad oficialmente.

6. Motor de Cálculo y Simulación

POST /simulations/evaluate

Descripción: Evalúa un borrador de pedido mediante "backwards scheduling" respetando plazos previos.

Response:

{
  "is_viable": false,
  "bottlenecks": [
    { "week": "2026-W10", "area": "soldadura", "missing_hours": 24 }
  ],
  "suggestions": [
    { "id": "sug-1", "type": "delay", "proposed_delivery_week": "2026-W13" },
    { "id": "sug-2", "type": "overtime", "area": "soldadura", "week": "2026-W10", "extra_hours_needed": 24 }
  ]
}


POST /simulations/apply

Body: { "suggestion_id": "sug-2", "order_data": {...} }

7. Visualización y Monitorización (CORE UI)

Nota para Backend: Estos endpoints son críticos de rendimiento. El servidor debe consolidar la información para que el frontend (Navegador/React/Vue) no haga cruces de arrays pesados.

GET /plant-status

Query: ?week=2026-W08

Descripción: Alimenta el plano interactivo. Devuelve el estado exacto de cada puesto para pintar su barra de capacidad y porcentaje.

Response:

[
  {
    "station_id": 1,
    "name": "Línea Soldadura 1",
    "status": "active",
    "metrics": {
      "capacity_hours": 80,
      "loaded_hours": 75,
      "occupancy_percentage": 93.75, 
      "alert_level": "amber" // green (<80%), amber (80-99%), red (>=100%)
    },
    "order_segments": [
      { "order_id": 101, "client": "Cliente A", "hours": 40, "color": "#3498db" },
      { "order_id": 105, "client": "Cliente B", "hours": 35, "color": "#e74c3c" }
    ]
  }
]


GET /heatmap

Query: ?from=2026-W01&to=2026-W36

Descripción: Alimenta la tira inferior de navegación.

Response:

[
  { "week": "2026-W01", "global_occupancy": 65.5, "status": "green" },
  { "week": "2026-W08", "global_occupancy": 105.0, "status": "red" }
]


WS /ws/plant

Eventos emitidos: STATION_STATUS_CHANGED, CAPACITY_UPDATED, NEW_ORDER_CONFIRMED.

Payload: Envía deltas (cambios) para actualizar el dashboard en tiempo real sin recargar.