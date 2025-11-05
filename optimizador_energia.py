#!/usr/bin/env python3
"""
Optimizador de Energía para Sistema de Vigilancia Autónomo
Diseñado para funcionamiento eficiente con panel solar
"""

import time
import logging
import subprocess       # Biblioteca para ejecutar comandos en la terminal
import psutil           # Biblioteca para leer estado del sistema (Bateria, CPU, Memoria, etc.)
import os
from datetime import datetime, timedelta
import json

class OptimizadorEnergia:
    def __init__(self, config_file="config/config_energia.json"):
        self.config = self.cargar_configuracion(config_file)
        self.setup_logging()
        self.estado_ahorro = False
        self.ultimo_ajuste = time.time()
        
    def cargar_configuracion(self, config_file):
        """Carga configuración de optimización energética"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)                 # Carga los datos
        except FileNotFoundError:           # si no esvuentra el archivo pone por defecto:
            config_default = {
                "modo_ahorro_activo": True,
                "cpu_max_ahorro": 60,
                "fps_ahorro": 10,
                "resolucion_ahorro": [320, 240],
                "temperatura_max": 65,
                "bateria_minima": 20,
                "horario_ahorro": {
                    "inicio": 22,
                    "fin": 6
                },
                "ajustes_dinamicos": True,
                "monitoreo_intervalo": 30
            }
            with open(config_file, 'w') as f:
                json.dump(config_default, f, indent=4)
            return config_default
    
    def setup_logging(self):
        """Configura logging para optimizador"""
        logging.basicConfig(
            filename='logs/optimizador_energia.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def leer_nivel_bateria(self):       # Solo funciona en Raspberry Pi (o Linux)
        """Lee el nivel de batería del sistema"""
        try:
            # Para Raspberry Pi con UPS/batería
            with open('/sys/class/power_supply/battery/capacity', 'r') as f:
                return int(f.read().strip())
        except:
            # Simulación para desarrollo
            return 85
    
    def leer_temperatura_cpu(self):
        """Lee temperatura del CPU"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                return int(f.read()) / 1000.0
        except:
            return 45.0
    
    def ajustar_frecuencia_cpu(self, frecuencia):
        """Ajusta la frecuencia del CPU"""
        try:
            # Para Raspberry Pi
            cmd = f"sudo cpufreq-set -f {frecuencia}MHz"        # Comando en linux para cambiarla frecuencia de CPU:  sudo cpufreq-set -f {frecuencia}MHz
            subprocess.run(cmd, shell=True, check=True)
            self.logger.info(f"Frecuencia CPU ajustada a {frecuencia}MHz")
            return True
        except Exception as e:
            self.logger.error(f"Error ajustando frecuencia CPU: {e}")
            return False
    
    def ajustar_brillo_pantalla(self, brillo):
        """Ajusta el brillo de la pantalla (si existe)"""
        try:
            # Para pantallas compatibles
            cmd = f"sudo sh -c 'echo {brillo} > /sys/class/backlight/rpi_backlight/brightness'"
            subprocess.run(cmd, shell=True, check=True)
            self.logger.info(f"Brillo ajustado a {brillo}")
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
            
            self.logger.info("Componentes innecesarios desactivados")
            return True
            
        except Exception as e:
            self.logger.error(f"Error desactivando componentes: {e}")
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
            
            self.logger.info("Componentes esenciales reactivados")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reactivando componentes: {e}")
            return False
    
    def optimizar_para_ahorro(self):
        """Aplica optimizaciones para ahorro de energía"""
        try:
            self.logger.info("Aplicando optimizaciones de ahorro de energía")
            
            self.ajustar_frecuencia_cpu(600)  # 600MHz en lugar de 1500MHz          Reducir frecuencia CPU
 
            self.ajustar_brillo_pantalla(50)                # Reducir brillo pantalla

            self.desactivar_componentes_innecesarios()      # Desactivar componentes innecesarios
            
            subprocess.run("echo 'powersave' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", 
                         shell=True, check=False)       # Configurar governor de CPU para ahorro
            """
            Este comando cambia el governor del CPU a "powersave", 
            escribiendo ese valor en los archivos /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 
            de todos los núcleos, lo que configura el procesador en modo de bajo consumo energético 
            para reducir el rendimiento y prolongar la autonomía del sistema.
            """
            
            self.estado_ahorro = True
            self.logger.info("Modo ahorro de energía activado")
            return True
            
        except Exception as e:
            self.logger.error(f"Error aplicando optimizaciones: {e}")
            return False
    
    def optimizar_para_rendimiento(self):
        """Aplica optimizaciones para máximo rendimiento"""
        try:
            self.logger.info("Aplicando optimizaciones de rendimiento")

            self.ajustar_frecuencia_cpu(1500)  # 1500MHz            # Aumentar frecuencia CPU

            self.ajustar_brillo_pantalla(100)               # Aumentar brillo pantalla

            self.activar_componentes_esenciales()           # Reactivar componentes
   
            subprocess.run("echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", 
                         shell=True, check=False)       # Configurar governor de CPU para rendimiento
            """
            Este comando cambia el governor del CPU a "performance", 
            escribiendo ese valor en los archivos /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 
            de todos los núcleos, lo que configura el procesador en modo de máximo rendimiento, 
            manteniendo la frecuencia más alta posible a costa de un mayor consumo de energía.
            """
            
            self.estado_ahorro = False
            self.logger.info("Modo rendimiento activado")
            return True
            
        except Exception as e:
            self.logger.error(f"Error aplicando optimizaciones de rendimiento: {e}")
            return False
    
    def es_horario_ahorro(self):
        """Verifica si es horario de ahorro de energía"""
        hora_actual = datetime.now().hour
        inicio_ahorro = self.config['horario_ahorro']['inicio']
        fin_ahorro = self.config['horario_ahorro']['fin']
        
        if inicio_ahorro > fin_ahorro:  # Horario que cruza medianoche
            return hora_actual >= inicio_ahorro or hora_actual < fin_ahorro
        else:
            return inicio_ahorro <= hora_actual < fin_ahorro
    
    def evaluar_estado_sistema(self):
        """Evalúa el estado del sistema para decidir optimizaciones"""
        try:
            # Leer métricas del sistema
            bateria = self.leer_nivel_bateria()
            temperatura = self.leer_temperatura_cpu()
            cpu_uso = psutil.cpu_percent(interval=1)
            memoria = psutil.virtual_memory().percent
            
            # Determinar si necesita ahorro de energía
            necesita_ahorro = (
                bateria < self.config['bateria_minima'] or
                temperatura > self.config['temperatura_max'] or
                self.es_horario_ahorro()
            )
            
            # Determinar si puede usar rendimiento completo
            puede_rendimiento = (
                bateria > 50 and
                temperatura < 60 and
                not self.es_horario_ahorro()
            )
            
            return {
                'bateria': bateria,
                'temperatura': temperatura,
                'cpu_uso': cpu_uso,
                'memoria': memoria,
                'necesita_ahorro': necesita_ahorro,
                'puede_rendimiento': puede_rendimiento
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluando estado del sistema: {e}")
            return None
    
    def ajustar_configuracion_camara(self, estado_sistema):
        """Ajusta configuración de cámara según estado del sistema"""
        try:
            if estado_sistema['necesita_ahorro']:
                # Configuración de ahorro
                fps = self.config['fps_ahorro']
                resolucion = self.config['resolucion_ahorro']
                self.logger.info(f"Ajustando cámara para ahorro: {fps}fps, {resolucion}")
            else:
                # Configuración normal
                fps = 15
                resolucion = [640, 480]
                self.logger.info(f"Ajustando cámara para rendimiento: {fps}fps, {resolucion}")
            
            # Aquí se actualizaría la configuración de la cámara
            # Esto se integraría con el sistema principal
            
            return fps, resolucion
            
        except Exception as e:
            self.logger.error(f"Error ajustando configuración de cámara: {e}")
            return 15, [640, 480]
    
    def monitorear_y_optimizar(self):
        """Función principal de monitoreo y optimización"""
        try:
            estado = self.evaluar_estado_sistema()
            if not estado:
                return
            
            # Log del estado actual
            self.logger.info(f"Estado: Batería={estado['bateria']}%, "
                           f"Temp={estado['temperatura']:.1f}°C, "
                           f"CPU={estado['cpu_uso']:.1f}%")
            
            # Aplicar optimizaciones según el estado
            if estado['necesita_ahorro'] and not self.estado_ahorro:
                self.optimizar_para_ahorro()
            elif estado['puede_rendimiento'] and self.estado_ahorro:
                self.optimizar_para_rendimiento()
            
            # Ajustar configuración de cámara
            fps, resolucion = self.ajustar_configuracion_camara(estado)
            
            # Actualizar timestamp del último ajuste
            self.ultimo_ajuste = time.time()
            
            return {
                'fps': fps,
                'resolucion': resolucion,
                'modo_ahorro': self.estado_ahorro
            }
            
        except Exception as e:
            self.logger.error(f"Error en monitoreo y optimización: {e}")
            return None
    
    def ejecutar_monitoreo_continuo(self):
        """Ejecuta monitoreo continuo en un hilo separado"""
        while True:
            try:
                self.monitorear_y_optimizar()
                time.sleep(self.config['monitoreo_intervalo'])
            except KeyboardInterrupt:
                self.logger.info("Monitoreo de energía interrumpido")
                break
            except Exception as e:
                self.logger.error(f"Error en monitoreo continuo: {e}")
                time.sleep(10)

if __name__ == "__main__":
    # Prueba del optimizador
    print("🔋 Iniciando Optimizador de Energía...")
    
    optimizador = OptimizadorEnergia()
    
    print("📊 Estado actual del sistema:")
    estado = optimizador.evaluar_estado_sistema()
    if estado:
        print(f"  Batería: {estado['bateria']}%")
        print(f"  Temperatura: {estado['temperatura']:.1f}°C")
        print(f"  CPU: {estado['cpu_uso']:.1f}%")
        print(f"  Memoria: {estado['memoria']:.1f}%")
        print(f"  Necesita ahorro: {estado['necesita_ahorro']}")
        print(f"  Puede rendimiento: {estado['puede_rendimiento']}")
    
    print("\n🔧 Aplicando optimizaciones...")
    resultado = optimizador.monitorear_y_optimizar()
    if resultado:
        print(f"  FPS: {resultado['fps']}")
        print(f"  Resolución: {resultado['resolucion']}")
        print(f"  Modo ahorro: {resultado['modo_ahorro']}")
    
    print("✅ Optimizador de energía configurado")
