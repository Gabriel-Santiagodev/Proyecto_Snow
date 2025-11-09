#!/usr/bin/env python3
"""
Simulador de Batería Solar para Sistema de Vigilancia Autónomo
Simula una batería 12V 150Ah (1800Wh) con panel solar 440W
Diseñado para desarrollo y pruebas sin hardware real
"""

import time
import json
import random
import logging
from datetime import datetime
from pathlib import Path

class SimuladorBateria:
    def __init__(self, config_file="config/config_bateria.json"):
        self.config = self.cargar_configuracion(config_file)
        self.setup_logging()
        
        # Especificaciones de hardware (tu sistema real)
        self.capacidad_total = 1800  # Wh (12V x 150Ah)
        self.voltaje_nominal = 12.0  # Voltios
        self.panel_solar_watts = 440  # Watts
        
        # Estado actual de la batería
        self.carga_actual = self.capacidad_total * 0.85  # Comienza al 85%
        self.voltaje_actual = 12.5  # Voltios
        
        # Consumo del sistema (Watts)
        self.consumo_dos_camaras = 10  # W
        self.consumo_una_camara = 8    # W
        self.consumo_standby = 3       # W
        self.consumo_actual = self.consumo_dos_camaras
        
        # Estado del sistema
        self.camaras_activas = 2
        self.sistema_activo = True
        self.clima_actual = "soleado"  # soleado, parcial, nublado, lluvioso
        
        # Estadísticas
        self.tiempo_inicio = time.time()
        self.total_consumido = 0
        self.total_generado = 0
        
        self.logger.info("🔋 Simulador de batería inicializado")
        self.logger.info(f"📊 Capacidad: {self.capacidad_total}Wh, Panel: {self.panel_solar_watts}W")
    
    def cargar_configuracion(self, config_file):
        """Carga configuración del simulador"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            config_default = {
                "velocidad_simulacion": 60,  # 1 minuto real = 60 minutos simulados
                "variacion_consumo": 0.1,    # ±10% variación aleatoria
                "horas_sol_promedio": 6,     # Horas de sol en Querétaro
                "eficiencia_panel": 0.75,    # 75% eficiencia real del panel
                "profundidad_descarga_max": 0.8,  # 80% DOD máximo
                "temperatura_ambiente": 25,   # °C
                "ubicacion": "Queretaro"
            }
            Path("config").mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config_default, f, indent=4)
            return config_default
    
    def setup_logging(self):
        """Configura sistema de logging"""
        Path("logs").mkdir(exist_ok=True)
        logging.basicConfig(
            filename='logs/simulador_bateria.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def obtener_hora_simulada(self):
        """Obtiene la hora del día simulada"""
        # Para desarrollo, usa hora real del sistema
        return datetime.now().hour + datetime.now().minute / 60.0
    
    def calcular_intensidad_solar(self):
        """Calcula la intensidad solar según hora del día y clima"""
        hora = self.obtener_hora_simulada()
        
        # Curva de intensidad solar (0-1)
        if 6 <= hora < 8:  # Amanecer
            intensidad_base = (hora - 6) / 2
        elif 8 <= hora < 12:  # Mañana
            intensidad_base = 0.5 + (hora - 8) / 8
        elif 12 <= hora < 14:  # Mediodía (pico)
            intensidad_base = 1.0
        elif 14 <= hora < 18:  # Tarde
            intensidad_base = 1.0 - (hora - 14) / 8
        elif 18 <= hora < 20:  # Atardecer
            intensidad_base = 0.5 - (hora - 18) / 4
        else:  # Noche
            intensidad_base = 0
        
        # Ajustar por clima
        factor_clima = {
            "soleado": 1.0,
            "parcial": 0.7,
            "nublado": 0.3,
            "lluvioso": 0.1
        }
        
        intensidad = intensidad_base * factor_clima.get(self.clima_actual, 1.0)
        
        # Agregar variación aleatoria
        variacion = random.uniform(-0.1, 0.1)
        intensidad = max(0, min(1.0, intensidad + variacion))
        
        return intensidad
    
    def calcular_generacion_solar(self, delta_tiempo_horas):
        """Calcula energía generada por el panel solar"""
        intensidad = self.calcular_intensidad_solar()
        eficiencia = self.config['eficiencia_panel']
        
        # Potencia generada (Watts)
        potencia = self.panel_solar_watts * intensidad * eficiencia
        
        # Energía generada (Wh)
        energia = potencia * delta_tiempo_horas
        
        return energia, potencia
    
    def calcular_consumo(self, delta_tiempo_horas):
        """Calcula energía consumida por el sistema"""
        # Consumo base según cámaras activas
        if not self.sistema_activo:
            consumo_base = self.consumo_standby
        elif self.camaras_activas == 2:
            consumo_base = self.consumo_dos_camaras
        else:
            consumo_base = self.consumo_una_camara
        
        # Variación aleatoria del consumo (±10%)
        variacion = random.uniform(
            1 - self.config['variacion_consumo'],
            1 + self.config['variacion_consumo']
        )
        
        consumo_watts = consumo_base * variacion
        self.consumo_actual = consumo_watts
        
        # Energía consumida (Wh)
        energia = consumo_watts * delta_tiempo_horas
        
        return energia, consumo_watts
    
    def actualizar_bateria(self, delta_tiempo_segundos=1):
        """Actualiza el estado de la batería"""

        delta_tiempo_horas = delta_tiempo_segundos / 3600.0
        
        # Calcular generación solar
        energia_generada, potencia_solar = self.calcular_generacion_solar(delta_tiempo_horas)
        
        # Calcular consumo
        energia_consumida, potencia_consumo = self.calcular_consumo(delta_tiempo_horas)
        
        # Balance energético
        balance = energia_generada - energia_consumida
        
        # Actualizar carga
        self.carga_actual += balance
        
        # Limitar carga entre 0 y capacidad total
        self.carga_actual = max(0, min(self.capacidad_total, self.carga_actual))
        
        # Actualizar estadísticas
        self.total_generado += energia_generada
        self.total_consumido += energia_consumida
        
        # Actualizar voltaje (basado en porcentaje de carga)
        self.actualizar_voltaje()
        
        return {
            'generacion': energia_generada,
            'consumo': energia_consumida,
            'balance': balance,
            'potencia_solar': potencia_solar,
            'potencia_consumo': potencia_consumo
        }
    
    def actualizar_voltaje(self):
        """Calcula voltaje según carga de batería AGM"""
        porcentaje = self.obtener_porcentaje()
        
        # Curva de descarga típica para batería AGM 12V
        if porcentaje >= 100:
            self.voltaje_actual = 12.8
        elif porcentaje >= 90:
            self.voltaje_actual = 12.7
        elif porcentaje >= 70:
            self.voltaje_actual = 12.5
        elif porcentaje >= 50:
            self.voltaje_actual = 12.3
        elif porcentaje >= 30:
            self.voltaje_actual = 12.0
        elif porcentaje >= 20:
            self.voltaje_actual = 11.8
        else:
            self.voltaje_actual = 11.5 + (porcentaje / 20) * 0.3
    
    def obtener_porcentaje(self):
        """Obtiene porcentaje de carga actual"""
        return (self.carga_actual / self.capacidad_total) * 100
    
    def obtener_estado(self):
        """Obtiene estado completo de la batería"""
        porcentaje = self.obtener_porcentaje()
        intensidad_solar = self.calcular_intensidad_solar()
        hora = self.obtener_hora_simulada()
        
        # Determinar modo recomendado
        if porcentaje >= 70:
            modo = "OPTIMO"
            emoji = "🟢"
        elif porcentaje >= 50:
            modo = "NORMAL"
            emoji = "🟡"
        elif porcentaje >= 35:
            modo = "ECO"
            emoji = "🟠"
        else:
            modo = "EMERGENCIA"
            emoji = "🔴"
        
        return {
            'porcentaje': porcentaje,
            'voltaje': self.voltaje_actual,
            'carga_wh': self.carga_actual,
            'capacidad_wh': self.capacidad_total,
            'consumo_actual': self.consumo_actual,
            'camaras_activas': self.camaras_activas,
            'intensidad_solar': intensidad_solar * 100,
            'clima': self.clima_actual,
            'hora': f"{int(hora):02d}:{int((hora % 1) * 60):02d}",
            'modo_recomendado': modo,
            'emoji_estado': emoji,
            'total_generado': self.total_generado,
            'total_consumido': self.total_consumido
        }
    
    def cambiar_camaras(self, numero_camaras):
        """Cambia número de cámaras activas"""
        if numero_camaras in [1, 2]:
            self.camaras_activas = numero_camaras
            self.logger.info(f"📹 Cámaras activas: {numero_camaras}")
            return True
        return False
    
    def cambiar_clima(self, clima):
        """Cambia condición climática"""
        climas_validos = ["soleado", "parcial", "nublado", "lluvioso"]
        if clima in climas_validos:
            self.clima_actual = clima
            self.logger.info(f"🌤️ Clima cambiado a: {clima}")
            return True
        return False
    
    def apagar_sistema(self):
        """Pone sistema en modo standby"""
        self.sistema_activo = False
        self.logger.info("💤 Sistema en standby")
    
    def encender_sistema(self):
        """Enciende el sistema"""
        self.sistema_activo = True
        self.logger.info("⚡ Sistema activado")
    
    def tiempo_restante_estimado(self):
        """Estima tiempo restante de batería"""
        if self.consumo_actual <= 0:
            return float('inf')
        
        horas = self.carga_actual / self.consumo_actual
        return horas
    
    def generar_reporte(self):
        """Genera reporte del estado actual"""
        estado = self.obtener_estado()
        tiempo_restante = self.tiempo_restante_estimado()
        
        reporte = f"""
╔════════════════════════════════════════════════════════════╗
║            🔋 SIMULADOR DE BATERÍA - PROYECTO SNOW         ║
╚════════════════════════════════════════════════════════════╝

📊 ESTADO DE LA BATERÍA:
  {estado['emoji_estado']} Nivel: {estado['porcentaje']:.1f}% ({estado['carga_wh']:.0f}Wh / {estado['capacidad_wh']:.0f}Wh)
  ⚡ Voltaje: {estado['voltaje']:.2f}V
  🎯 Modo recomendado: {estado['modo_recomendado']}
  ⏱️  Tiempo restante: {tiempo_restante:.1f} horas

⚙️ SISTEMA:
  📹 Cámaras activas: {estado['camaras_activas']}
  🔌 Consumo actual: {estado['consumo_actual']:.1f}W
  
☀️ ENERGÍA SOLAR:
  🌤️ Clima: {estado['clima']}
  📈 Intensidad solar: {estado['intensidad_solar']:.0f}%
  🕐 Hora: {estado['hora']}

📈 ESTADÍSTICAS:
  ⬆️ Total generado: {estado['total_generado']:.1f}Wh
  ⬇️ Total consumido: {estado['total_consumido']:.1f}Wh
  💰 Balance: {estado['total_generado'] - estado['total_consumido']:.1f}Wh

╚════════════════════════════════════════════════════════════╝
        """
        return reporte
    
    def simular_dia_completo(self, velocidad=60):
        """Simula un día completo (24 horas) de forma acelerada"""
        print("🚀 Iniciando simulación de día completo...")
        print(f"⏩ Velocidad: {velocidad}x (1 segundo real = {velocidad} minutos simulados)")
        
        for segundo in range(1440):  # 24 horas = 1440 minutos
            delta_minutos = velocidad  # Minutos simulados por segundo
            delta_segundos = delta_minutos * 60
            
            self.actualizar_bateria(delta_segundos)
            
            # Mostrar estado cada hora simulada
            if segundo % 60 == 0:
                estado = self.obtener_estado()
                print(f"{estado['hora']} - {estado['emoji_estado']} {estado['porcentaje']:.1f}% | "
                      f"☀️ {estado['intensidad_solar']:.0f}% | "
                      f"📹 {estado['camaras_activas']} cams | "
                      f"{estado['modo_recomendado']}")
            
            time.sleep(1)
        
        print("\n✅ Simulación completada")
        print(self.generar_reporte())


# Funciones de utilidad para integración
def crear_simulador():
    """Crea instancia del simulador"""
    return SimuladorBateria()

def leer_nivel_bateria(simulador):
    """Lee nivel de batería (compatible con optimizador_energia.py)"""
    return simulador.obtener_porcentaje()

def leer_voltaje_bateria(simulador):
    """Lee voltaje de batería"""
    return simulador.voltaje_actual


if __name__ == "__main__":
    print("🔋 Simulador de Batería - Proyecto Snow")
    print("=" * 60)
    
    # Crear simulador
    sim = SimuladorBateria()
    
    # Mostrar estado inicial
    print(sim.generar_reporte())
    
    # Menú interactivo
    print("\n🎮 MODO INTERACTIVO")
    print("Comandos:")
    print("  1 - Cambiar a 1 cámara")
    print("  2 - Cambiar a 2 cámaras")
    print("  s - Clima soleado")
    print("  p - Clima parcialmente nublado")
    print("  n - Clima nublado")
    print("  l - Clima lluvioso")
    print("  r - Mostrar reporte")
    print("  d - Simular día completo")
    print("  q - Salir")
    
    try:
        while True:
            comando = input("\n> ").lower()
            
            if comando == '1':
                sim.cambiar_camaras(1)
                print("✅ Cambiado a 1 cámara")
            elif comando == '2':
                sim.cambiar_camaras(2)
                print("✅ Cambiado a 2 cámaras")
            elif comando == 's':
                sim.cambiar_clima("soleado")
                print("✅ Clima: Soleado")
            elif comando == 'p':
                sim.cambiar_clima("parcial")
                print("✅ Clima: Parcialmente nublado")
            elif comando == 'n':
                sim.cambiar_clima("nublado")
                print("✅ Clima: Nublado")
            elif comando == 'l':
                sim.cambiar_clima("lluvioso")
                print("✅ Clima: Lluvioso")
            elif comando == 'r':
                print(sim.generar_reporte())
            elif comando == 'd':
                sim.simular_dia_completo(velocidad=60)
            elif comando == 'q':
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Comando no reconocido")
            
            # Actualizar batería (1 minuto)
            sim.actualizar_bateria(60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Simulador detenido")