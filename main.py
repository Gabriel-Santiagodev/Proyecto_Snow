import threading
import time
import datetime
import logging
import subprocess       # Biblioteca para ejecutar comandos en la terminal
import psutil           # Biblioteca para leer estado del sistema (Bateria, CPU, Memoria, etc.)
import os
import json
from ultralytics import YOLO
import cv2
import pygame
import tkinter as tk
from tkinter import messagebox

run = None
lock_sistema = threading.Lock()
lock_control_evento = threading.Lock()


class ErrorSignalHandler(logging.Handler):
    def __init__(self, evento_error, nivel_minimo=logging.WARNING):
        super().__init__()
        self.evento_error = evento_error        # Si hay un error enviara un mensaje 
        self.nivel_minimo = nivel_minimo
        self.error_activo = False               # Determina si hay un error fatal 

    def emit(self, record):
        """Determina si el nivel de peligro es suficiente para registrarlo"""
        if record.levelno >= self.nivel_minimo:
            if not self.error_activo:  # evita múltiples ventanas seguidas
                self.error_activo = True
                self.evento_error.set()

                # hilo_error = threading.Thread(target=self.sign, args=(record), daemon=True)
                # hilo_error.start()
                self.sign(record)
            else:
                # Ya hay un error activo
                pass

    def sign(self, record):
        """Metodo para mandar menzaje de error (Actualmente esta incompleto o mal pensado)
        muestra una ventana de error (buscar otra manera de enviar mensaje)"""
        # Crear ventana temporal (invisible)
        root = tk.Tk()
        root.withdraw()

        # Mostrar mensaje con los datos del log
        messagebox.showerror(
            "⚠️ Advertencia del sistema",
            f"Se detectó un {record.levelname}\n\n"
            f"Módulo: {record.name}\n"
            f"Línea: {record.lineno}\n"
            f"Mensaje: {record.getMessage()}"
        )

        # Al cerrar la ventana, reinicia estado
        self.error_activo = False
        self.evento_error.clear()
        root.destroy()


class Sistema:
    def __init__(self, config_file="configuraciones/administracion.json"):
        self.evento = threading.Event()
        self.evento_error = threading.Event()
        self.logging = self.setup_logging()
        self.config = self.cargar_configuracion(config_file)
        self.estado = self.leer_estado()
        self.ultimo_cambio = (None, None)        # (ahorro, normal)
        self.last_run = None

    def setup_logging(self):
        """Metodo de logging, especializado para registar unicamnete con esta clase"""
        logger = logging.getLogger("Sistema")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            # FileHandler para logs
            file_handler = logging.FileHandler('logging/administracion.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s /// %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # 🔔 Handler que dispara el evento
            signal_handler = ErrorSignalHandler(self.evento_error)
            logger.addHandler(signal_handler)

        return logger

    def cargar_configuracion(self, config_file):
        """Carga configuración de la clase"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)                 # Carga los datos
        except FileNotFoundError:           # si no esvuentra el archivo pone por defecto:
            self.logging.error(f"No se encontro el archivo de configuracion, cargando por defaul")
            config_default = {
        "temperatura_max": 65,
        "bateria_minima": 20,
        "inicio_de_trabajo": 6,
        "fin_de_trabajo": 22
        }
            with open(config_file, 'w') as f:
                json.dump(config_default, f, indent=4)
            return config_default

    def leer_estado(self):
        """Se encarga de leer la bateria, temperatura, memoria y uso de cpu"""
        try:
            # with open('/sys/class/power_supply/battery/capacity', 'r') as bateria:  # Para Raspberry Pi con UPS/batería
            #         bateria = int(bateria.read().strip())
            
            # with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temperatura:
            #         temperatura = int(temperatura.read()) / 1000.0
            
            bateria, temperatura = 50, 25             # para realizar pruevas en un entorno windows
            
            cpu_uso = psutil.cpu_percent(interval=1)
            memoria = psutil.virtual_memory().percent

            necesita_ahorro = (bateria < self.config['bateria_minima'] or temperatura > self.config['temperatura_max'] )
            puede_rendimiento = (bateria > 50 and temperatura < 60)
            
            if not necesita_ahorro:
                estado = {
                    'bateria': bateria,
                    'temperatura': temperatura,
                    'memoria': memoria,
                    'cpu_uso': cpu_uso,
                    'necesita_ahorro': necesita_ahorro,         # 'necesita_ahorro': necesita_ahorro,
                    'puede_rendimiento': puede_rendimiento      # 'puede_rendimiento': puede_rendimiento
                }
                self.logging.info(f"Estado del equipo: {estado}")
            else:
                estado = {
                    'bateria': 50,
                    'temperatura': 25,
                    'memoria': memoria,
                    'cpu_uso': cpu_uso,
                    'necesita_ahorro': necesita_ahorro,         # 'necesita_ahorro': necesita_ahorro,
                    'puede_rendimiento': puede_rendimiento      # 'puede_rendimiento': puede_rendimiento
                }
                self.logging.warn(f"Error evaluando estado del sistema cambiar datos de bateria y temperatura, es posible que no se puedan leer: \n{estado}")
            return estado

        except Exception as e:
            self.logging.critical(f"Error evaluando estado del sistema: {e})")
            return None

    def ajustar_frecuencia_cpu(self, frecuencia):
        """Ajusta la frecuencia del cpu"""
        try:
            cmd = f"sudo cpufreq-set -f {frecuencia}MHz"        # Comando en linux para cambiarla frecuencia de CPU:  sudo cpufreq-set -f {frecuencia}MHz
            subprocess.run(cmd, shell=True, check=True)
        except Exception as e:
            logging.error(f"Error ajustando frecuencia CPU: {e}")
            return False

    def ajustar_brillo_pantalla(self, brillo):
        """Ajusta el brillo de la pantalla"""
        try:
            # Para pantallas compatibles
            cmd = f"sudo sh -c 'echo {brillo} > /sys/class/backlight/rpi_backlight/brightness'"
            subprocess.run(cmd, shell=True, check=True)
            return True
        except:
            # No hay pantalla o no es compatible
            return False

    def desactivar_componentes_innecesarios(self):
        """Desactiva componentes innecesarios para ahorrar energía"""
        try:
            comandos_ahorro = [
                "sudo systemctl stop bluetooth",
                "sudo systemctl stop wifi-powersave",
                "sudo modprobe -r usb_storage",  # Desactivar USB storage
                "sudo systemctl stop avahi-daemon",  # Desactivar mDNS
            ]
            
            for comando in comandos_ahorro:
                try:
                    subprocess.run(comando, shell=True, check=False)
                except:
                    pass  # Ignorar errores si el servicio no existe
            
            return True
            
        except Exception as e:
            logging.error(f"Error desactivando componentes: {e}")
            return False

    def activar_componentes_esenciales(self):
        """Reactiva componentes esenciales"""
        try:
            comandos_reactivar = [
                "sudo systemctl start bluetooth",
                "sudo systemctl start wifi-powersave",
                "sudo modprobe usb_storage",
                "sudo systemctl start avahi-daemon",
            ]
            
            for comando in comandos_reactivar:
                try:
                    subprocess.run(comando, shell=True, check=False)
                except:
                    pass

            return True
            
        except Exception as e:
            logging.error(f"Error reactivando componentes: {e}")
            return False

    def administrador_rendimiento(self):
        """Administra el rendimiento y determina si es necesario aplicar o desactivar un ahorro energetico"""
        global run
        cambio_actual = (self.estado['necesita_ahorro'], self.estado['puede_rendimiento'])

        if self.ultimo_cambio == cambio_actual:
            return

        self.ultimo_cambio = cambio_actual

        if self.estado['necesita_ahorro'] or not run:
            self.logging.info("Aplicando optimizaciones de rendimiento")
                
            # self.ajustar_frecuencia_cpu(600)  # 600MHz en lugar de 1500MHz          Reducir frecuencia CPU

            # self.ajustar_brillo_pantalla(50)                # Reducir brillo pantalla

            # desactivar_componentes_innecesarios()      # Desactivar componentes innecesarios
            
            # subprocess.run("echo 'powersave' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", 
            #                 shell=True, check=False)       # Configurar governor de CPU para ahorro
            """
            Este comando cambia el governor del CPU a "powersave", 
            escribiendo ese valor en los archivos /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 
            de todos los núcleos, lo que configura el procesador en modo de bajo consumo energético 
            para reducir el rendimiento y prolongar la autonomía del sistema.
            """

        if self.estado['puede_rendimiento'] and run:
            self.logging.info("Aplicando a modo normal")

            # self.ajustar_frecuencia_cpu(1500)  # 1500MHz            # Aumentar frecuencia CPU

            # self.ajustar_brillo_pantalla(100)               # Aumentar brillo pantalla

            # activar_componentes_esenciales()           # Reactivar componentes

            # subprocess.run("echo 'schedutil' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", 
            #        shell=True, check=False)                 # Este conmando es mas asercado a por defecto

            # subprocess.run("echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", 
            #                 shell=True, check=False)       # Configurar governor de CPU para rendimiento   /// Máximo rendimiento posible.
            """
            Este comando cambia el governor del CPU a "performance", 
            escribiendo ese valor en los archivos /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 
            de todos los núcleos, lo que configura el procesador en modo de máximo rendimiento, 
            manteniendo la frecuencia más alta posible a costa de un mayor consumo de energía.
            """

    #      threading 
    def control_tiempo(self):
        """Metodo principal de la clase, se encaga de correr oras funciones con el horario de trabajo"""
        global run
        
        with lock_sistema:
            inicio = int(self.config['inicio_de_trabajo'])
            fin = int(self.config['fin_de_trabajo'])

            # inicio, fin = 0, 25

            while True:
                self.estado = self.leer_estado()
                self.administrador_rendimiento()

                time_now = datetime.datetime.now().hour     # Hora actual en formato entero (0–23)
                run = inicio <= time_now <= fin         # Determinar si el sistema debe estar activo
                self.control_evento()

                # if run:
                #     fin = 1
                # if fin == 1 and not run:
                #     fin = 25

                time.sleep(10)          # Cada cuanto se realiza una verificacion del tiempo
    
    def control_evento(self):
        """Evita la ejecucion continua de run"""
        global run
        with lock_control_evento:

            if self.last_run == None:
                self.last_run = run

            if run and not self.last_run:
                self.logging.info(f"iniciando camaras por horario") 
                self.evento.set()
                self.evento.clear()
            self.last_run = run


class SADS:
    def __init__(self, evento, evento_error, config_file="configuraciones/configuracion_SADS.json", camara = True):
        self.evento = evento
        self.evento_error = evento_error
        self.logging = self.setup_logging()                         # Configuracion de logger 
        self.configuracion = self.cargar_configuracion(config_file)
        self.nombre = self.configuracion["nombre"]
        self.detecto = {"captura1": False, "captura2": False}
        self.camara = cv2.VideoCapture(self.cargar_configuracion["input"]) if camara == True else camara        # abrira una camara especificada en su configuracion

        self.modelo = YOLO(self.configuracion['modelo'])

        self.roys = {cam: tuple(coords) for cam, coords in self.configuracion['rois'].items()}      # Carga los roys en diccionarios de configuracion
        self.sound_path = self.configuracion['sound_path']      # Carga los sonidos en diccionarios de configuracion

        self.lock_SADS = threading.Lock()           # Asigna los lock (Estructura de codigo que modifican variables de forma segura)
        self.lock_protocolo = threading.Lock()

    def setup_logging(self):
        """Metodo de logging, especializado para registar unicamnete con esta clase"""
        logger = logging.getLogger("SADS")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            file_handler = logging.FileHandler('logging/configuracion_SADS.log', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s /// %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Handler que dispara el mismo evento
            signal_handler = ErrorSignalHandler(self.evento_error)
            logger.addHandler(signal_handler)

        return logger

    def cargar_configuracion(self, config_file):
        """Carga configuración de la clase"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)                 # Carga los datos
        except FileNotFoundError:           # si no esvuentra el archivo pone por defecto:
            self.logging.error(f"No se encontro el archivo de configuracion, cargando por defaul")
            config_default = {
                "dibujar_pantalla": True,
                "modelo": "best.pt",
                "ventana_tiempo": 5,
                "rois": {
                    "captura1": [400, 0, 640, 480],
                    "captura2": [0, 0, 300, 480]
                },
                "sound_path": {
                    "captura1": "sonido_prueva0.mp3",
                    "captura2": "sonido_prueva2.mp3"
                }
            }
            with open(config_file, 'w') as f:
                json.dump(config_default, f, indent=4)
            return config_default

    def toma_frame(self):
        """Captura los frames de las capturas y las devuelve como diccionarios """
        ret, frame = self.camara.read()

        if not self.camara.isOpened():
            self.logging.error("No se pudo abrir la camara")
            return None

        if ret:
            cola_frames = {         #Diccionario para almacenar el frame duplicado
                "captura1": frame.copy(),
                "captura2": frame.copy()
            }
            return cola_frames     #Almacenamiento de frames en la cola
        return None

    def detecion_roi(self, nombre_captura, frame):
        """Se asegura de de que el modelo se aplique a la region de interes (roy)"""

        roi_x1, roi_y1, roi_x2, roi_y2 = self.roys[nombre_captura]

        frame_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]     # Extraer ROI


        results = self.modelo(frame_roi)     # Detección con YOLO

        return results

    def dibujo (self, nombre_captura, frame, results):
        """Dibuja la pantalla principal y los roys si es ta configudaro de tal forma"""

        if self.configuracion["dibujar_pantalla"]:
        
            roi_x1, roi_y1, roi_x2, roi_y2 = self.roys[nombre_captura]

            cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 0), 2)

            annotated_frame = results[0].plot()             # Dibuja las predicciones sobre el frame

            cv2.imshow(f"{self.nombre} - Frame completo", frame)      # Mostrar ventanas
            cv2.imshow(f"{self.nombre} /// {nombre_captura} - ROI", annotated_frame)

    def protocolo_detecion(self, nombre_captura):
        """Cordina las camaras y detecciones """
        contador =0
        otra = "captura2" if nombre_captura == "captura1" else "captura1"    # identifica la otra camara 
        self.detecto[nombre_captura] = True

        while self.detecto[nombre_captura] and contador < self.configuracion['ventana_tiempo']:
            time.sleep(1)
            contador += 1
            with self.lock_protocolo:  # Solo protege la parte que modifica cosas
            # Revisa sin lock, lectura no destructiva
                if self.detecto[nombre_captura] and self.detecto[otra]:
                    
                    self.logging.info(f"🚨 Alarma disparada con {contador}s (ultima deteccion en {nombre_captura} /// {self.nombre})")
                    pygame.mixer.music.load(self.sound_path[nombre_captura])
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    self.detecto[nombre_captura] = False
                    self.detecto[otra] = False
                  
                break
    
    def sads(self):
        """Metodo principal Sistema Autonomo de Deteccion Snow"""
        global run

        with self.lock_SADS:
            while True:

                if run:

                    for nombre_captura, frame in self.toma_frame().items():

                        results = self.detecion_roi(nombre_captura, frame)

                        self.dibujo(nombre_captura, frame, results)

                        for box in results[0].boxes:
                            conf = float(box.conf[0])
                            if conf > 0.83 and not self.detecto[nombre_captura]:
                                self.logging.info(f"Clase detectada con {conf*100:.2f}% de confianza de  /// {nombre_captura} /// {self.nombre}") 
                                t = threading.Thread(target=self.protocolo_detecion, args=(nombre_captura,), daemon=True)
                                t.start()

                    if cv2.waitKey(1) & 0xFF == 27:  # ESC
                        self.camara.release()
                        cv2.destroyAllWindows()
                        break
                else:
                    self.logging.info(f"camara detenida por run horario")
                    self.evento.wait()


if __name__ == "__main__":

    camara_global = cv2.VideoCapture(0)  
    pygame.mixer.init()

    sistema = Sistema()
    hilo_control = threading.Thread(target=sistema.control_tiempo, args=(), daemon=True)
    hilo_control.start()
    
    while run == None:
        time.sleep(1)
    
    camara1 = SADS(sistema.evento, sistema.evento_error, config_file="configuraciones\configuracion_SADS1.json", camara=camara_global)
    camara2 = SADS(sistema.evento, sistema.evento_error, config_file="configuraciones\configuracion_SADS2.json", camara=camara_global)
    camara3 = SADS(sistema.evento, sistema.evento_error, config_file="configuraciones\configuracion_SADS3.json", camara=camara_global)

    a = threading.Thread(target=camara1.sads, args=(), daemon=True)
    a.start()

    b = threading.Thread(target=camara2.sads, args=(), daemon=True)
    b.start()

    c = threading.Thread(target=camara3.sads, args=(), daemon=True)
    c.start()

    while True:
        time.sleep(60 * 10)