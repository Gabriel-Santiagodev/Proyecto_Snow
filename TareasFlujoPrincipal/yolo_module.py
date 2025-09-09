from ultralytics import YOLO
import cv2
import pygame

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='SADA_logging.log', encoding='utf-8', level=logging.DEBUG,     # Configuracion del registro 
                    format= '%(asctime)s - %(levelname)s /// %(message)s ')

pygame.mixer.init()                                 # Inicializa pygame para reproducir sonido

# Carga tu modelo entrenado
model = YOLO("best.pt")

# Ruta del sonido
sound_path = "sonido_prueva1.mp3"

cap = cv2.VideoCapture(0)                          # Abre la cámara (0 = webcam predeterminada)

if not cap.isOpened():
    logging.error("No se pudo abrir la cámara")
    exit()

logging.info("se ha abierto la camara")

while True:
    ret, frame = cap.read()     # cap.read() da 2 argumentos   ==   ret = (funciona?), frame = array de imagen
    if not ret:
        break

    results = model(frame)                          # YOLO espera un array tipo imagen

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
    cv2.imshow("Detección YOLO", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):           # q para salir 
        break

cap.release()
cv2.destroyAllWindows()
