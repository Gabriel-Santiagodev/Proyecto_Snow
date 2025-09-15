import cv2
import numpy as np
import time
from config import THRESHOLD
import ModulosGenerales.modulo_logging as modulo_logging 
import logging



# Funcion para comprobar si hay obstrucciones
def obstruccion(cam,THRESHOLD):
    
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

    #Print para buscar el THRESHOLD perfecto segun las condiciones de nuestro proyecto. Este print es temporal
    print(f"Cambio en camara: {total_cambio}")

    #Comprobacion de obstruccion
    return THRESHOLD > total_cambio



#Funcion para revisar las camaras y si hay problemas
def verificar_camaras(cam1,cam2,THRESHOLD):
    
    #Comprobacion de obstruccion en ambas camaras
    obstruccion_cam1 = obstruccion(cam1, THRESHOLD)
    obstruccion_cam2 = obstruccion(cam2, THRESHOLD)

    #Error al abrir ambas camaras
    if not cam1.isOpened() and not cam2.isOpened():
        logger.error("Ninguna de las camaras se pudo abrir")
        return False
    #Error al abrir la camara 1
    elif not cam1.isOpened():
        logger.warning("Camara 1 no se pudo abrir")
        return False
    #Error al abrir la camara 2
    elif not cam2.isOpened():
        logger.warning("Camara 2 no se pudo abrir")
        return False
    #Error de obstrucion en ambas camaras
    elif obstruccion_cam1 and obstruccion_cam2:
        logger.critical("Ambas camaras obstruidas")
        return False
    #Error de obstrucion en camara 1
    elif obstruccion_cam1:
        logger.error("Camara 1 obstruida")
        return False  
    #Error de obstrucion en camara 2
    elif obstruccion_cam2:
        logger.error("Camara 2 obstruida")
        return False
    else:
        return True 



#Funcion que almacena Frames
def toma_frame(cam1,cam2,cola_frames):

    #Captura de frames para ambas camaras
    condicion1, frame1 = cam1.read()
    condicion2, frame2 = cam2.read()
    if condicion1 and condicion2:
        #Diccionario para almacenar los frames
        frames_YOLO = {
            "camara1": frame1,
            "camara2": frame2
        }
        #Almacenamiento de frames en la cola
        cola_frames.put(frames_YOLO)



#Declaracion de variables
camara1 = cv2.VideoCapture(0)
camara2 = cv2.VideoCapture(1)



#Configuracion del logging
modulo_logging.setup_logging()
logger = logging.getLogger("snow").getChild("cameras_module")



#Flujo principal del modulo
def run(stop_event,cola_frames):
    logger.info("Module 'cameras_module' started")

    while not stop_event.is_set():
        esta_trabajando = verificar_camaras(camara1, camara2, THRESHOLD) 
        if esta_trabajando:
            toma_frame(camara1, camara2,cola_frames)
        else:
            #Pausa para no saturar, en caso de que las camaras no sirvan
            time.sleep(2)

    logger.info("Module 'cameras_module' stopped")