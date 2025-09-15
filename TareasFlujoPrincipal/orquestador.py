import logging
import time
import ModulosGenerales.modulo_logging as modulo_logging 
from ultralytics import YOLO
from cameras_module import esta_trabajando,toma_frame
from TareasFlujoPrincipal.audio_module import AudioSystem
import cv2

model = YOLO("best.pt")  # modelo YOLO
roi_x1, roi_y1, roi_x2, roi_y2 = 320, 0, 640, 480   # Definir la zona de interés (x1, y1, x2, y2)


#Declaracion de variables
camara1 = cv2.VideoCapture(0)
camara2 = cv2.VideoCapture(1)

"""
from TareasFlujoPrincipal import cameras_module, yolo_module, audio_module, 
from TareasSegundoPlano import oled_module
"""
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
            if esta_trabajando:
                toma_frame(camara1, camara2, cola_frames)


                frame = cola_frames.get()  # Espera hasta que haya un frame disponible en la cola
                
                frame_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2] # Extraer el ROI (recorte del frame)

                frame_with_roi = frame.copy()   # La funcion copy realiza una copia de frame para evitar q al modificar alguno el otro se modifique
                cv2.rectangle(frame_with_roi, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 0), 2)


                results = model(frame_roi)                          # YOLO espera un array tipo imagen

                for box in results[0].boxes:    # Bucle de detecciones      results[0] indica la imagen actual      .boxes indica las bounding box
                    conf = float(box.conf[0])           # Guarda la confianza de las bounding box
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
