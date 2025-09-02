
import time
from ModulosGenerales.error_buffer import get_recent_errors, get_dropped_errors_count
from config import ERROR_BUFFER_MAXLEN

def show_main_screen():
    print("\n[OLED] Proyecto SNOW - Sistema operativo activo\n")

def show_error_screen(errors: list[str], dropped: int):
    print("\n[OLED] ⚠️ Errores recientes:")
    for err in errors:
        print(f" - {err}")
    if dropped > 0:
        print(f" [+E] {dropped} errores más no mostrados")

def run(stop_event):
    """
    Simula la pantalla OLED. Se ejecuta en un hilo separado.
    Muestra los últimos errores si existen, o una pantalla principal si no.
    """
    while not stop_event.is_set():
        errors = get_recent_errors()
        dropped = get_dropped_errors_count()

        if errors:
            show_error_screen(errors, dropped)
        else:
            show_main_screen()

        time.sleep(0.5)  # refresco cada medio segundo