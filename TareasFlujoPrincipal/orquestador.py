import os
import logging
import time
import ModulosGenerales.modulo_logging as modulo_logging 
from ultralytics import YOLO
from TareasFlujoPrincipal.audio_module import AudioSystem
import cv2
import pygame
from config import THRESHOLD



#Configuracion del modelo YOLO
direccion_script = os.path.dirname(os.path.abspath(__file__))
camino_modelo = os.path.join(direccion_script, "best.pt")
modelo = YOLO(camino_modelo)  # modelo YOLO
roi_x1, roi_y1, roi_x2, roi_y2 = 320, 0, 640, 480   



#Configuracion del Logging
modulo_logging.setup_logging()
logger = logging.getLogger("snow").getChild("orchestrator")



def run(stop_event,cola_frames,cola_audio):

    """
    Orchestrator: coordina el flujo entre cámaras, YOLO
    y audio, con o sin tracking.
    """

    logger.info("Orquestador iniciado")
    while not stop_event.is_set():
        try:       
            frame = cola_frames.get()
            frame_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2] # Extraer el ROI (recorte del frame)
            frame_with_roi = frame.copy()   # La funcion copy realiza una copia de frame para evitar q al modificar alguno el otro se modifique
            cv2.rectangle(frame_with_roi, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 0), 2)

            results = modelo(frame_roi)

            for box in results[0].boxes:    # Bucle de detecciones      results[0] indica la imagen actual      .boxes indica las bounding box
                conf = float(box.conf[0])
                print(f"{conf*100:.2f}")           # Guarda la confianza de las bounding box
                if conf > 0.85:                     # si la conf es mayor a 84% reproduce un sonido y detiene el sistema hasta que termine este
                    logging.info(f"Clase detectada con {conf*100:.2f}% de confianza")
                    audio = AudioSystem(audio_file="audio.mp3")
                    if not cola_audio.empty():
                        señal = cola_audio.get()
                        if señal == "play_audio":
                            audio.activar_reproduccion
                    audio.gestionar_cola()
                    time.sleep(0.1)

                else:
                    time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error en el orquestador: {e}")
            
    logger.info("Orquestador detenido")
