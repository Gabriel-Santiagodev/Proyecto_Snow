#!/usr/bin/env python3
"""
Sistema de Vigilancia - Versión de Desarrollo para Windows
Versión simplificada para pruebas y desarrollo
"""

import time
import threading
import logging
import signal
import sys
import os
import json
import datetime
import psutil
from pathlib import Path
from ultralytics import YOLO
import cv2
import pygame
import numpy as np

class SistemaVigilanciaDesarrollo:
    def __init__(self):
        # Configuración inicial
        self.config = self.cargar_configuracion()
        self.setup_logging()
        
        # Estado del sistema
        self.sistema_activo = True
        self.ultimo_heartbeat = time.time()
        self.contador_reinicios = 0
        self.max_reinicios = 5
        
        # Componentes del sistema
        self.modelo = None
        self.camara1 = None
        self.camara2 = None
        self.lock = threading.Lock()
        
        # Configuración de cámaras y ROIs
        self.rois = {
            "camara1": (400, 0, 640, 480),
            "camara2": (0, 0, 300, 480)
        }
        self.ultimo_evento = {"camara1": None, "camara2": None}
        self.detecto = {"camara1": False, "camara2": False}
        self.sound_path = {
            "camara1": "sonido_prueva0.mp3", 
            "camara2": "sonido_prueva2.mp3"
        }
        self.umbral_obstruccion = 5000  # umbral para comprobar si hay obstruccion en las camaras
        # Almacena el tiempo donde se hizo el ultimo chequeo de las camaras
        self.ultimo_chequeo = time.time() 
        # Tiempo en segundos de cada cuando se debe de hacer un chequeo de las camaras
        self.intervalo_chequeo = 30  
        
        # Configuración de horarios
        self.hora_inicio = self.config.get('hora_inicio', 7)  # 7 AM
        self.hora_fin = self.config.get('hora_fin', 20)       # 8 PM
        
        # Inicializar componentes
        self.inicializar_componentes()
        
        # Configurar manejadores de señales
        signal.signal(signal.SIGTERM, self.manejar_terminacion)
        signal.signal(signal.SIGINT, self.manejar_terminacion)
        
        logging.info("🚀 Sistema de Vigilancia - Modo Desarrollo iniciado")

    def cargar_configuracion(self):
        """Carga configuración desde archivo JSON"""
        config_path = Path("config/config_sistema.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Configuración por defecto
            config_default = {
                "hora_inicio": 6,
                "hora_fin": 20,
                "umbral_confianza": 0.83,
                "ventana_tiempo": 5,
                "max_reinicios": 5,
                "heartbeat_interval": 30
            }
            with open(config_path, 'w') as f:
                json.dump(config_default, f, indent=4)
            return config_default

    def setup_logging(self):
        """Configura sistema de logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Logger principal
        self.logger = logging.getLogger('sistema_vigilancia_desarrollo')
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_dir / 'sistema_desarrollo.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Logger para detecciones
        self.detection_logger = logging.getLogger('detecciones_desarrollo')
        detection_handler = logging.FileHandler(log_dir / 'detecciones_desarrollo.log')
        detection_handler.setFormatter(formatter)
        self.detection_logger.addHandler(detection_handler)
        self.detection_logger.setLevel(logging.INFO)

################################################################################
#                            MÓDULO DE CÁMARAS                                 #
#          Responsable: [Roberto Carlos Jimenez Rodriguez. ITIID-CD 01]        #
################################################################################

    def inicializar_componentes(self):
        """Inicializa todos los componentes del sistema"""
        try:
            # Inicializar pygame para audio
            pygame.mixer.init()
            
            # Cargar modelo YOLO
            self.modelo = YOLO('best.pt')
            self.logger.info("Modelo YOLO cargado correctamente")
            
            # Inicializar cámara
            self.camara1 = cv2.VideoCapture(0)
            if not self.camara1.isOpened():
                raise Exception("No se pudo abrir la cámara 1")
            else:
                self.camara2 = self.camara1
                if not self.camara2.isOpened():
                    raise Exception("No se pudo abrir la cámara 2")
            
            # Configurar camara1
            self.camara1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camara1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camara1.set(cv2.CAP_PROP_FPS, 15)
            # Configurar camara2
            self.camara2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camara2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camara2.set(cv2.CAP_PROP_FPS, 15)
            
            self.logger.info("Cámara inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando componentes: {e}")
            raise
    
    def tomar_frame(self):
        """Captura frame de la cámara"""
        try:
            ret1, frame1 = self.camara1.read()
            if not ret1:
                raise Exception("Error capturando frame de la camara 1")
            ret2, frame2 = self.camara2.read()
            if not ret2: 
                raise Exception("Error capturando frame de la camara 2")
            return {
                "camara1": frame1.copy(),
                "camara2": frame2.copy()
            }
        except Exception as e:
            self.logger.error(f"Error tomando frame: {e}")
            return None

    def deteccion_roi(self, frame, roi_x1, roi_y1, roi_x2, roi_y2):
        """Realiza detección en región de interés"""
        try:
            frame_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
            results = self.modelo(frame_roi)
            return results
        except Exception as e:
            self.logger.error(f"Error en detección ROI: {e}")
            return None
    
    def limpiar_recursos(self):
        """Limpia todos los recursos del sistema"""
        try:
            if self.camara1:
                self.camara1.release()
            # Despues de hacer pruebas y tener las 2 camaras funcionando, vamos a cambiar este if por solo "if self.camara2:"
            if self.camara2 and self.camara2 != self.camara2:
                self.camara2.release()
            cv2.destroyAllWindows()
            self.logger.info("Recursos limpiados correctamente")
        except Exception as e:
            self.logger.error(f"Error limpiando recursos: {e}")

    # Funcion para comprobar si hay obstrucciones
    def obstruccion(self, camara):

        #Captura de 2 frames en distintos periodos de tiempo
        ret1, frame1 = camara.read()
        if not ret1:
            self.logger.error("Error leyendo primer frame para obstrucción")
            return True
        time.sleep(0.1)
        ret2, frame2 = camara.read()
        if not ret2:
            self.logger.error("Error leyendo segundo frame para obstrucción")
            return True
        
        escalagrises1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        escalagrises2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        #Calculo del cambio de valores (pixeles) entre cada frame
        diferencia = cv2.absdiff(escalagrises1, escalagrises2)
        total_cambio = np.sum(diferencia)

        #Print para buscar el THRESHOLD perfecto segun las condiciones de nuestro proyecto. 
        # Este print es temporal Y SERA ELIMINADO
        self.logger.debug(f"Cambio detectado en cámara: {total_cambio}")

        #Comprobacion de obstruccion
        return self.umbral_obstruccion > total_cambio

    #Funcion para revisar si hay problemas en las camaras
    def verificar_camaras(self, cam1, cam2):

        #Error al abrir ambas camaras
        if not cam1.isOpened() and not cam2.isOpened():
            self.logger.error("Ninguna de las camaras se pudo abrir")
            return False
        #Error al abrir la camara 1
        elif not cam1.isOpened():
            self.logger.warning("Camara 1 no se pudo abrir")
            return False
        #Error al abrir la camara 2
        elif not cam2.isOpened():
            self.logger.warning("Camara 2 no se pudo abrir")
            return False

        #Comprobacion de obstruccion en ambas camaras
        obstruccion_cam1 = self.obstruccion(cam1)
        obstruccion_cam2 = self.obstruccion(cam2)

        #Error de obstrucion en ambas camaras
        if obstruccion_cam1 and obstruccion_cam2:
            self.logger.critical("Ambas camaras obstruidas")
            return False
        #Error de obstrucion en camara 1
        elif obstruccion_cam1:
            self.logger.error("Camara 1 obstruida")
            return False  
        #Error de obstrucion en camara 2
        elif obstruccion_cam2:
            self.logger.error("Camara 2 obstruida")
            return False
        else:
            return True 

################################################################################
#                          FIN MÓDULO DE CÁMARAS                               #
#          Responsable: [Roberto Carlos Jimenez Rodriguez. ITIID-CD 01]        #
################################################################################



################################################################################
#                            AHORRO DE ENERGIA                                 #
#          Responsable: [Roberto Carlos JImenez Rodriguez. ITIID-CD 01]        #
################################################################################

    def es_horario_activo(self):
        """Verifica si el sistema debe estar activo según la hora"""
        hora_actual = datetime.datetime.now().hour
        return self.hora_inicio <= hora_actual < self.hora_fin

################################################################################
#                          FIN AHORRO DE ENERGIA                               #
#          Responsable: [Roberto Carlos Jimenez Rodriguez. ITIID-CD 01]        #
################################################################################



    def verificar_estado_sistema(self):
        """Monitorea la salud del sistema"""
        try:
            # Verificar uso de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"CPU alta: {cpu_percent}%")
            
            # Verificar memoria
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                self.logger.warning(f"Memoria alta: {memory.percent}%")
            
            # Verificar espacio en disco
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"Espacio en disco bajo: {disk.percent}%")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando estado del sistema: {e}")
            return False

    def manejar_terminacion(self, signum, frame):
        """Maneja la terminación del sistema"""
        self.logger.info(f"Recibida señal {signum}, terminando sistema...")
        self.sistema_activo = False
        self.limpiar_recursos()
        sys.exit(0)

    def dibujar_ventanas(self, cam_name, frame, results, roi_x1, roi_y1, roi_x2, roi_y2):
        """Dibuja ventanas de visualización"""
        try:
            # Dibujar ROI
            cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 0), 2)
            
            if results and len(results) > 0:
                annotated_frame = results[0].plot()
                cv2.imshow(f"{cam_name} - ROI", annotated_frame)
            
            cv2.imshow(f"{cam_name} - Frame completo", frame)
            
        except Exception as e:
            self.logger.error(f"Error dibujando ventanas: {e}")

    def protocolo_deteccion(self, cam_name, ventana_tiempo):
        """Protocolo de detección con coordinación entre cámaras"""
        try:
            otra = "camara2" if cam_name == "camara1" else "camara1"
            self.detecto[cam_name] = True
            contador = 0

            with self.lock:
                while self.detecto[cam_name] and contador < ventana_tiempo:
                    time.sleep(1)
                    contador += 1

                    if self.detecto[cam_name] and self.detecto[otra]:
                        self.detection_logger.info(f"🚨 Alarma disparada con {contador}s (última detección en {cam_name})")
                        
                        # Reproducir sonido
                        try:
                            pygame.mixer.music.load(self.sound_path[cam_name])
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                pygame.time.Clock().tick(10)
                        except Exception as e:
                            self.logger.error(f"Error reproduciendo sonido: {e}")
                        
                        self.detecto[cam_name] = False
                        self.detecto[otra] = False
                        break

                self.detecto[cam_name] = False
                self.detecto[otra] = False
                
        except Exception as e:
            self.logger.error(f"Error en protocolo de detección: {e}")

    def heartbeat(self):
        """Sistema de heartbeat para monitoreo"""
        while self.sistema_activo:
            try:
                print("💓 Heartbeat del sistema (modo desarrollo)")
                
                # Verificar estado del sistema
                if not self.verificar_estado_sistema():
                    self.logger.warning("Problemas detectados en el sistema")
                
                self.ultimo_heartbeat = time.time()
                time.sleep(self.config.get('heartbeat_interval', 30))
                
            except Exception as e:
                self.logger.error(f"Error en heartbeat: {e}")
                time.sleep(10)

    def ejecutar_sistema(self):
        """Función principal del sistema"""
        try:
            # Iniciar thread de heartbeat
            heartbeat_thread = threading.Thread(target=self.heartbeat, daemon=True)
            heartbeat_thread.start()
            
            self.logger.info("Sistema iniciado correctamente")
            print("🎯 Sistema de Vigilancia Snow - Modo Desarrollo")
            print("📋 Presiona ESC para salir")
            print("🔍 Monitoreando detecciones...")
            
            while self.sistema_activo:
                try:

                    # Verificar si hay problemas en las camaras
                    if time.time() - self.ultimo_chequeo > self.intervalo_chequeo:
                        if not self.verificar_camaras(self.camara1, self.camara2):
                            time.sleep(2)
                            continue
                        self.ultimo_chequeo = time.time()

                    # Verificar si es horario activo
                    if not self.es_horario_activo():
                        self.logger.info("Fuera del horario activo, sistema en standby")
                        print("🌙 Fuera del horario activo (6 AM - 8 PM)")
                        time.sleep(60)  # Esperar 1 minuto
                        continue
                    
                    # Capturar frames
                    cola_frames = self.tomar_frame()
                    if cola_frames is None:
                        self.logger.error("Error capturando frame, reintentando...")
                        time.sleep(1)
                        continue
                    
                    # Procesar cada cámara
                    for cam_name, frame in cola_frames.items():
                        roi_x1, roi_y1, roi_x2, roi_y2 = self.rois[cam_name]
                        results = self.deteccion_roi(frame, roi_x1, roi_y1, roi_x2, roi_y2)
                        
                        if results is None:
                            continue
                        
                        self.dibujar_ventanas(cam_name, frame, results, roi_x1, roi_y1, roi_x2, roi_y2)
                        
                        # Procesar detecciones
                        if results and len(results) > 0 and results[0].boxes is not None:
                            for box in results[0].boxes:
                                conf = float(box.conf[0])
                                umbral = self.config.get('umbral_confianza', 0.83)
                                
                                if conf > umbral and not self.detecto[cam_name]:
                                    self.detection_logger.info(f"Clase detectada con {conf*100:.2f}% de confianza en {cam_name}")
                                    print(f"🎯 Detección en {cam_name}: {conf*100:.1f}% confianza")
                                    
                                    ventana_tiempo = self.config.get('ventana_tiempo', 5)
                                    t = threading.Thread(
                                        target=self.protocolo_deteccion, 
                                        args=(cam_name, ventana_tiempo), 
                                        daemon=True
                                    )
                                    t.start()
                    
                    # Verificar tecla ESC para salir
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error en bucle principal: {e}")
                    time.sleep(5)
                    
        except Exception as e:
            self.logger.critical(f"Error crítico en sistema: {e}")
        finally:
            self.limpiar_recursos()

def main():
    """Función principal"""
    sistema = None
    try:
        sistema = SistemaVigilanciaDesarrollo()
        sistema.ejecutar_sistema()
    except KeyboardInterrupt:
        print("\n⚠️  Sistema interrumpido por usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        if sistema:
            sistema.limpiar_recursos()

if __name__ == "__main__":
    main()
