# 🚨 Sistema de Vigilancia Autónomo SADA

Sistema de vigilancia inteligente diseñado para funcionamiento autónomo en exteriores con Raspberry Pi y panel solar.

## 🎯 Características Principales

### ✅ **Funcionalidades Implementadas**
- **Detección Multi-ROI**: Una cámara con dos regiones de interés independientes
- **Reinicio Automático**: Sistema robusto que se recupera automáticamente de errores
- **Señal de Emergencia**: Sistema SMS sin internet para alertas críticas
- **Apagado Nocturno**: Funcionamiento solo en horarios útiles
- **Monitoreo de Salud**: Supervisión continua del estado del sistema
- **Optimización Energética**: Ajustes automáticos para panel solar
- **Servicio Systemd**: Inicio automático y gestión como servicio
- **Logging Robusto**: Sistema de logs con rotación automática

### 🔧 **Tecnologías Utilizadas**
- **YOLO**: Detección de objetos en tiempo real
- **OpenCV**: Procesamiento de video
- **Pygame**: Reproducción de sonidos
- **RPi.GPIO**: Control de hardware Raspberry Pi
- **Systemd**: Gestión de servicios
- **GSM Module**: Comunicación SMS sin internet

## 📁 Estructura del Proyecto

```
proyecto_snow/
├── main_bateria.py                   # Sistema principal con gestión de batería
├── sistema_vigilancia_autonomo.py    # Sistema autónomo para Raspberry Pi
├── simulador_bateria.py              # Simulador de batería para desarrollo
├── optimizador_energia.py            # Optimización energética
├── config/                           # Configuraciones
│   ├── config_sistema.json          # Configuración principal
│   ├── config_sms.json              # Configuración SMS
│   ├── config_energia.json          # Configuración energía
│   └── config_bateria.json          # Configuración batería
├── documentacion/                    # Documentación del sistema
│   ├── sistema_vigilancia.service   # Servicio systemd
│   ├── README_SISTEMA_SADA.md       # Esta documentación
│   └── INSTRUCCIONES_FINALES.md     # Instrucciones de uso
├── instalar_sistema.sh               # Script de instalación
├── best.pt                           # Modelo YOLO
├── sonido_prueva0.mp3                # Sonido cámara 1
├── sonido_prueva2.mp3                # Sonido cámara 2
└── logs/                             # Directorio de logs (se genera automáticamente)
```

## 🚀 Instalación y Configuración

### 1. **Instalación Automática**
```bash
# Hacer ejecutable el script de instalación
chmod +x instalar_sistema.sh

# Ejecutar instalación
./instalar_sistema.sh

# Reiniciar el sistema
sudo reboot
```

### 2. **Instalación Manual**
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3-pip python3-venv python3-dev libopencv-dev python3-opencv

# Instalar dependencias Python
pip3 install ultralytics opencv-python pygame psutil numpy torch torchvision

# Configurar servicio
sudo cp sistema_vigilancia.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sistema_vigilancia.service
```

## ⚙️ Configuración

### **Configuración Principal** (`config_sistema.json`)
```json
{
    "hora_inicio": 6,           // Hora de inicio (6 AM)
    "hora_fin": 20,             // Hora de fin (8 PM)
    "umbral_confianza": 0.83,   // Umbral de detección (83%)
    "ventana_tiempo": 5,        // Ventana de confirmación (5 seg)
    "max_reinicios": 5,         // Máximo reinicios automáticos
    "pin_led_status": 18,       // Pin GPIO para LED de estado
    "pin_boton_emergencia": 24, // Pin GPIO para botón emergencia
    "pin_buzzer": 25            // Pin GPIO para buzzer
}
```

### **Configuración SMS** (`config_sms.json`)
```json
{
    "puerto_serial": "/dev/ttyUSB0",
    "velocidad": 9600,
    "pin_sim": "1234",
    "numero_emergencia": "+1234567890",
    "mensaje_emergencia": "🚨 ALERTA SADA: Sistema con problemas críticos"
}
```

### **Configuración Energía** (`config_energia.json`)
```json
{
    "modo_ahorro_activo": true,
    "fps_ahorro": 10,
    "resolucion_ahorro": [320, 240],
    "temperatura_max": 65,
    "bateria_minima": 20,
    "horario_ahorro": {
        "inicio": 22,
        "fin": 6
    }
}
```

## 🎮 Uso del Sistema

### **Comandos Principales**
```bash
# Iniciar sistema principal
python3 main_bateria.py

# O iniciar sistema autónomo
python3 sistema_vigilancia_autonomo.py

# Ver estado del servicio (si está como servicio)
sudo systemctl status sistema_vigilancia

# Ver logs en tiempo real
sudo journalctl -u sistema_vigilancia -f
```

### **Gestión del Servicio**
```bash
# Iniciar servicio
sudo systemctl start sistema_vigilancia

# Parar servicio
sudo systemctl stop sistema_vigilancia

# Reiniciar servicio
sudo systemctl restart sistema_vigilancia

# Habilitar inicio automático
sudo systemctl enable sistema_vigilancia

# Deshabilitar inicio automático
sudo systemctl disable sistema_vigilancia
```

## 🔌 Hardware Requerido

### **Componentes Principales**
- **Raspberry Pi 4** (recomendado) o Pi 3B+
- **Cámara USB** o módulo de cámara oficial
- **Panel Solar** (20W mínimo)
- **Batería** (10Ah mínimo)
- **Controlador de carga** solar
- **Módulo GSM** (opcional, para SMS)

### **Componentes Opcionales**
- **LED de estado** (conectado a GPIO 18)
- **Botón de emergencia** (conectado a GPIO 24)
- **Buzzer** (conectado a GPIO 25)
- **Sensor de temperatura** DS18B20
- **Módulo LoRa** (alternativa a GSM)

## 🔧 Configuración de Hardware

### **Conexiones GPIO**
```
GPIO 18  → LED de estado (con resistencia 220Ω)
GPIO 24  → Botón de emergencia (con pull-up interno)
GPIO 25  → Buzzer (con transistor de control)
GPIO 2/3 → I2C (para sensores adicionales)
```

### **Módulo GSM (Opcional)**
```
VCC  → 5V
GND  → GND
TX   → GPIO 14 (UART TX)
RX   → GPIO 15 (UART RX)
```

## 📊 Monitoreo y Logs

### **Archivos de Log**
- `logs/sistema_vigilancia.log` - Log principal del sistema
- `logs/detecciones.log` - Log de detecciones y alarmas
- `logs/sistema_sms.log` - Log del sistema SMS
- `logs/optimizador_energia.log` - Log de optimización energética

### **Monitoreo del Sistema**
```bash
# Ver temperatura del CPU
vcgencmd measure_temp

# Ver uso de CPU y memoria
htop

# Ver espacio en disco
df -h

# Ver logs del sistema
tail -f logs/sistema_vigilancia.log
```

## 🚨 Sistema de Emergencia

### **Activación Manual**
- Presionar botón de emergencia (GPIO 24)
- El sistema enviará SMS de alerta
- Se activará buzzer y LED de estado

### **Activación Automática**
- Fallo crítico del sistema
- Máximo número de reinicios alcanzado
- Temperatura excesiva del CPU
- Batería muy baja

## 🔋 Optimización Energética

### **Modos de Funcionamiento**
1. **Modo Rendimiento**: Máxima calidad, mayor consumo
2. **Modo Normal**: Balance entre calidad y consumo
3. **Modo Ahorro**: Mínimo consumo, calidad reducida

### **Ajustes Automáticos**
- **Frecuencia CPU**: 1500MHz → 600MHz en modo ahorro
- **FPS Cámara**: 15fps → 10fps en modo ahorro
- **Resolución**: 640x480 → 320x240 en modo ahorro
- **Componentes**: Desactivación de servicios innecesarios

## 🛠️ Mantenimiento

### **Tareas Regulares**
```bash
# Backup de logs (automático cada día a las 2 AM)
./backup_logs.sh

# Limpieza de logs antiguos (automático)
find logs/ -name "*.log" -mtime +7 -delete

# Verificación del sistema
./monitoreo_sistema.sh
```

### **Actualización del Sistema**
```bash
# Actualizar código
git pull origin main

# Reiniciar servicio
sudo systemctl restart sistema_vigilancia
```

## 🔍 Solución de Problemas

### **Problemas Comunes**

#### **Cámara no funciona**
```bash
# Verificar dispositivos USB
lsusb

# Verificar permisos
sudo usermod -a -G video pi

# Reiniciar servicio
sudo systemctl restart sistema_vigilancia
```

#### **Sistema no inicia automáticamente**
```bash
# Verificar servicio
sudo systemctl status sistema_vigilancia

# Verificar logs
sudo journalctl -u sistema_vigilancia

# Reinstalar servicio
sudo systemctl disable sistema_vigilancia
sudo systemctl enable sistema_vigilancia
```

#### **Alto consumo de energía**
```bash
# Verificar configuración de energía
cat config_energia.json

# Activar modo ahorro manualmente
python3 optimizador_energia.py
```

### **Logs de Diagnóstico**
```bash
# Ver errores del sistema
grep "ERROR" logs/sistema_vigilancia.log

# Ver detecciones recientes
tail -20 logs/detecciones.log

# Ver estado del servicio
sudo journalctl -u sistema_vigilancia --since "1 hour ago"
```

## 📈 Rendimiento y Métricas

### **Métricas Típicas**
- **CPU**: 30-60% en funcionamiento normal
- **Memoria**: 200-400MB RAM
- **Temperatura**: 45-65°C
- **Consumo**: 2-4W en modo normal, 1-2W en modo ahorro

### **Optimizaciones Recomendadas**
- Usar tarjeta SD clase 10 o superior
- Configurar swap de 512MB
- Usar fuente de alimentación de 5V 3A
- Mantener ventilación adecuada

## 🔒 Seguridad

### **Medidas Implementadas**
- Ejecución con usuario no privilegiado
- Protección de archivos de configuración
- Logs de auditoría
- Reinicio automático en caso de fallos

### **Recomendaciones**
- Cambiar contraseñas por defecto
- Configurar firewall si es necesario
- Mantener sistema actualizado
- Backup regular de configuraciones

## 📞 Soporte

### **Información del Sistema**
- **Versión**: 1.0
- **Autor**: Sistema SADA
- **Fecha**: 2025
- **Licencia**: Uso interno

### **Contacto**
Para soporte técnico o consultas sobre el sistema, contactar al equipo de desarrollo.

---

## 🎯 Resumen de Mejoras Implementadas

✅ **Sistema robusto con una sola cámara y dos ROIs**  
✅ **Reinicio automático en caso de errores**  
✅ **Sistema de emergencia SMS sin internet**  
✅ **Apagado automático nocturno**  
✅ **Monitoreo de salud del sistema**  
✅ **Optimización para panel solar**  
✅ **Servicio systemd para inicio automático**  
✅ **Logging robusto con rotación**  
✅ **Scripts de instalación y mantenimiento**  
✅ **Documentación completa**  

El sistema está listo para funcionamiento autónomo en exteriores con todas las funcionalidades solicitadas implementadas y probadas.
