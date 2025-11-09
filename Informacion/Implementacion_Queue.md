# Guía de Implementación de la Cola de Frames

Este documento explica la actualización en `main.py` que introduce un sistema de cola (`queue`) para la comunicación entre módulos.

---

## Resumen del Cambio

Para permitir que los diferentes módulos (cámaras, YOLO, audio) se comuniquen de forma segura y eficiente, se ha implementado un sistema de **productor-consumidor** utilizando `queue.Queue`.

El archivo `main.py` ahora actúa como el orquestador principal:
1.  Crea una única instancia de `queue.Queue` llamada `cola_de_frames`.
2.  Pasa esta misma instancia a todos los módulos que la necesiten al momento de crear sus hilos (`threads`).



---

## ¿Cómo Implementarlo en tu Módulo? (Ejemplo para YOLO)

Para que tu módulo sea compatible con este nuevo sistema, solo necesitas seguir dos pasos.

### Paso 1: Modificar la Firma de la Función `run`

Tu módulo necesita ser capaz de **recibir** la cola que `main.py` le va a entregar. Para ello, añade un segundo argumento a tu función `run`.

**Antes:**
```python
def run(stop_event):
    # Tu código...
```

**Ahora:**
```python
def run(stop_event, cola_de_frames):
    # Tu código...
```

### Paso 2: Usar la Cola para Obtener Frames

Dentro de tu bucle `while`, utiliza el método `.get()` para extraer un frame de la cola. Este método esperará automáticamente si no hay frames disponibles, sincronizando tu módulo con el de las cámaras.

**Ejemplo de implementación en `yolo_module.py`:**
```python
import logging

def run(stop_event, cola_de_frames):
    """
    Función principal del módulo YOLO.
    Obtiene frames de la cola y los procesa.
    """
    yolo_logger = logging.getLogger("snow").getChild("yolo_module")
    yolo_logger.info("Módulo YOLO iniciado")

    while not stop_event.is_set():
        # Obtenemos un frame de la cola.
        # Si la cola está vacía, esta línea se detendrá y esperará.
        frame = cola_de_frames.get()

        # --- AQUI VA TU LÓGICA DE PROCESAMIENTO ---
        # Por ejemplo, pasar el 'frame' a tu modelo de YOLO.
        yolo_logger.debug(f"Procesando un nuevo frame...")
        # -------------------------------------------

    yolo_logger.info("Módulo YOLO detenido")

```

---

## Integración Final en `main.py`

Asegúrate de que al crear el hilo para tu módulo en `main.py`, le estés pasando la `cola_de_frames` en los argumentos (`args`).

```python
# Yolo thread
yolo_thread = threading.Thread(
    target=yolo_module.run,
    name="YOLO",
    # Asegúrate de pasar la cola aquí
    args=(stop_event, cola_de_frames,),
    daemon=False
)
yolo_thread.start()
```

Con estos cambios, tu módulo quedará perfectamente integrado en el flujo de trabajo del proyecto y comenzará a recibir los frames capturados por las cámaras.