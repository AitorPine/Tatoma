# Tatoma — explicación completa del proyecto

## Para qué sirve este documento

Este documento reúne el contexto funcional y técnico de Tatoma para que una IA pueda utilizarlo como base al preparar una presentación de PowerPoint, un guion de exposición o una explicación del proyecto. La presentación debe basarse en el funcionamiento real descrito aquí y, cuando sea necesario, contrastarlo con el código y la documentación del repositorio.

No hay que inventar funcionalidades, resultados, ahorros o garantías. Conviene distinguir entre lo que la aplicación ya hace, lo que se puede configurar y cualquier idea de mejora que todavía no esté implementada.

## 1. Resumen del proyecto

Tatoma es una aplicación web para planificar la producción de una planta industrial. Su objetivo es ofrecer una visión semanal de los pedidos y de la capacidad de las áreas de producción, y servir de apoyo cuando se necesita decidir si un pedido nuevo puede aceptarse y con qué fecha o condiciones.

El flujo industrial de ejemplo contempla tres áreas:

1. **Soldadura**
2. **Pintura**
3. **Montaje**

Cada pedido puede requerir una o varias de estas fases, distintas horas de trabajo por unidad y una cantidad determinada de unidades. El sistema utiliza esos datos, la fecha de entrega deseada y la disponibilidad de los puestos para estimar la carga de trabajo y detectar posibles conflictos.

La aplicación combina cuatro piezas:

- una interfaz visual para consultar el plano y la ocupación de la planta;
- una API que gestiona pedidos, recursos, usuarios y simulaciones;
- un motor determinista que calcula carga, capacidad, asignaciones y conflictos;
- una recomendación en lenguaje natural que puede utilizar una IA local, con una alternativa heurística cuando el servicio de IA no está disponible.

La IA no sustituye al motor de planificación: los cálculos de capacidad y viabilidad los realiza el backend.

## 2. El problema que aborda

En una fábrica no basta con saber cuántas horas requiere un pedido en total. También importa **en qué fase** se necesitan esas horas, **en qué semana** deben realizarse, qué puestos pueden hacer el trabajo y qué carga ya se ha comprometido.

Por ejemplo, puede haber horas suficientes sumando toda la fábrica y, aun así, no tener disponibilidad en pintura en la semana necesaria. También puede existir capacidad en soldadura, pero no en una línea compatible con la habilidad requerida. Las ausencias, una avería o un puesto en mantenimiento pueden reducir todavía más la capacidad útil.

La aplicación convierte esta planificación en una pregunta concreta: dadas las características del pedido, el calendario y los recursos configurados, ¿se puede planificar el trabajo? Si no, ¿dónde aparece el conflicto y qué alternativas se pueden estudiar?

El Excel `PLANIFICACIÓN COMERCIAL.xlsx` es una referencia con pedidos y planificación semanal de 2026. Puede servir como ejemplo de la clase de información comercial que se quiere organizar. Sus cifras no deben presentarse como resultados del motor sin haber comprobado cómo se importaron, distribuyeron y calcularon.

## 3. Conceptos fundamentales

### Pedido

Un pedido u orden de fabricación contiene, entre otros, los siguientes datos:

- código identificador;
- cliente;
- cantidad de unidades;
- semana actual o de referencia;
- semana de entrega solicitada;
- plazo previo, expresado en semanas;
- habilidad técnica requerida;
- horas necesarias por unidad en cada área;
- fases activas;
- estado del pedido.

La carga de una fase se estima multiplicando la cantidad por las horas por unidad de esa fase. Por ejemplo, si un pedido de 10 unidades requiere 2 horas de soldadura por unidad, representa 20 horas de trabajo de soldadura.

### Semana

El backend expresa semanas en formato ISO `AAAA-WNN`, por ejemplo `2026-W08`. El calendario y las funciones de comparación permiten tratar cambios de año al calcular semanas anteriores o posteriores.

### Fase y flujo de trabajo

El flujo de trabajo define las fases, su orden y cuántas semanas antes de la entrega se programa cada una. En la configuración inicial:

- soldadura se planifica 2 semanas antes de la entrega;
- pintura se planifica 1 semana antes;
- montaje se planifica en la semana de entrega.

El administrador puede cambiar la secuencia, los nombres, el área asociada y el desfase semanal. Un pedido puede indicar qué fases tiene activas; las horas unitarias mayores que cero determinan si hay trabajo asociado a una fase.

### Puesto, área y habilidad

- Un **área** representa una etapa o zona productiva, como soldadura.
- Un **puesto** es un recurso productivo concreto de un área, como la línea P1 o la cabina de pintura.
- Una **habilidad** limita qué puestos pueden realizar determinados pedidos. Los puestos con habilidad `general` pueden actuar como puestos genéricos; también se admiten habilidades específicas.

## 4. Cómo funciona la evaluación de un pedido

De forma simplificada, al evaluar un pedido la aplicación realiza estos pasos:

1. Recibe los datos del pedido: cantidad, entrega, plazo previo, áreas, horas por unidad y habilidad.
2. Obtiene el flujo de trabajo activo y calcula en qué semana se planifica cada fase. El desfase configurado se resta a la semana de entrega.
3. Calcula la primera semana posible de inicio a partir de la semana actual y el plazo previo.
4. Calcula las horas requeridas por fase como `cantidad × horas por unidad`.
5. Busca puestos activos y compatibles con el área y la habilidad requerida.
6. Calcula la capacidad disponible de esos puestos para la semana de la fase.
7. Resta la carga que ya está comprometida y comprueba también posibles límites de unidades por turno.
8. Si falta capacidad, registra el conflicto con semana, área, horas requeridas, horas disponibles y sobrecarga estimada.
9. Si el plan base es viable, reparte la carga entre los puestos compatibles según la holgura disponible.
10. Genera estrategias alternativas y solicita una recomendación al componente de IA local o al fallback.

El resultado de evaluación incluye si el plan base es viable, si respeta el plazo previo, los conflictos encontrados, las asignaciones previstas, las estrategias propuestas y la recomendación del asesor.

Evaluar un pedido no significa que se haya aceptado. La interfaz presenta una acción separada para aceptar el pedido cuando el plan base es viable, o para aplicar una estrategia viable si se elige una alternativa. La aplicación vuelve a cargar los datos tras esas operaciones.

## 5. Cómo calcula el sistema la capacidad

### Capacidad horaria de los puestos

La capacidad horaria base semanal de un puesto se obtiene a partir de:

`número de operarios × turnos × horas por turno × 5 días laborables`

Después se ajusta con las horas de ausencia registradas para los trabajadores asignados y con los ajustes de capacidad de la semana. Un puesto que no esté activo tiene capacidad cero.

Los ajustes se pueden asociar a un puesto o a un área. Entre sus motivos se contemplan situaciones como averías, vacaciones, bajas y horas extra. Un ajuste positivo aumenta las horas disponibles y uno negativo las reduce.

### Límite de unidades

Algunos puestos también tienen un máximo de unidades por turno. La configuración inicial de ejemplo incluye una capacidad orientativa en la cabina de pintura. En esos puestos no basta con comprobar las horas: el motor también comprueba si las unidades comprometidas más las del nuevo pedido superan el límite calculado.

### Carga ya comprometida

El motor consulta las asignaciones de producción ya guardadas para cada puesto y semana. En la evaluación base compara las horas necesarias para el pedido nuevo con las horas libres en los puestos compatibles. Las asignaciones externas/subcontratadas no se consideran carga interna del puesto.

### Ocupación visual

La interfaz representa la relación entre carga y capacidad. En el plano, los colores indican:

- **Verde:** menos del 80 % de ocupación;
- **Ámbar:** desde el 80 % hasta menos del 100 %;
- **Rojo:** 100 % o más.

La vista permite cambiar de semana y consultar métricas agregadas y por puesto. La barra de cada puesto representa pedidos asignados y muestra una marca de referencia para la capacidad.

## 6. Estrategias que puede proponer el motor

Cuando el plan base no encaja, el motor genera cinco tipos de estrategia. Su viabilidad depende de los datos y la capacidad configurada; una propuesta no debe describirse como garantizada sin revisar el resultado concreto de la simulación.

1. **Redistribuir entre puestos compatibles.** Comprueba el reparto del trabajo entre líneas activas con la habilidad necesaria, sin coste adicional, para la misma fecha.
2. **Partir el lote y nivelar la producción.** Busca huecos en semanas anteriores y distribuye el trabajo hacia atrás, respetando la fecha más temprana permitida por el plazo previo.
3. **Añadir horas extra o turnos.** Estima las horas de capacidad adicionales necesarias en las semanas y áreas afectadas, y calcula el coste con la tarifa de horas extra configurada.
4. **Subcontratar parte de una fase.** Mantiene internamente la parte que cabe y asigna el excedente a un proveedor externo. Estima el coste variable y el coste logístico configurados por área, y compara el resultado con la alternativa de horas extra.
5. **Retrasar la entrega.** Busca una fecha posterior que permita planificar el pedido con la capacidad ordinaria. El motor prueba fechas futuras hasta un máximo de 24 semanas y propone la primera que resulte viable mediante la evaluación base.

Las estrategias y sus asignaciones se devuelven al cliente. El usuario con permisos de planificación puede aplicar una alternativa; la operación guarda el pedido, las asignaciones y, cuando corresponda, los ajustes de capacidad asociados.

## 7. La IA local y su función

La integración de IA se encuentra en el backend, en el servicio de recomendación local. Si hay conflictos, el backend proporciona a Ollama un resumen estructurado del pedido, los conflictos y las estrategias viables. El servicio configurado utiliza el modelo `qwen2.5:7b-instruct` en `http://localhost:11434/api/chat`.

La respuesta de la IA se utiliza para generar una síntesis, una explicación económica y una valoración de riesgo. Si Ollama no responde o no está disponible, el código contempla un fallback heurístico que selecciona una alternativa según las opciones disponibles y comunica el criterio de coste o impacto.

Es importante explicar con precisión los límites:

- La IA **no decide por sí sola** la capacidad física ni valida el plan industrial.
- El motor matemático produce los conflictos, asignaciones y estrategias; la IA ayuda a explicar y recomendar entre los resultados recibidos.
- La recomendación depende de las alternativas que el motor haya calculado y de la configuración económica de áreas.
- Cuando el pedido no tiene conflictos, se genera una respuesta determinista indicando aceptación sin coste adicional.
- El uso de Ollama es local según la URL configurada; para generar la recomendación hace falta tener el servicio local disponible. El fallback permite que el flujo de evaluación responda también cuando Ollama no está ejecutándose.

## 8. Qué puede gestionar cada usuario

El sistema define tres roles:

- **admin:** administra usuarios y la configuración estructural de planta, como flujo de trabajo y otros parámetros restringidos a administración.
- **planner:** consulta la planta y puede realizar operaciones de planificación, como gestionar pedidos y aplicar ajustes permitidos.
- **viewer:** consulta la información sin los permisos de escritura asignados a administrador o planificador.

La API aplica los permisos en el servidor; no dependen únicamente de ocultar botones en la interfaz. Las credenciales iniciales de desarrollo están documentadas en el README. En despliegues, se deben configurar contraseñas seguras y la clave secreta de la aplicación.

## 9. Interfaz de usuario

Tras iniciar sesión, el frontend ofrece varias vistas:

### Plano

Muestra el diseño de la planta como una cuadrícula con puestos colocados en posiciones y tamaños determinados. Cada puesto presenta su área, estado, número de operarios, horas de carga, capacidad y ocupación. Es posible recorrer semanas; la edición del plano y de los puestos está restringida a administración.

En las opciones de configuración de un puesto se contemplan nombre, área, estado, trabajadores, turnos, horas por turno, turnos máximos, unidades por turno, habilidades y tamaño/posición visual.

### Pedidos

Muestra pedidos guardados y permite evaluar uno nuevo con código, cliente, cantidad, semana de entrega, horas por unidad para las áreas y plazo previo. El resultado presenta viabilidad, conflictos, estrategias y, si hay conflictos, la explicación del asesor. Según el rol y el resultado, se pueden aceptar pedidos, aplicar estrategias o eliminar pedidos.

### Equipo

Permite consultar operarios, puesto asociado, habilidades y ausencias. Los permisos del backend limitan quién puede crear, editar o eliminar trabajadores; la gestión de ausencias tiene sus propios permisos de escritura.

### Flujo

Permite a administración cambiar el orden de las fases, su área, el desfase en semanas, el carácter opcional, añadir o quitar pasos y restaurar el flujo inicial.

## 10. Importación de pedidos

El backend incluye un endpoint de importación protegido por permisos de planificación. Admite archivos CSV y Excel. El formato de importación genérico contempla columnas para código, cliente, cantidad, semana de entrega, plazo previo, habilidad y horas unitarias por área.

También hay lógica para interpretar el formato de planificación comercial, que puede identificar cabeceras de pedidos y columnas de semanas, convertir los marcadores semanales reconocidos en cantidades y crear pedidos semanales independientes. Si una fila o un marcador no es válido, la respuesta puede incluir errores para revisar. En la importación comercial se usan los datos de línea de producción cuando se pueden identificar líneas de soldadura concretas.

Al presentar esta funcionalidad, conviene mostrar la plantilla/formato realmente utilizado y el resultado de una importación de prueba. No se debe asumir que cualquier Excel arbitrario será reconocido ni que la importación sustituye a una validación comercial manual.

## 11. Arquitectura técnica

### Frontend

- Implementado con HTML, CSS y JavaScript.
- No requiere un servidor frontend independiente en el despliegue normal.
- Los archivos están en `planta/`.
- `index.html` carga configuración, cliente de API, estado, métricas, autenticación y vistas.
- Las vistas están separadas para plano, pedidos, equipo y flujo.
- El frontend consulta el backend para la información persistente y recibe cambios mediante WebSocket.

### Backend

- Python y FastAPI.
- La API principal está bajo el prefijo `/api/v1`.
- SQLAlchemy gestiona el acceso relacional a los datos.
- Pydantic define y valida los esquemas de entrada y salida.
- JWT se utiliza para las sesiones autenticadas.
- El módulo `main.py` coordina rutas, validaciones, persistencia, simulaciones y WebSockets.

### Motor de planificación

`tatoma_ctp_backend/app/services/engine.py` contiene la lógica de capacidad y planificación: encuentra las fases activas, calcula el inicio más temprano, compara la demanda con la holgura de puestos compatibles, registra conflictos, asigna horas y prepara estrategias.

### Asesor de IA

`tatoma_ctp_backend/app/services/ai_local.py` implementa la consulta a Ollama y la respuesta heurística alternativa.

### Persistencia

- SQLite almacena pedidos, asignaciones, puestos, trabajadores, áreas, flujo, usuarios y ajustes.
- La base de desarrollo se encuentra en `tatoma_ctp_backend/tatoma_ctp.db`.
- La ruta SQLite es relativa al directorio desde el que se inicia el proceso; al ejecutar Uvicorn desde `tatoma_ctp_backend`, la base se crea allí.

### Actualizaciones en tiempo real

El backend expone un WebSocket de planta. El frontend vuelve a cargar la información cuando recibe notificaciones para mantener la vista sincronizada con cambios en pedidos, puestos, ajustes y simulaciones.

### Despliegue

Uvicorn ejecuta FastAPI, que sirve tanto la API como los archivos de la aplicación web en un mismo origen. El README describe la instalación, el arranque con Uvicorn y la configuración para acceso remoto. Para acceso externo se recomienda HTTPS delante del servicio y configurar correctamente el proxy para WebSockets.

## 12. Datos iniciales de ejemplo

Al iniciar una base vacía, la función de seed configura una planta de ejemplo llamada Armentera, con:

- 7 puestos de soldadura (P1–P7), con distintas habilidades y estados;
- 1 puesto/cabina de pintura con unidades por turno configuradas;
- 2 puestos de montaje (M1–M2);
- trabajadores de ejemplo y una ausencia registrada;
- tres áreas con tarifas de coste ordinario, horas extra y subcontratación;
- flujo inicial con los desfases de soldadura, pintura y montaje;
- algunos pedidos y asignaciones para que se pueda visualizar carga desde el arranque.

Esta información permite explorar la aplicación en desarrollo. Debe presentarse como configuración de demostración, no como una descripción garantizada de la situación productiva actual de la empresa.

## 13. Cómo ejecutar y demostrar el proyecto

La ruta recomendada de demostración es:

1. Iniciar la aplicación siguiendo el README y entrar con un usuario autorizado.
2. Mostrar el plano y explicar una semana, un puesto, su capacidad, carga y estado.
3. Cambiar de semana para explicar cómo cambia la ocupación.
4. Abrir pedidos y evaluar un caso concreto, mostrando los datos de entrada.
5. Si es viable, explicar por qué cabe y aceptar el pedido solo si se desea demostrar persistencia.
6. Si no es viable, señalar el conflicto exacto y comparar las estrategias que el motor marcó como viables.
7. Aplicar una estrategia de prueba solo si se desea modificar los datos; explicar su efecto en la planificación.
8. Mostrar el equipo, una ausencia y el flujo de fases para ilustrar qué parámetros alimentan el cálculo.
9. Explicar la diferencia entre resultado determinista y recomendación en lenguaje natural.

Antes de exponer, conviene elegir un caso pequeño, comprobar que los datos de inicio son reproducibles y evitar aplicar cambios en una base compartida o productiva.

## 14. Guion orientativo para una presentación

Este guion organiza la explicación del proyecto; se puede adaptar al tiempo disponible:

1. **Título y propósito:** aplicación de planificación de producción y visibilidad de capacidad.
2. **Problema operativo:** pedidos con distintas cantidades y plazos compiten por recursos y semanas.
3. **Idea de la solución:** centralizar pedidos, capacidad, restricciones y calendario en un plan visual.
4. **Datos de entrada:** explicar pedido, fases, horas por unidad, fecha, plazo previo y habilidades.
5. **Recursos productivos:** enseñar áreas, puestos, turnos, operarios, habilidades y ausencias.
6. **Cálculo:** explicar la demanda por fase y cómo el motor la compara con capacidad libre y carga comprometida.
7. **Demostración de viabilidad:** presentar un pedido que cabe en el plan y cómo se representa.
8. **Demostración de conflicto:** presentar un cuello de botella y localizarlo por semana y área.
9. **Alternativas:** explicar nivelado, horas extra, subcontratación y cambio de fecha; mostrar los costes estimados cuando estén disponibles.
10. **Visualización de planta:** explicar plano, ocupación semanal y umbrales de color.
11. **IA local:** explicar que ayuda a redactar/recomendar sobre alternativas ya calculadas, con fallback.
12. **Arquitectura y cierre:** resumir frontend, API, motor, SQLite y posibles adaptaciones mediante configuración.

Prioriza una historia clara: **datos del pedido → cálculo de carga → detección del conflicto o viabilidad → alternativas → decisión informada**.

## 15. Aspectos que conviene explicar con rigor

- La viabilidad se calcula sobre los datos y la configuración existentes; una configuración incompleta puede producir resultados que no representen la operación real.
- El flujo inicial es configurable, pero la interfaz de pedidos y el ejemplo visual están centrados en soldadura, pintura y montaje. No presentes la aplicación como un planificador universal de cualquier proceso sin validar esa adaptación.
- El motor comprueba semanas, horas, puestos compatibles y, cuando está configurado, límites de unidades. No afirmes que optimiza automáticamente todos los objetivos de producción posibles.
- Los importes de horas extra y subcontratación dependen de tarifas configuradas y son estimaciones del sistema, no ofertas de proveedores ni costes contables certificados.
- Una recomendación del modelo local no es una aprobación automática del pedido ni reemplaza la decisión de planificación.
- Los datos sembrados son ejemplos de desarrollo. Para hablar de resultados reales hay que cargar datos válidos y comprobar el plan resultante.
- Diferencia una simulación de un pedido guardado, confirmado o aplicado: son pasos distintos en la interfaz y en la API.

## 16. Archivos principales del repositorio

- `README.md`: requisitos, desarrollo local y despliegue.
- `docs/requisitos.md`: requisitos funcionales del sistema.
- `docs/endpoints.md`: resumen de rutas y contratos de la API.
- `planta/index.html`: entrada de la interfaz.
- `planta/css/styles.css`: estilos de la interfaz.
- `planta/js/api.js`: comunicación con el backend.
- `planta/js/state.js`: carga y estado de la sesión de interfaz.
- `planta/js/engine.js`: métricas y cálculos auxiliares presentados en el frontend.
- `planta/js/views/planta.js`: vista del plano y controles de capacidad.
- `planta/js/views/pedidos.js`: pedidos y evaluación de simulaciones.
- `planta/js/views/equipo.js`: vista de operarios y ausencias.
- `planta/js/views/flujo.js`: configuración del flujo.
- `tatoma_ctp_backend/app/main.py`: API, rutas y coordinación del backend.
- `tatoma_ctp_backend/app/models.py`: entidades persistidas.
- `tatoma_ctp_backend/app/schemas.py`: modelos de entrada/salida.
- `tatoma_ctp_backend/app/seed.py`: datos iniciales de ejemplo.
- `tatoma_ctp_backend/app/services/engine.py`: motor industrial de planificación.
- `tatoma_ctp_backend/app/services/ai_local.py`: recomendación con IA local y fallback.
- `tatoma_ctp_backend/app/utils_weeks.py`: utilidades de calendario semanal.
- `tatoma_ctp_backend/requirements.txt`: dependencias de Python, incluido Uvicorn.
- `README.md`: instalación, arranque con Uvicorn y configuración para acceso remoto.
- `PLANIFICACIÓN COMERCIAL.xlsx`: referencia comercial de planificación.

## Instrucciones para la IA que prepare la presentación

- Usa este documento como contexto y revisa el código o la documentación cuando necesites confirmar un detalle.
- Explica el proyecto en español claro, definiendo los términos industriales y técnicos antes de utilizarlos.
- Dedica la mayor parte de la presentación a qué problema resuelve, qué datos utiliza, cómo funciona el cálculo y qué ve o decide el usuario.
- No conviertas la presentación en una lista de tecnologías: relaciona cada componente con su función en la solución.
- Cuando describas IA, deja claro qué aporta y qué parte sigue siendo determinista.
- Usa ejemplos y cifras solo si puedes rastrear su origen y verificar el resultado.
- Separa las capacidades existentes de las propuestas futuras y evita atribuir al sistema resultados empresariales no medidos.
- Si falta información para una afirmación o una diapositiva, indícalo como dato pendiente de confirmar en vez de inventarlo.
