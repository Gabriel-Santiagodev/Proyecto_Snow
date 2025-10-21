import time
import threading
from ultralytics import YOLO
import os

import pygame
import logging

# Librerias necesarias para el manejo de las camaras
import cv2
import numpy as np


# Configuracion del loggin
logger = logging.getLogger(__name__)
logging.basicConfig(filename='SADA_logging.log', encoding='utf-8', level=logging.DEBUG,
                    format= '%(asctime)s - %(levelname)s /// %(message)s ')



##############################################################################################################################################

pygame.mixer.init()

# Importacion del modelo YOLO
direccion_script = os.path.dirname(os.path.abspath(__file__))
camino_modelo = os.path.join(direccion_script, "best.pt")
modelo = YOLO(camino_modelo)
#modelo = YOLO('best.pt')  # modelo YOLO


# Zonas de deteccion en las camaras
rois = {"camara1": (400, 0, 640, 480),"camara2": (0, 0, 300, 480),}     # Almacena rois    --->    roi_x1, roi_y1, roi_x2, roi_y2


#  Variables para comprobar si nuestro sujeto se direge o se va del punto meta
# Almacena el tiempo de la deteccion 
ultimo_evento = {"camara1": None, "camara2": None} 
# Almacena si se detecto algo
detecto = {"camara1": False, "camara2": False}            
sound_path = {"camara1": "sonido_prueva0.mp3", "camara2": "sonido_prueva2.mp3"}     # almacena la ruta de sonido        # sound_path = "sonido_prueva2.mp3"


# Declaracion de variables. Camaras a utilizar
camara1 = cv2.VideoCapture(0)                 # (0 = webcam predeterminada)                       
camara2 = camara1                                # Por el momento, se comparte la misma camara para hacer pruebas     'people.mp4'
# cap1 = cv2.VideoCapture('traffic.mp4')   # Abre la cámara (0 = webcam predeterminada)


# Variables para las camaras

# Almacena el tiempo donde se hizo el ultimo chequeo de las camaras
ultimo_chequeo = time.time() 
# Tiempo en segundos de cada cuando se debe de hacer un chequeo de las camaras
intervalo_chequeo = 30  

# Funcion para comprobar si hay obstrucciones
def obstruccion(cam):
    
    #Captura de 2 frames en distintos periodos de tiempo
    ret1, frame1 = cam.read()
    if not ret1:
        return True
    time.sleep(1)
    ret2, frame2 = cam.read()
    if not ret2:
        return True

    #Calculo del cambio de valores (pixeles) entre cada frame
    diferencia = cv2.absdiff(frame1, frame2)
    total_cambio = np.sum(diferencia)

    #Print para buscar el THRESHOLD perfecto segun las condiciones de nuestro proyecto. 
    # Este print es temporal Y SERA ELIMINADO
    print(f"Cambio en camara: {total_cambio}")

    #Comprobacion de obstruccion
    return 5000 > total_cambio



#Funcion para revisar si hay problemas en las camaras
def verificar_camaras(cam1,cam2):
    
    #Comprobacion de obstruccion en ambas camaras
    obstruccion_cam1 = obstruccion(cam1)
    obstruccion_cam2 = obstruccion(cam2)

    #Error al abrir ambas camaras
    if not cam1.isOpened() and not cam2.isOpened():
        logging.error("Ninguna de las camaras se pudo abrir")
        return False
    #Error al abrir la camara 1
    elif not cam1.isOpened():
        logging.warning("Camara 1 no se pudo abrir")
        return False
    #Error al abrir la camara 2
    elif not cam2.isOpened():
        logging.warning("Camara 2 no se pudo abrir")
        return False
    #Error de obstrucion en ambas camaras
    elif obstruccion_cam1 and obstruccion_cam2:
        logging.critical("Ambas camaras obstruidas")
        return False
    #Error de obstrucion en camara 1
    elif obstruccion_cam1:
        logging.error("Camara 1 obstruida")
        return False  
    #Error de obstrucion en camara 2
    elif obstruccion_cam2:
        logging.error("Camara 2 obstruida")
        return False
    else:
        return True 
    


# Funcion para capturar frames. Para cada camara
def toma_frame(cam1,cam2):      

    # Devuelve 2 variables, ret1/2 es un valor booleano. frame1/2 almacenara el frame corresponiente a su camara
    ret1, frame1 = cam1.read()
    ret2, frame2 = cam2.read()

    #Diccionario para almacenar los frames
    if ret1 and ret2:
        diccionario_frames = {         
            "camara1": frame1,
            "camara2": frame2
        }
        #Almacenamiento de frames en la cola
        return diccionario_frames
    # Para evitar que el codigo se rompa, regresamos un valor nulo
    else:
        return None
   



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

    if time.time() - ultimo_chequeo > intervalo_chequeo:
        if not verificar_camaras(camara1, camara2):
            continue
        ultimo_chequeo = time.time()

    cola_frames = toma_frame(camara1, camara2)

    if cola_frames is None:
        logging.warning("No se pudieron capturar los frames")

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
        camara1.release()
        camara2.release()
        cv2.destroyAllWindows()
        break