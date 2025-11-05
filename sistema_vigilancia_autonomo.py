#!/usr/bin/env python3
"""
Sistema de Vigilancia Autónomo para Exteriores
Diseñado para Raspberry Pi con panel solar
Autor: Sistema SADA
"""

import time
import threading
import logging
import signal
import sys
import os
import subprocess
import datetime
import json
import psutil
from pathlib import Path
from ultralytics import YOLO
import cv2
import pygame
try:
    import RPi.GPIO as GPIO  # Para control de hardware en Raspberry Pi
    RASPBERRY_PI = True
except ImportError:
    RASPBERRY_PI = False
    print("⚠️  RPi.GPIO no disponible - ejecutando en modo desarrollo")

class SistemaVigilanciaAutonomo:
    def __init__(self):
        # Configuración inicial
        self.config = self.cargar_configuracion()
        self.setup_logging()
        self.setup_gpio()
        
        # Estado del sistema
        self.sistema_activo = True
        self.ultimo_heartbeat = time.time()
        self.contador_reinicios = 0
        self.max_reinicios = 5
        
        # Componentes del sistema
        self.modelo = None
        self.cap = None
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
        
        # Configuración de horarios
        self.hora_inicio = self.config.get('hora_inicio', 6)  # 6 AM
        self.hora_fin = self.config.get('hora_fin', 20)       # 8 PM
        
        # Inicializar componentes
        self.inicializar_componentes()
        
        # Configurar manejadores de señales
        signal.signal(signal.SIGTERM, self.manejar_terminacion)
        signal.signal(signal.SIGINT, self.manejar_terminacion)
        
        logging.info("🚀 Sistema de Vigilancia Autónomo iniciado")

    def cargar_configuracion(self):
        """Carga configuración desde archivo JSON"""
        config_path = Path("config_sistema.json")
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
                "pin_led_status": 18,
                "pin_boton_emergencia": 24,
                "pin_buzzer": 25,
                "log_rotation_days": 7,
                "heartbeat_interval": 30
            }
            with open(config_path, 'w') as f:
                json.dump(config_default, f, indent=4)
            return config_default

    def setup_logging(self):
        """Configura sistema de logging robusto"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configurar rotación de logs
        from logging.handlers import RotatingFileHandler
        
        # Logger principal
        self.logger = logging.getLogger('sistema_vigilancia')
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo con rotación
        file_handler = RotatingFileHandler(
            log_dir / 'sistema_vigilancia.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola (solo errores críticos)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Logger para detecciones
        self.detection_logger = logging.getLogger('detecciones')
        detection_handler = RotatingFileHandler(
            log_dir / 'detecciones.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        detection_handler.setFormatter(formatter)
        self.detection_logger.addHandler(detection_handler)
        self.detection_logger.setLevel(logging.INFO)

    def setup_gpio(self):
        """Configura pines GPIO para Raspberry Pi"""
        if not RASPBERRY_PI:
            self.logger.info("Modo desarrollo - GPIO simulado")
            self.pin_led = self.config.get('pin_led_status', 18)
            self.pin_boton = self.config.get('pin_boton_emergencia', 24)
            self.pin_buzzer = self.config.get('pin_buzzer', 25)
            return
            
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # LED de estado
            self.pin_led = self.config.get('pin_led_status', 18)
            GPIO.setup(self.pin_led, GPIO.OUT)
            
            # Botón de emergencia
            self.pin_boton = self.config.get('pin_boton_emergencia', 24)
            GPIO.setup(self.pin_boton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin_boton, GPIO.FALLING, 
                                callback=self.boton_emergencia_presionado, 
                                bouncetime=300)
            
            # Buzzer
            self.pin_buzzer = self.config.get('pin_buzzer', 25)
            GPIO.setup(self.pin_buzzer, GPIO.OUT)
            
            self.logger.info("GPIO configurado correctamente")
        except Exception as e:
            self.logger.error(f"Error configurando GPIO: {e}")

    def inicializar_componentes(self):
        """Inicializa todos los componentes del sistema"""
        try:
            # Inicializar pygame para audio
            pygame.mixer.init()
            
            # Cargar modelo YOLO
            self.modelo = YOLO('best.pt')
            self.logger.info("Modelo YOLO cargado correctamente")
            
            # Inicializar cámara
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("No se pudo abrir la cámara")
            
            # Configurar cámara para mejor rendimiento
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)  # Reducir FPS para ahorrar energía
            
            self.logger.info("Cámara inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando componentes: {e}")
            raise

    def es_horario_activo(self):
        """Verifica si el sistema debe estar activo según la hora"""
        hora_actual = datetime.datetime.now().hour
        return self.hora_inicio <= hora_actual < self.hora_fin

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
            
            # Verificar temperatura (Raspberry Pi)
            try:
                temp = self.leer_temperatura_cpu()
                if temp > 70:
                    self.logger.warning(f"Temperatura alta: {temp}°C")
            except:
                pass
            
            # Verificar espacio en disco
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"Espacio en disco bajo: {disk.percent}%")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando estado del sistema: {e}")
            return False

    def leer_temperatura_cpu(self):
        """Lee la temperatura del CPU de Raspberry Pi"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) / 1000.0
            return temp
        except:
            return 0

    def boton_emergencia_presionado(self, channel):
        """Maneja la presión del botón de emergencia"""
        self.logger.critical("🚨 BOTÓN DE EMERGENCIA PRESIONADO")
        self.activar_senal_emergencia()
        self.reproducir_sonido_emergencia()

    def activar_senal_emergencia(self):
        """Activa señal de emergencia sin internet"""
        try:
            if RASPBERRY_PI:
                # Parpadear LED rápidamente
                for _ in range(10):
                    GPIO.output(self.pin_led, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(self.pin_led, GPIO.LOW)
                    time.sleep(0.1)
                
                # Activar buzzer
                GPIO.output(self.pin_buzzer, GPIO.HIGH)
                time.sleep(2)
                GPIO.output(self.pin_buzzer, GPIO.LOW)
            else:
                # Modo desarrollo - simular señal
                print("🚨 SEÑAL DE EMERGENCIA ACTIVADA (modo desarrollo)")
                for _ in range(10):
                    print("💡 LED parpadeando...")
                    time.sleep(0.1)
                print("🔊 Buzzer activado por 2 segundos")
                time.sleep(2)
            
            # Aquí podrías implementar:
            # - Envío de SMS con módulo GSM
            # - Transmisión LoRa
            # - Señal de radio
            # - Almacenamiento para revisión posterior
            
            self.logger.critical("Señal de emergencia activada")
            
        except Exception as e:
            self.logger.error(f"Error activando señal de emergencia: {e}")

    def reproducir_sonido_emergencia(self):
        """Reproduce sonido de emergencia"""
        try:
            pygame.mixer.music.load("sonido_emergencia.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            self.logger.error(f"Error reproduciendo sonido de emergencia: {e}")

    def manejar_terminacion(self, signum, frame):
        """Maneja la terminación del sistema"""
        self.logger.info(f"Recibida señal {signum}, terminando sistema...")
        self.sistema_activo = False
        self.limpiar_recursos()
        sys.exit(0)

    def limpiar_recursos(self):
        """Limpia todos los recursos del sistema"""
        try:
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            if RASPBERRY_PI:
                GPIO.cleanup()
            self.logger.info("Recursos limpiados correctamente")
        except Exception as e:
            self.logger.error(f"Error limpiando recursos: {e}")

    def reiniciar_sistema(self):
        """Reinicia el sistema automáticamente"""
        self.contador_reinicios += 1
        self.logger.warning(f"Reiniciando sistema (intento {self.contador_reinicios}/{self.max_reinicios})")
        
        if self.contador_reinicios >= self.max_reinicios:
            self.logger.critical("Máximo número de reinicios alcanzado, activando señal de emergencia")
            self.activar_senal_emergencia()
            return False
        
        # Limpiar recursos actuales
        self.limpiar_recursos()
        time.sleep(5)  # Esperar antes de reiniciar
        
        # Reinicializar componentes
        try:
            self.inicializar_componentes()
            self.contador_reinicios = 0  # Reset contador si reinicio exitoso
            return True
        except Exception as e:
            self.logger.error(f"Error en reinicio: {e}")
            return False

    def tomar_frame(self):
        """Captura frame de la cámara"""
        try:
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Error capturando frame")
            
            return {
                "camara1": frame.copy(),
                "camara2": frame.copy()
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
                if RASPBERRY_PI:
                    # Actualizar LED de estado
                    GPIO.output(self.pin_led, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(self.pin_led, GPIO.LOW)
                else:
                    # Modo desarrollo - simular heartbeat
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
            
            while self.sistema_activo:
                try:
                    # Verificar si es horario activo
                    if not self.es_horario_activo():
                        self.logger.info("Fuera del horario activo, sistema en standby")
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
                    if not self.reiniciar_sistema():
                        break
                    time.sleep(5)
                    
        except Exception as e:
            self.logger.critical(f"Error crítico en sistema: {e}")
            self.activar_senal_emergencia()
        finally:
            self.limpiar_recursos()

def main():
    """Función principal"""
    sistema = None
    try:
        sistema = SistemaVigilanciaAutonomo()
        sistema.ejecutar_sistema()
    except KeyboardInterrupt:
        print("\nSistema interrumpido por usuario")
    except Exception as e:
        print(f"Error crítico: {e}")
        if sistema:
            sistema.activar_senal_emergencia()
    finally:
        if sistema:
            sistema.limpiar_recursos()

if __name__ == "__main__":
    main()
