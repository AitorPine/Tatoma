# API · Tatoma Manufacturing Planner

Base: `/api/v1`. Todas las rutas HTTP, salvo el login, requieren `Authorization: Bearer <access_token>`. Los roles son `admin`, `planner` y `viewer`; las operaciones de escritura aplican controles de rol en el servidor.

## Autenticación

- `POST /auth/login`: `{"username":"admin","password":"…"}`. Devuelve `access_token`, `refresh_token`, `token_type` y `user`.
- `POST /auth/refresh`: requiere el token de renovación en el encabezado Bearer; devuelve un nuevo par de tokens.
- `POST /auth/logout`: revoca el token de acceso actual en el proceso del servidor.
- `GET /me` o `GET /auth/me`: usuario autenticado.

## Usuarios, operarios y planta

- `/users`: `GET`, `POST`; `/users/{id}`: `PATCH`, `DELETE`. Administración restringida a `admin`.
- `/workers`: `GET`, `POST`; `/workers/{id}`: `PATCH`, `DELETE`; `/workers/{id}/absences`: `PUT` con `{"absences":[{"week":"2026-W08","hours":16,"reason":"vacaciones"}]}`. Creación/modificación/borrado de trabajadores requiere `admin`; las ausencias permiten `admin` y `planner`.
- `GET /plants/{id}` devuelve `cols`, `rows` y puestos; `PUT /plants/{id}/layout` recibe `{"cols":20,"rows":15,"positions":[{"id":"P1","x":2,"y":4,"w":2,"h":2}]}`.
- `/stations`: `GET`, `POST`; `/stations/{id}`: `PATCH`, `DELETE`; `/stations/{id}/skills`: `PUT` con `{"skills":["heavy_welding"]}`; `/stations/{id}/status`: `PATCH` con estado `active`, `stopped` o `maintenance`.
- `/areas`: `GET`, `PUT` (admin). `/workflow`: `GET`, `PUT` (admin), con pasos `{step_order, area_id, name, offset_weeks_before_delivery, is_optional}`.

## Capacidad y pedidos

- `GET /capacity?from=2026-W01&to=2026-W10` devuelve semanas con capacidad, carga comprometida y métricas por puesto.
- `GET /capacity/adjustments` devuelve `{week, area, station_id, hours_delta, reason}`. `PUT` recibe `{"adjustments":[...]}`; un delta negativo reduce capacidad y uno positivo añade horas.
- `/orders`: `GET`, `POST`; `/orders/{id}`: `GET`, `PATCH`, `DELETE`; `/orders/{id}/confirm`: `POST`.
- Un pedido usa `code`, `client`, `quantity`, `current_week`, `delivery_week`, `lead_time_weeks`, `required_skill`, `hours_per_unit` (por ejemplo `{"soldadura":4,"pintura":1,"montaje":2}`), `active_phases` y `status`.
- `POST /orders/import` acepta CSV o XLSX y actualmente importa las filas directamente; no implementa una previsualización/confirmación previa.

## Simulación y ocupación

- `POST /simulations/evaluate` recibe un pedido y devuelve `viable`, `lead_time_ok`, `conflicts`, asignaciones base, estrategias y recomendación del asesor local.
- `POST /simulations/apply` recibe `{order, selected_strategy_code, allocations, capacity_adjustments_to_create, final_delivery_week}` y guarda la estrategia seleccionada.
- `GET /plant-status?week=2026-W08` devuelve `{week, bar_scale_max_hours, stations}` con capacidad, carga, ocupación, estado y segmentos por puesto.
- `GET /heatmap?from=2026-W01&to=2026-W36` devuelve métricas semanales agregadas.
- `WS /api/v1/ws/plant` emite eventos de cambios de puesto, ajustes, pedidos y simulaciones.
- `GET /health` verifica el servidor. `/docs` ofrece OpenAPI.