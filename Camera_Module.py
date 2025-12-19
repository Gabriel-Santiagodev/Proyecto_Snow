import cv2
import threading
import time

class Camera_Module:
    def __init__(self, src, width=640, height=480, fps=30):
        """ 
            .read() obtiene un valor True/False y un frame de la cámara
            self.leido = True/False
            self.frame = Imagen capturada 
        """
        self.leido = False
        self.frame = None

        # Variable para apagar la cámara
        self.stopped = False
        
        # Evitar glitches en caso de que la cámara esté trabajando y se quiera leer
        self.lock = threading.Lock()

        # Inicialización de la cámara
        self.stream = cv2.VideoCapture(src)

        # Configuración de zonas Roi
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_FPS, fps)

        # Lectura del primer frame
        if self.stream.isOpened():
            (self.leido, self.frame) = self.stream.read()
    
    # Inicializador de las camaras
    def start(self):
        t = threading.Thread(target=self.update, args=(), daemon=True)
        t.start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.stream.release()
                return
            
            if self.stream.isOpened():
                (leido, frame) = self.stream.read()
            
                with self.lock:
                    self.leido = leido
                    if leido:
                        self.frame = frame
                
                time.sleep(0.01)
            else:
                time.sleep(0.01)

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.stopped = True
        
    def release(self):
        self.stop()

    def isOpened(self):
        return self.stream.isOpened()