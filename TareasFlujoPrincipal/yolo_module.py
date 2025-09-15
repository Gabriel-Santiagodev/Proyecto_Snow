from ultralytics import YOLO
import cv2
import numpy as np

import pygame

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='SADA_logging.log', encoding='utf-8', level=logging.DEBUG,     # Configuracion del registro 
                    format= '%(asctime)s - %(levelname)s /// %(message)s ')

pygame.mixer.init()
sound_path = "sonido_prueva1.mp3"

# def centro(x1, y1, x2, y2):
#     x, y = (x1 + x2) // 2, (y1 + y2) // 2
#     return x, y

model = YOLO("best.pt")  # modelo YOLO

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    exit()

# Definir la zona de interés (x1, y1, x2, y2)
roi_x1, roi_y1, roi_x2, roi_y2 = 320, 0, 640, 480

# roi_x1, roi_y1, roi_x2, roi_y2 = 200, 100, 600, 400


while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Extraer el ROI (recorte del frame)
    frame_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

    frame_with_roi = frame.copy()   # La funcion copy realiza una copia de frame para evitar q al modificar alguno el otro se modifique
    cv2.rectangle(frame_with_roi, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 0), 2)


    results = model(frame_roi)                          # YOLO espera un array tipo imagen

    for box in results[0].boxes:    # Bucle de detecciones      results[0] indica la imagen actual      .boxes indica las bounding box
        conf = float(box.conf[0])           # Guarda la confianza de las bounding box
        if conf > 0.85:                     # si la conf es mayor a 84% reproduce un sonido y detiene el sistema hasta que termine este
            logging.info(f"Clase detectada con {conf*100:.2f}% de confianza")

            pygame.mixer.music.load(sound_path)     # # Reproduce el sonido
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():        # Bucle para aplicar delay mientras se aplicael sonido
                pygame.time.Clock().tick(10)        # indica un delay para no sobrecargar la cpu

            break  # evita múltiples sonidos en un mismo frame


    annotated_frame = results[0].plot()             # Dibuja las predicciones sobre el frame
    cv2.imshow("Detección YOLO y ROY", annotated_frame)
    cv2.imshow("Frame Completo", frame_with_roi)

    if cv2.waitKey(1) & 0xFF == 27:  # Presionar ESC para salir
        break


cv2.waitKey(0)

cap.release()
cv2.destroyAllWindows()
