import time
import threading
from ultralytics import YOLO
import cv2
import pygame
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='SADA_logging.log', encoding='utf-8', level=logging.DEBUG,     # Configuracion del registro 
                    format= '%(asctime)s - %(levelname)s /// %(message)s ')

##############################################################################################################################################
pygame.mixer.init()
modelo = YOLO('best.pt')  # modelo YOLO

rois = {"camara1": (400, 0, 640, 480),"camara2": (0, 0, 300, 480),}     # Almacena rois    --->    roi_x1, roi_y1, roi_x2, roi_y2
ultimo_evento = {"camara1": None, "camara2": None}      # Almacena el tiempo de la deteccion 
detecto = {"camara1": False, "camara2": False}            # Almacena si se detecto algo
sound_path = {"camara1": "sonido_prueva0.mp3", "camara2": "sonido_prueva2.mp3"}     # almacena la ruta de sonido        # sound_path = "sonido_prueva2.mp3"

cap1 = cv2.VideoCapture(0)                          # Abre la cámara (0 = webcam predeterminada)
# cap1 = cv2.VideoCapture('traffic.mp4')                          # Abre la cámara (0 = webcam predeterminada)
cap2 = cap1                        # Abre la cámara (0 = webcam predeterminada)     'people.mp4'

def toma_frame(cam1,cam2):      #Captura de frames para ambas camaras

    ret1, frame1 = cam1.read()
    ret2, frame2 = cam2.read()

    if not cam1.isOpened() and not cam2.isOpened():
        logging.error("No se pudo abrir las camaras")
        exit()

    if ret1 and ret2:
        cola_frames = {         #Diccionario para almacenar los frames
            "camara1": frame1,
            "camara2": frame2
        }
        return cola_frames     #Almacenamiento de frames en la cola


def dibujo (cam_name, cam_frame, results, roi_x1, roi_y1, roi_x2, roi_y2):      # dibuja la pantalla principal y la roi
    cv2.rectangle(cam_frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 0), 2)

    annotated_frame = results[0].plot()             # Dibuja las predicciones sobre el frame

    cv2.imshow(f"{cam_name} - Frame completo", cam_frame)      # Mostrar ventanas
    cv2.imshow(f"{cam_name} - ROI", annotated_frame)


def detecion_roi (cap, roi_x1, roi_y1, roi_x2, roi_y2):

    frame_roi = cap[roi_y1:roi_y2, roi_x1:roi_x2]     # Extraer ROI
    results = modelo(frame_roi)     # Detección con YOLO

    return results


lock = threading.Lock()                                 # evitar condiciones de carrera
def protocolo_detecion(cam_name, ventana_tiempo):       # Cordina las camaras y detecciones con audio
    global ultimo_evento
    global detecto
    contador =0

    otra = "camara2" if cam_name == "camara1" else "camara1"    # identifica la otra camara 

    detecto[cam_name] = True

    with lock:                                      # Sirve para que solo un hilo a la vez pueda modificar ultimo_evento
        
        while detecto[cam_name] == True and contador < ventana_tiempo:
            time.sleep(1)
            contador += 1

            if detecto[cam_name] == True and detecto[otra] == True: 
                logging.info(f"🚨 Alarma disparada con {contador}s (ultima deteccion en {cam_name})")
                pygame.mixer.music.load(sound_path[cam_name])
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                detecto[cam_name], detecto[otra] = False, False
                break

        detecto[cam_name], detecto[otra] = False, False
    
    

##############################################################################################################################################

while True:

    cola_frames = toma_frame(cap1, cap2)

    for cam_name, cam_frame in cola_frames.items():

        roi_x1, roi_y1, roi_x2, roi_y2 = rois[cam_name]
        results = detecion_roi(cam_frame, roi_x1, roi_y1, roi_x2, roi_y2)

        dibujo(cam_name, cam_frame, results, roi_x1, roi_y1, roi_x2, roi_y2)

        for box in results[0].boxes:
            conf = float(box.conf[0])
            if conf > 0.83 and detecto[cam_name]==False:
                logging.info(f"Clase detectada con {conf*100:.2f}% de confianza de  //{cam_name}")
                t = threading.Thread(target=protocolo_detecion, args=(cam_name, 5), daemon=True) 
                t.start()
            # else:                                                       # Linea para comprobar errores 
            #     if detecto[cam_name] == False:
            #          logging.info(f"false {cam_name}")
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        cap1.release()
        cap2.release()
        cv2.destroyAllWindows()
        break