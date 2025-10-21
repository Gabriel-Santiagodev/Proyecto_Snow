#!/usr/bin/env python3
"""
Sistema de Emergencia SMS para Vigilancia Autónoma
Utiliza módulo GSM para enviar alertas sin internet
"""

import serial
import time
import logging
import json
from datetime import datetime

class SistemaEmergenciaSMS:
    def __init__(self, config_file="config/config_sms.json"):
        self.config = self.cargar_configuracion(config_file)
        self.setup_logging()
        self.serial_connection = None
        self.inicializar_modulo_gsm()
    
    def cargar_configuracion(self, config_file):
        """Carga configuración del módulo SMS"""
        try:
            with open(config_file, 'r') as f:       # Abre elarchivo json y lo carga a la variable f
                return json.load(f)
        except FileNotFoundError:                   # En dado caso que no exista el arcvo tiene una configuaracion por default
            # Configuración por defecto
            config_default = {
                "puerto_serial": "/dev/ttyUSB0",
                "velocidad": 9600,
                "pin_sim": "1234",
                "numero_emergencia": "+1234567890",
                "mensaje_emergencia": "🚨 ALERTA SADA: Sistema de vigilancia con problemas críticos",
                "timeout_comando": 5,
                "max_reintentos": 3
            }
            with open(config_file, 'w') as f:       # Carga los datos por default 
                json.dump(config_default, f, indent=4)
            return config_default   # Returna la configuracion 
    
    def setup_logging(self):        # Configuracion de logging 
        """Configura logging para el sistema SMS"""
        logging.basicConfig(
            filename='logs/sistema_sms.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def inicializar_modulo_gsm(self):
        """Inicializa conexión con módulo GSM"""
        try:
            self.serial_connection = serial.Serial(
                port=self.config['puerto_serial'],          # /dev/ttyUSB0      el puerto al que está conectado el módulo
                baudrate=self.config['velocidad'],          # 9600              la tasa de transmisión (baudrate)
                timeout=self.config['timeout_comando']      # 5                 el tiempo máximo de espera al leer datos del puerto
            )
            time.sleep(2)  # Esperar inicialización
            
            # Verificar conexión
            if self.verificar_conexion():
                self.logger.info("Módulo GSM inicializado correctamente")
                return True
            else:
                self.logger.error("Error verificando conexión GSM")
                return False
                
        except Exception as e:
            self.logger.error(f"Error inicializando módulo GSM: {e}")
            return False
    
    def verificar_conexion(self):
        """Verifica si el módulo GSM responde"""
        try:
            self.enviar_comando("AT")
            respuesta = self.leer_respuesta()
            return "OK" in respuesta
        except Exception as e:
            self.logger.error(f"Error verificando conexión: {e}")
            return False
    
    def enviar_comando(self, comando):
        """Envía comando AT al módulo GSM"""
        try:
            comando_bytes = (comando + '\r\n').encode('utf-8')
            self.serial_connection.write(comando_bytes)
            self.serial_connection.flush()
            time.sleep(0.5)
        except Exception as e:
            self.logger.error(f"Error enviando comando {comando}: {e}")
    
    def leer_respuesta(self, timeout=None):
        """Lee respuesta del módulo GSM"""
        try:
            if timeout:
                self.serial_connection.timeout = timeout
            
            respuesta = ""
            start_time = time.time()
            
            while time.time() - start_time < (timeout or self.config['timeout_comando']):
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    respuesta += data.decode('utf-8', errors='ignore')
                
                if "OK" in respuesta or "ERROR" in respuesta:
                    break
                    
                time.sleep(0.1)
            
            return respuesta.strip()
            
        except Exception as e:
            self.logger.error(f"Error leyendo respuesta: {e}")
            return ""
    
    def configurar_modulo(self):
        """Configura el módulo GSM para SMS"""
        try:
            comandos_config = [
                "AT+CMGF=1",  # Modo texto
                "AT+CNMI=1,2,0,0,0",  # Configurar notificaciones SMS
                "AT+CSMP=17,167,0,0",  # Configurar formato SMS
            ]
            
            for comando in comandos_config:
                self.enviar_comando(comando)
                respuesta = self.leer_respuesta()
                if "OK" not in respuesta:
                    self.logger.warning(f"Comando {comando} no respondió OK: {respuesta}")
            
            # Verificar PIN de SIM
            self.enviar_comando(f"AT+CPIN={self.config['pin_sim']}")
            respuesta = self.leer_respuesta()
            
            if "OK" in respuesta:
                self.logger.info("SIM configurada correctamente")
                return True
            else:
                self.logger.error(f"Error configurando SIM: {respuesta}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configurando módulo: {e}")
            return False
    
    def verificar_senal(self):
        """Verifica la calidad de señal"""
        try:
            self.enviar_comando("AT+CSQ")
            respuesta = self.leer_respuesta()
            
            if "+CSQ:" in respuesta:
                # Extraer valor de señal
                signal_strength = respuesta.split("+CSQ: ")[1].split(",")[0]
                signal_db = int(signal_strength) * 2 - 113  # Convertir a dBm
                
                self.logger.info(f"Señal GSM: {signal_db} dBm")
                return signal_db
            else:
                self.logger.warning("No se pudo obtener información de señal")
                return None
                
        except Exception as e:
            self.logger.error(f"Error verificando señal: {e}")
            return None
    
    def enviar_sms_emergencia(self, mensaje_personalizado=None):
        """Envía SMS de emergencia"""
        try:
            # Verificar señal
            if self.verificar_senal() is None:
                self.logger.error("No hay señal GSM disponible")
                return False
            
            # Configurar módulo
            if not self.configurar_modulo():
                self.logger.error("Error configurando módulo para SMS")
                return False
            
            # Preparar mensaje
            mensaje = mensaje_personalizado or self.config['mensaje_emergencia']
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mensaje_completo = f"{mensaje}\n\nTimestamp: {timestamp}\nSistema: SADA Vigilancia"
            
            # Enviar SMS
            numero = self.config['numero_emergencia']
            
            self.enviar_comando(f'AT+CMGS="{numero}"')
            time.sleep(1)
            
            # Enviar mensaje
            mensaje_bytes = (mensaje_completo + '\x1A').encode('utf-8')
            self.serial_connection.write(mensaje_bytes)
            self.serial_connection.flush()
            
            # Leer respuesta
            respuesta = self.leer_respuesta(timeout=30)
            
            if "OK" in respuesta:
                self.logger.info(f"SMS de emergencia enviado a {numero}")
                return True
            else:
                self.logger.error(f"Error enviando SMS: {respuesta}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando SMS de emergencia: {e}")
            return False
    
    def enviar_sms_deteccion(self, camara, confianza):
        """Envía SMS cuando se detecta algo"""
        try:
            mensaje = f"🚨 DETECCIÓN SADA\nCámara: {camara}\nConfianza: {confianza:.1f}%\nHora: {datetime.now().strftime('%H:%M:%S')}"
            return self.enviar_sms_emergencia(mensaje)
        except Exception as e:
            self.logger.error(f"Error enviando SMS de detección: {e}")
            return False
    
    def enviar_sms_estado_sistema(self, estado):
        """Envía SMS con estado del sistema"""
        try:
            mensaje = f"📊 ESTADO SISTEMA SADA\nEstado: {estado}\nHora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return self.enviar_sms_emergencia(mensaje)
        except Exception as e:
            self.logger.error(f"Error enviando SMS de estado: {e}")
            return False
    
    def cerrar_conexion(self):
        """Cierra conexión serial"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.logger.info("Conexión GSM cerrada")
        except Exception as e:
            self.logger.error(f"Error cerrando conexión: {e}")

# Función para integración con el sistema principal
def enviar_alerta_emergencia(mensaje="Sistema con problemas críticos"):
    """Función simple para enviar alerta de emergencia"""
    try:
        sms_system = SistemaEmergenciaSMS()
        resultado = sms_system.enviar_sms_emergencia(mensaje)
        sms_system.cerrar_conexion()
        return resultado
    except Exception as e:
        logging.error(f"Error en alerta de emergencia: {e}")
        return False

if __name__ == "__main__":
    # Prueba del sistema SMS
    print("🧪 Probando Sistema SMS de Emergencia...")
    
    sms = SistemaEmergenciaSMS()
    
    if sms.verificar_conexion():
        print("✅ Módulo GSM conectado")
        
        if sms.configurar_modulo():
            print("✅ Módulo configurado")
            
            if sms.enviar_sms_emergencia("🧪 Prueba del sistema SMS SADA"):
                print("✅ SMS de prueba enviado")
            else:
                print("❌ Error enviando SMS")
        else:
            print("❌ Error configurando módulo")
    else:
        print("❌ Error conectando con módulo GSM")
    
    sms.cerrar_conexion()
