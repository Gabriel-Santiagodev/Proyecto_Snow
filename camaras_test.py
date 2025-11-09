#ESTE ARCHIVO ES SOLO PARA PROBAR COMO LOS ERRORES DE LAS CAMARAS INTERACTUAN CON LA PANTALLA OLED, SE BORRARA DESPUES  

import logging
import ModulosGenerales.modulo_logging as modulo_logging 
import threading
import TareasSegundoPlano.oled_module as camara_menu
import time

modulo_logging.setup_logging()
Main_test = logging.getLogger("snow").getChild("camaras")

stop_event = threading.Event()

camara_thread = threading.Thread(
    target=camara_menu.run,
    name="CAMARA",
    args=(stop_event,),
    daemon=False
)
camara_thread.start()

while True:
    Main_test.error("Camara 1 apagada")
    time.sleep(1)

try: 
    camara_thread.join()
except KeyboardInterrupt:
    stop_event.set()
    camara_thread.join()




