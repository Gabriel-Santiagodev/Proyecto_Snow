import logging
import time
import ModulosGenerales.modulo_logging as modulo_logging 
from ultralytics import YOLO
from cameras_module import esta_trabajando,toma_frame
import cv2

#Declaracion de variables
camara1 = cv2.VideoCapture(0)
camara2 = cv2.VideoCapture(1)

"""
from TareasFlujoPrincipal import cameras_module, yolo_module, audio_module, 
from TareasSegundoPlano import oled_module
"""
modulo_logging.setup_logging()
logger = logging.getLogger("snow").getChild("orchestrator")

def run(stop_event,cola_frames):

    
    """
    Orchestrator: coordina el flujo entre cámaras, YOLO
    y audio, con o sin tracking.
    """

    logger.info("Orquestador iniciado")

    while not stop_event.is_set():
        try:
            if esta_trabajando:
                logger.info("Module 'cameras_module' started")
                toma_frame(camara1, camara2, cola_frames)
            else:
                time.sleep(2)

        except Exception as e:
            logger.error(f"Error en el orquestador: {e}")
            
    logger.info("Orquestador detenido")
