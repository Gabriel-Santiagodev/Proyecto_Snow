#!/usr/bin/env python3
"""
Este es el sistema principal de deteccion - Versión con Gestión de Batería
Cuenta con adaptación automática según nivel de batería
"""
""" 

                        Modos de trabajo

| Porcentaje de bateria | Modo de trabajo | Camaras    | Accion                                    
|-----------------------|-----------------|------------|-------------------------------------------
| 70-100%               | 🟢 ÓPTIMO       | 2 @ 15 FPS | Todo el sistema trabaja                  
| 50-70%                | 🟢 NORMAL       | 2 @ 12 FPS | Se reducen ligeramente los chequeos      
| 35-50%                | 🟡 BAJA         | 1 @ 8 FPS  | Trabaja solo con una camara                      
| 20-35%                | 🟠 CRITICA      | 1 @ 5 FPS  | Chequeos minimos               
| <20%                  | 🔴 EMERGENCIA   | 0          | Enciende la alerta LED, deja de trabajar 

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
import oled_module
# ════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LOGGING PARA ULTRALYTICS/YOLO
# ════════════════════════════════════════════════════════════

# Desactivar verbose de YOLO (suprime prints en consola)
os.environ['YOLO_VERBOSE'] = 'False'

# Librerias que usan YOLO
import cv2
import pygame
import numpy as np
from ultralytics import YOLO

# Configurar logger de Ultralytics
ultralytics_logger = logging.getLogger('ultralytics')

# Muestra mediante loggin info, warning, error
# Opciones: DEBUG, INFO, WARNING, ERROR
ultralytics_logger.setLevel(logging.INFO)

# Desactivar propagación para evitar duplicados
ultralytics_logger.propagate = False

# Handler para guardar logs de YOLO en archivo separado
Path("logs").mkdir(exist_ok=True)
yolo_handler = logging.FileHandler('logs/yolo.log')
yolo_handler.setLevel(logging.INFO)
yolo_formatter = logging.Formatter('%(asctime)s - YOLO - %(levelname)s - %(message)s')
yolo_handler.setFormatter(yolo_formatter)
ultralytics_logger.addHandler(yolo_handler)

# ════════════════════════════════════════════════════════════

# Importar simulador de batería
# IMPORTACION TEMPORAL. CUANDO TENGAMOS MANERA DE LEER LA BATERIA LO ELIMINAREMOS
from simulador_bateria import SimuladorBateria

# ════════════════════════════════════════════════════════════

# Importar Camera_Module.py
from Camera_Module import Camera_Module

class SistemaVigilanciaConBateria:
    def __init__(self):

        # Configuración inicial
        self.config = self.cargar_configuracion()
        self.setup_logging()
        
        # ════════════════════════════════════════════════════════════
        # 🔋 INICIALIZAR SIMULADOR DE BATERÍA
        # ════════════════════════════════════════════════════════════
        self.bateria = SimuladorBateria()
        self.logger.info("🔋 Sistema de batería inicializado")
        
        # Umbrales de batería (porcentajes)
        self.BATERIA_OPTIMA = 70      # 70-100%: 2 cámaras
        self.BATERIA_NORMAL = 50      # 50-70%: 2 cámaras
        self.BATERIA_BAJA = 35        # 35-50%: 1 cámara
        self.BATERIA_CRITICA = 20     # <20%: 1 camara
        
        # Modo actual del sistema
        self.modo_actual = "OPTIMO"
        self.ultimo_cambio_modo = time.time()
        # ════════════════════════════════════════════════════════════
        # 🔋 FIN SIMULADOR DE BATERÍA
        # ════════════════════════════════════════════════════════════
        
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
        
        # Diccionario de zonas roi (zonas donde se hara la deteccion)
        self.rois = {
            "camara 1": (400, 0, 640, 480),
            "camara 2": (0, 0, 300, 480)
        }

        # Configuración de cámaras
        self.ultimo_evento = {"camara1": None, "camara2": None}
        self.detecto = {"camara1": False, "camara2": False}
        self.sound_path = {
            "camara1": "sonido_prueva0.mp3", 
            "camara2": "sonido_prueva2.mp3"
        }
        self.umbral_obstruccion = 5000
        self.ultimo_chequeo = time.time()
        self.intervalo_chequeo = 30
        
        # Configuración de horarios
        self.hora_inicio = self.config.get('hora_inicio', 6.5) # 6:30 AM
        self.hora_fin = self.config.get('hora_fin', 20) # 8:00 PM
        
        # Evento para controlar el módulo OLED
        self.stop_event = threading.Event()

        # Bandera para evitar limpieza doble
        self.recursos_limpiados = False
        
        # Inicializar componentes
        self.inicializar_componentes()
        
        # Configurar manejadores de señales
        signal.signal(signal.SIGTERM, self.manejar_terminacion)
        signal.signal(signal.SIGINT, self.manejar_terminacion)
        
        logging.info("Sistema de Vigilancia con Batería iniciado")

    def cargar_configuracion(self):
        """Carga configuración desde archivo JSON"""
        config_path = Path("config/config_sistema.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            config_default = {
                "hora_inicio": 6.5,
                "hora_fin": 20,
                "umbral_confianza": 0.83,
                "ventana_tiempo": 5,
                "max_reinicios": 5,
                "heartbeat_interval": 30
            }
            Path("config").mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config_default, f, indent=4)
            return config_default

    def setup_logging(self):
        """Configura sistema de logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('sistema_vigilancia_bateria')
        self.logger.setLevel(logging.DEBUG)
        
        file_handler = logging.FileHandler(log_dir / 'sistema_con_bateria.log')
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.detection_logger = logging.getLogger('detecciones_bateria')
        detection_handler = logging.FileHandler(log_dir / 'detecciones_bateria.log')
        detection_handler.setFormatter(formatter)
        self.detection_logger.addHandler(detection_handler)
        self.detection_logger.setLevel(logging.INFO)

    ############################################################################
    #                            MÓDULO DE CÁMARAS                             #
    #          Responsable: [Roberto Carlos Jimenez Rodriguez. ITIID-CD 01]   #
    ############################################################################

    def inicializar_componentes(self):

        """Inicializa todos los componentes del sistema"""
        try:
            pygame.mixer.init()
            
            self.modelo = YOLO('best.pt', verbose=False)
            self.logger.info("Modelo YOLO cargado correctamente")            
            
            # Inicializar cámaras
            self.camara1 = Camera_Module(src = 0).start()
            self.camara2 = Camera_Module(src = 1).start()

            # Tiempo para que las cámaras arranquen
            time.sleep(2.0)
            
            # Comprobacion de errores
            if not self.camara1.isOpened() and not self.camara2.isOpened():
                raise Exception("Error Critico: Ambas camaras no se pudieron abrir")
            else:
                if not self.camara1.isOpened():
                    self.logger.warning("No se pudo abrir la cámara 1")
                if not self.camara2.isOpened():
                    self.logger.warning("No se puedo abrir la cámara 2")
            if self.camara1.isOpened() and self.camara2.isOpened():
                self.logger.info("Cámaras inicializadas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando componentes: {e}")
            raise
    
    def tomar_frame(self, usar_ambas_camaras=True):

        """Captura frame de las cámaras (adaptable según batería)"""
        frames_capturados = {}

        # Obtener los frames de camara1
        frame1 = self.camara1.read()

        # Guardar los frames de camara1 en un diccionario
        if frame1 is not None:
            frames_capturados["camara1"] = frame1
        else:
            self.logger.warning("Error: Camara 1 devolvio frame vacio (None)")
            return None
        
        if usar_ambas_camaras and self.camara2.isOpened():
            # Obtener los frames de camara1
            frame2 = self.camara2.read()
            
            # Guardar los frames de camara1 en un diccionario
            if frame2 is not None:
                frames_capturados["camara2"] = frame2
            else:
                self.logger.warning("Error: Camara 2 devolvio frame vacio (None)")

        return frames_capturados                

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
        # Evitar limpieza doble
        if self.recursos_limpiados:
            return
        self.recursos_limpiados = True
        
        try:
            self.stop_event.set()
            self.logger.info("Módulo OLED detenido")
            time.sleep(0.5)
            
            if self.camara1:
                self.camara1.release()
            if self.camara2:
                self.camara2.release()
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            self.logger.info("Recursos limpiados correctamente")
        except Exception as e:
            self.logger.error(f"Error limpiando recursos: {e}")

    def obstruccion(self, camara):
        """Detecta si la cámara está obstruida"""
        try:
            ret1, frame1 = camara.read()
            if not ret1:
                self.logger.error("Error leyendo primer frame para obstrucción")
                return True
            
            time.sleep(0.1)
            
            ret2, frame2 = camara.read()
            if not ret2:
                self.logger.error("Error leyendo segundo frame para obstrucción")
                return True
            
            escalagrises_frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            escalagrises_frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            diferencia = cv2.absdiff(escalagrises_frame1, escalagrises_frame2)
            total_cambio = np.sum(diferencia)
            
            # ESTE LOGGER VA A SER ELIMINADO CUANDO SE ENCUENTRE EL UMBRAL DE OBSTRUCCION PERFECTO
            self.logger.debug(f"Cambio detectado en cámara: {total_cambio}")
            
            return total_cambio < self.umbral_obstruccion
            
        except Exception as e:
            self.logger.error(f"Error detectando obstrucción: {e}")
            return True

    def verificar_camaras(self, cam1, cam2):
        """Verifica el estado de las cámaras"""
        try:
            if not cam1.isOpened():
                self.logger.warning("Cámara 1 no se pudo abrir")
                return False
            
            if not cam2.isOpened():
                self.logger.warning("Cámara 2 no se pudo abrir")
                return False
            
            obstruccion_cam1 = self.obstruccion(cam1)
            
            if obstruccion_cam1:
                self.logger.error("Cámara 1 obstruida")
                return False
            
            obstruccion_cam2 = self.obstruccion(cam2)
            if obstruccion_cam2:
                self.logger.error("Cámara 2 obstruida")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando cámaras: {e}")
            return False

    ############################################################################
    #                          FIN MÓDULO DE CÁMARAS                           #
    ############################################################################

    ############################################################################
    #                      GESTIÓN DE BATERÍA Y MODOS                          #    
    #      Responsable: [Roberto Carlos Jimenez Rodriguez. ITIID-CD 01]        #
    ############################################################################

    def actualizar_bateria(self):
        # Cada segundo, se va a actualizar el estado de la bateria. Almacena el valor
        self.bateria.actualizar_bateria(1)
    
    def obtener_estado_bateria(self):
        # Retorna el estado de la bateria
        return self.bateria.obtener_estado()
    
    def determinar_modo_operacion(self, porcentaje_bateria):
        """
         Segun el porcentaje de bateria, se decide de que manera trabajar
         Retorna el modo en el que se debe trabajar

        Args:
            porcentaje_bateria (float): Porcentaje actual de batería (0-100)
    
        Returns:
            (modo, num_camaras)
                - modo (str): "OPTIMO", "NORMAL", "ECO", "CONSERVACION", o "EMERGENCIA"
                - num_camaras (int): Número de cámaras a usar (0, 1, o 2)
                
                Umbrales:
                    - 70-100%: OPTIMO (2 cámaras)
                    - 50-70%: NORMAL (2 cámaras, eco)
                    - 35-50%: ECO (1 cámara)
                    - 20-35%: CONSERVACION (1 cámara, mínimo)
                    - <20%: EMERGENCIA (preparar apagado)
        """
        if porcentaje_bateria >= self.BATERIA_OPTIMA:
            return "OPTIMO", 2  
        elif porcentaje_bateria >= self.BATERIA_NORMAL:
            return "NORMAL", 2  
        elif porcentaje_bateria >= self.BATERIA_BAJA:
            return "ECO", 1     
        elif porcentaje_bateria >= self.BATERIA_CRITICA:
            return "CONSERVACION", 1 
        else:
            return "EMERGENCIA", 0    
    
    def cambiar_modo(self, nuevo_modo, num_camaras):
        # Cambio de modo
        if nuevo_modo != self.modo_actual:
            self.logger.info(f"Cambiando modo: {self.modo_actual} → {nuevo_modo}")
            self.logger.info(f"Cámaras activas: {num_camaras}")
            
            # Actualizar simulador de batería
            self.bateria.cambiar_camaras(num_camaras if num_camaras > 0 else 1)
            
            self.modo_actual = nuevo_modo
            self.ultimo_cambio_modo = time.time()

    # ESTA AREA ESTA COMENTADA PORQUE SIRVE SOLO AL MOMENTO DE HACER PRUEBAS
    """
    def mostrar_estado_bateria(self):
        # Muestra estado de batería en consola
        estado = self.obtener_estado_bateria()
        
        barra_bateria = self.generar_barra_bateria(estado['porcentaje'])
        
        print(f"\r🔋 {barra_bateria} {estado['porcentaje']:.1f}% | "
              f"⚡ {estado['voltaje']:.2f}V | "
              f"📹 {estado['camaras_activas']} cam | "
              f"{estado['emoji_estado']} {estado['modo_recomendado']}", 
              end='', flush=True)

    def generar_barra_bateria(self, porcentaje):
        # Genera barra visual de batería
        lleno = int(porcentaje / 10)
        vacio = 10 - lleno
        
        if porcentaje >= 70:
            color = "█"
        elif porcentaje >= 35:
            color = "▓"
        else:
            color = "░"
        
        return f"[{color * lleno}{'░' * vacio}]"
    """

    ############################################################################
    #                    FIN GESTIÓN DE BATERÍA Y MODOS                        #
    ############################################################################

    def es_horario_activo(self):
        """Verifica si el sistema debe estar activo según la hora"""
        ahora = datetime.datetime.now()
        # Convertir a decimal (6:30 AM = 6.5)
        hora_actual = ahora.hour + ahora.minute / 60.0
        return self.hora_inicio <= hora_actual < self.hora_fin

    def verificar_estado_sistema(self):
        """Monitorea la salud del sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"CPU alta: {cpu_percent}%")
            
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                self.logger.warning(f"Memoria alta: {memory.percent}%")
            
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
                print("\n💓 Heartbeat del sistema")
                
                if not self.verificar_estado_sistema():
                    self.logger.warning("Problemas detectados en el sistema")
                
                # Mostrar reporte de batería cada heartbeat
                estado = self.obtener_estado_bateria()
                print(f"🔋 Batería: {estado['porcentaje']:.1f}% | Modo: {self.modo_actual}")
                
                self.ultimo_heartbeat = time.time()
                time.sleep(self.config.get('heartbeat_interval', 30))
                
            except Exception as e:
                self.logger.error(f"Error en heartbeat: {e}")
                time.sleep(10)

    def ejecutar_sistema(self):
        """Función principal del sistema"""
        try:
            heartbeat_thread = threading.Thread(target=self.heartbeat, daemon=True)
            heartbeat_thread.start()
            
            # Iniciar módulo OLED
            oled_thread = threading.Thread(
                target=oled_module.run, 
                args=(self.stop_event,), 
                daemon=True
            )
            oled_thread.start()
            self.logger.info("Módulo OLED iniciado")
            
            self.logger.info("Sistema iniciado correctamente")
            # ESTOS PRINTS SERAN ELIMINADOS CUANDO SE CONSIGA LA VERSION FINAL
            print("Sistema de Vigilancia Snow - Con Gestión de Batería")
            print("Presiona ESC para salir")
            print("Monitoreando detecciones...\n")
            
            while self.sistema_activo:
                try:
                    # ════════════════════════════════════════════════════
                    # ACTUALIZAR Y VERIFICAR BATERÍA
                    # ════════════════════════════════════════════════════
                    self.actualizar_bateria()
                    estado_bateria = self.obtener_estado_bateria()
                    porcentaje = estado_bateria['porcentaje']
                    
                    # Determinar modo de operación
                    nuevo_modo, num_camaras = self.determinar_modo_operacion(porcentaje)
                    
                    # Cambiar modo si es necesario
                    if nuevo_modo != self.modo_actual:
                        self.cambiar_modo(nuevo_modo, num_camaras)

                    if not hasattr(self, 'ultimo_porcentaje_log'):
                        self.ultimo_porcentaje_log = 100
                        self.logger.info(f"Batería inicial: {porcentaje:.1f}%")

                    porcentaje_redondeado = int(porcentaje / 10) * 10  # Round to nearest 10
                    if porcentaje_redondeado < self.ultimo_porcentaje_log:
                        self.ultimo_porcentaje_log = porcentaje_redondeado
                        self.logger.info(f"Batería: {porcentaje:.1f}% ({estado_bateria['voltaje']:.2f}V)")
                    
                    # ESTA AREA ESTA COMENTADA PORQUE SIRVE SOLO AL MOMENTO DE HACER PRUEBAS
                    # if int(time.time()) % 5 == 0:  # Solo cada 5 segundos
                    #    self.mostrar_estado_bateria()
                    
                    # ════════════════════════════════════════════════════
                    # VERIFICAR CAMARAS
                    # ════════════════════════════════════════════════════
                    if time.time() - self.ultimo_chequeo > self.intervalo_chequeo:
                        if not self.verificar_camaras(self.camara1, self.camara2):
                            time.sleep(2)
                            continue
                        self.ultimo_chequeo = time.time()

                    # ════════════════════════════════════════════════════
                    # VERIFICAR HORARIO
                    # ════════════════════════════════════════════════════                   
                    if not self.es_horario_activo():
                        self.logger.info("Fuera del horario activo, sistema en standby")
                        self.limpiar_recursos()
                        time.sleep(60)
                        continue

                    # ════════════════════════════════════════════════════
                    # VERIFICAR SI SE SOLICITÓ DETENER DESDE OLED
                    # ════════════════════════════════════════════════════
                    if self.stop_event.is_set():
                        self.logger.info("Detención solicitada desde módulo OLED")
                        break
                    
                    # ════════════════════════════════════════════════════
                    # CAPTURA Y PROCESAMIENTO DE FRAMES
                    # ════════════════════════════════════════════════════                    
                    usar_dos_camaras = (num_camaras == 2)
                    cola_frames = self.tomar_frame(usar_ambas_camaras=usar_dos_camaras)
                    
                    if cola_frames is None:
                        self.logger.error("Error capturando frame, reintentando...")
                        time.sleep(1)
                        continue
                    
                    # ════════════════════════════════════════════════════
                    # PROCESAMIENTO CON YOLO
                    # ════════════════════════════════════════════════════
                    for cam_name, frame in cola_frames.items():
                        roi_x1, roi_y1, roi_x2, roi_y2 = self.rois[cam_name]
                        results = self.deteccion_roi(frame, roi_x1, roi_y1, roi_x2, roi_y2)
                        
                        if results is None:
                            continue
                        
                        self.dibujar_ventanas(cam_name, frame, results, roi_x1, roi_y1, roi_x2, roi_y2)
                        
                        if results and len(results) > 0 and results[0].boxes is not None:
                            for box in results[0].boxes:
                                conf = float(box.conf[0])
                                umbral = self.config.get('umbral_confianza', 0.83)
                                
                                if conf > umbral and not self.detecto[cam_name]:
                                    self.detection_logger.info(f"Clase detectada con {conf*100:.2f}% de confianza en {cam_name}")
                                    print(f"\nDetección en {cam_name}: {conf*100:.1f}% confianza")
                                    
                                    ventana_tiempo = self.config.get('ventana_tiempo', 5)
                                    t = threading.Thread(
                                        target=self.protocolo_deteccion, 
                                        args=(cam_name, ventana_tiempo), 
                                        daemon=True
                                    )
                                    t.start()
                    
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
        sistema = SistemaVigilanciaConBateria()
        sistema.ejecutar_sistema()
    except KeyboardInterrupt:
        print("\n\nSistema interrumpido por usuario")
    except Exception as e:
        print(f"Error crítico: {e}")
    finally:
        if sistema:
            sistema.limpiar_recursos()

if __name__ == "__main__":
    main()