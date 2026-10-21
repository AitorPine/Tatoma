Qué hace

Plano de la nave: cada puesto muestra su nombre, los operarios, un punto de estado (verde activa, rojo parada, naranja mantenimiento) y una barra en perspectiva dividida por pedidos. La escala de la barra se ajusta al máximo de carga de la semana. La marca negra es la capacidad, y el borde pasa de verde a ámbar a partir del 80 % y a rojo por encima del 100 %.
Navegación semanal: con ◀ ▶ o con una tira de 36 semanas coloreada por ocupación, para ver de un vistazo qué semanas se complican.
Ajuste de capacidad: el botón «Ajustar capacidad» resta horas por vacaciones, bajas o averías en una semana y un área concretas.
Pedidos: el formulario evalúa un pedido nuevo. La soldadura se reparte en las semanas previas, la pintura en las dos anteriores y el montaje en la semana de entrega. Si no cabe, indica semana y área del cuello de botella. Propone retrasar la entrega, partir el lote o cubrir con horas extra, y el botón «Aplicar» recalcula al instante.
Administrador: «Editar plano» permite fijar columnas y filas de la nave, crear puestos pulsando «+» y editar cada uno (área, estado, operarios, turnos, horas por turno, tamaño). La pestaña «Equipo» añade trabajadores y los asigna a un puesto.
Planificador: puede gestionar pedidos y ajustar capacidad, pero no editar el plano.

Lo que falta

La importación directa del Excel.
Las vacaciones individuales por operario y las unidades por turno de pintura.
Las habilitaciones por línea de soldadura: ahora la carga se reparte entre las líneas de forma proporcional.
Los flujos de trabajo editables.
Los datos están solo en localStorage, sin backend.
Endpoints que necesita el backend

Prefijo /api/v1, con JWT en Authorization: Bearer.

Autenticación

POST /auth/login: devuelve el token y el usuario con su rol.
POST /auth/refresh y POST /auth/logout.
GET /me.

Usuarios y trabajadores (administrador)

GET/POST /users y PATCH/DELETE /users/:id, con el rol admin, planner o viewer.
GET/POST /workers y PATCH/DELETE /workers/:id, con puesto y habilidades.
PUT /workers/:id/absences: vacaciones y bajas por semanas.

Planta y puestos (administrador)

GET /plants/:id y PUT /plants/:id/layout, que guarda las dimensiones del grid y la posición de los puestos.
GET/POST /stations y PATCH/DELETE /stations/:id, con campos como area, x, y, w, h, workers, shifts, hoursPerShift, unitsPerShift y status.
PUT /stations/:id/skills: los trabajos que puede hacer cada línea.
GET/PUT /areas: las áreas.
GET/PUT /workflow: el flujo de fases, por ejemplo soldadura → pintura → montaje.

Capacidad y disponibilidad

GET /capacity?from=&to=: capacidad por semana, área y puesto.
GET/PUT /capacity/adjustments: ajustes por semana, área o puesto, con motivo (vacaciones, baja o averia).
PATCH /stations/:id/status: estado actual o programado.

Pedidos

GET/POST /orders y GET/PATCH/DELETE /orders/:id, con cantidad, entrega, horas por unidad, plazo previo y cliente.
POST /orders/import: sube el Excel y valida las filas.
POST /orders/:id/confirm.

Motor de cálculo

POST /simulations/evaluate: recibe un pedido borrador y devuelve la viabilidad, los conflictos con semana y área, y las sugerencias.
POST /simulations/apply: aplica una sugerencia elegida.

Visualización

GET /plant-status?week=2026-W08: estaciones con carga, capacidad, porcentaje y segmentos por pedido. Es lo que alimenta el plano, y conviene devolverlo ya calculado desde el servidor.
GET /heatmap?from=&to=: la tira semanal.
WS /ws/plant: avisos en tiempo real cuando cambia el estado de un puesto.