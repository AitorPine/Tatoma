Los requisitos funcionales de la aplicación, combinando la visión del problema de la empresa y la simulación de capacidad necesaria, se dividen en cuatro bloques principales:

**1. Gestión de Pedidos y Tiempos de Producción**

* **Ingreso de proyectos/pedidos:** Registrar la cantidad a fabricar, la fecha de entrega solicitada y las horas de operario por unidad requeridas en cada fase: soldadura, pintura y montaje.


* **Gestión de plazos previos:** Permitir la introducción de un tiempo de aprovisionamiento, preparación de materias primas y diseño, garantizando que la soldadura no se planifique antes de que este plazo finalice.


* **Distribución temporal:** Posicionar la carga de soldadura y pintura en las semanas previas a la fecha de entrega, y la carga de montaje en la misma semana de entrega solicitada.



**2. Configuración de Recursos y Trabajadores**

* **Definición de puestos e infraestructura:** Configurar el número de zonas, operarios por puesto, turnos disponibles y las horas por turno. Incluye establecer la capacidad orientativa en la línea de pintura (ej. 32 unidades por turno). Todos los parámetros deben ser modificables.


* **Gestión de disponibilidad y calendario:** Ajustar la capacidad disponible en semanas concretas para reflejar vacaciones elegidas de forma individual, bajas médicas o averías en la maquinaria.


* **Restricciones de habilidades por puesto:** Asignar qué líneas específicas de producción (de las 7 de soldadura disponibles) están habilitadas para realizar determinados trabajos, limitando el cálculo de capacidad a los operarios cualificados para esa tarea.



**3. Motor de Cálculo y Detección de Cuellos de Botella (Problema Principal)**

* **Evaluación de aceptación:** Calcular de forma automática, semana a semana, si un nuevo pedido puede ser aceptado al comparar su carga con la capacidad libre y los proyectos ya comprometidos.


* **Identificación del conflicto:** Si un pedido no es viable, el sistema debe señalar exactamente en qué semana y en qué área de la fábrica (soldadura, pintura o montaje) se produce el cuello de botella.


* **Simulación de soluciones (Funcionalidad avanzada):** Cuando un pedido no encaja, el asistente debe proponer automáticamente sugerencias de modificación o ajustes para mejorar la situación y hacer viable la entrega, como la reorganización de la carga.



**4. Visualización y Monitorización (Plano y Ocupación)**

* **Mapa de estado visual:** Mostrar un mapa gráfico por zonas de trabajo (soldadura, pintura y montaje) que funcione mediante un código de colores.


* **Niveles de ocupación térmicos:** Diferenciar visualmente las áreas con capacidad disponible, las que están próximas al límite (a partir del 80% de ocupación) y las que están sobrecargadas.


* **Consulta temporal:** Permitir la navegación de esta visualización semana a semana para anticipar el estado de la planta de un solo vistazo.