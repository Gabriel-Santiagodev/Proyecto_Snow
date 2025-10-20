#!/bin/bash

# Script de instalación para Sistema de Vigilancia Autónomo
# Para Raspberry Pi con panel solar

echo "🚀 Instalando Sistema de Vigilancia Autónomo SADA..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si se ejecuta como root
if [ "$EUID" -eq 0 ]; then
    print_error "No ejecutar como root. Usar: sudo -u pi $0"
    exit 1
fi

# Actualizar sistema
print_status "Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
print_status "Instalando dependencias del sistema..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libopencv-dev \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    git \
    vim \
    htop \
    i2c-tools \
    python3-smbus \
    python3-rpi.gpio

# Instalar dependencias de Python
print_status "Instalando dependencias de Python..."
pip3 install --upgrade pip
pip3 install \
    ultralytics \
    opencv-python \
    pygame \
    psutil \
    numpy \
    pillow \
    torch \
    torchvision

# Configurar GPIO
print_status "Configurando GPIO..."
sudo usermod -a -G gpio pi
sudo usermod -a -G i2c pi

# Crear directorios necesarios
print_status "Creando directorios..."
mkdir -p logs
mkdir -p backups
mkdir -p config

# Configurar permisos
print_status "Configurando permisos..."
chmod +x sistema_vigilancia_autonomo.py
chmod +x instalar_sistema.sh
chmod 644 config_sistema.json

# Configurar servicio systemd
print_status "Configurando servicio systemd..."
sudo cp sistema_vigilancia.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sistema_vigilancia.service

# Configurar auto-mount de USB (para backups)
print_status "Configurando auto-mount USB..."
sudo mkdir -p /mnt/usb
echo "/dev/sda1 /mnt/usb vfat defaults,uid=pi,gid=pi,umask=0000 0 0" | sudo tee -a /etc/fstab

# Configurar swap para mejor rendimiento
print_status "Configurando swap..."
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=512/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Configurar overclocking ligero para mejor rendimiento
print_status "Configurando overclocking..."
if ! grep -q "arm_freq=1500" /boot/config.txt; then
    echo "arm_freq=1500" | sudo tee -a /boot/config.txt
    echo "gpu_freq=500" | sudo tee -a /boot/config.txt
    echo "over_voltage=2" | sudo tee -a /boot/config.txt
fi

# Configurar para ahorro de energía
print_status "Configurando ahorro de energía..."
if ! grep -q "dtparam=audio=off" /boot/config.txt; then
    echo "dtparam=audio=off" | sudo tee -a /boot/config.txt
fi

# Configurar watchdog para reinicio automático
print_status "Configurando watchdog..."
sudo modprobe bcm2835_wdt
echo "bcm2835_wdt" | sudo tee -a /etc/modules
sudo systemctl enable watchdog

# Crear script de monitoreo
print_status "Creando script de monitoreo..."
cat > monitoreo_sistema.sh << 'EOF'
#!/bin/bash
# Script de monitoreo del sistema

LOG_FILE="logs/monitoreo.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Verificar temperatura
TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d\' -f1)
echo "[$DATE] Temperatura: ${TEMP}°C" >> $LOG_FILE

# Verificar uso de CPU
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "[$DATE] CPU: ${CPU}%" >> $LOG_FILE

# Verificar memoria
MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
echo "[$DATE] Memoria: ${MEM}%" >> $LOG_FILE

# Verificar espacio en disco
DISK=$(df -h / | awk 'NR==2{printf "%s", $5}' | cut -d'%' -f1)
echo "[$DATE] Disco: ${DISK}%" >> $LOG_FILE

# Verificar estado del servicio
if systemctl is-active --quiet sistema_vigilancia; then
    echo "[$DATE] Servicio: ACTIVO" >> $LOG_FILE
else
    echo "[$DATE] Servicio: INACTIVO" >> $LOG_FILE
    sudo systemctl restart sistema_vigilancia
fi
EOF

chmod +x monitoreo_sistema.sh

# Configurar cron para monitoreo
print_status "Configurando cron para monitoreo..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/pi/protocolo_deteccion/monitoreo_sistema.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * /home/pi/protocolo_deteccion/backup_logs.sh") | crontab -

# Crear script de backup
print_status "Creando script de backup..."
cat > backup_logs.sh << 'EOF'
#!/bin/bash
# Script de backup de logs

BACKUP_DIR="/mnt/usb/backups_$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup de logs
cp -r logs/ $BACKUP_DIR/
cp config_sistema.json $BACKUP_DIR/

# Backup de configuración del sistema
sudo cp /etc/systemd/system/sistema_vigilancia.service $BACKUP_DIR/

# Limpiar logs antiguos (más de 7 días)
find logs/ -name "*.log" -mtime +7 -delete

echo "Backup completado en $BACKUP_DIR"
EOF

chmod +x backup_logs.sh

# Crear script de inicio rápido
print_status "Creando script de inicio rápido..."
cat > iniciar_sistema.sh << 'EOF'
#!/bin/bash
# Script de inicio rápido del sistema

echo "🚀 Iniciando Sistema de Vigilancia Autónomo..."

# Verificar si el servicio está corriendo
if systemctl is-active --quiet sistema_vigilancia; then
    echo "✅ Servicio ya está activo"
    sudo systemctl status sistema_vigilancia
else
    echo "🔄 Iniciando servicio..."
    sudo systemctl start sistema_vigilancia
    sleep 3
    sudo systemctl status sistema_vigilancia
fi

# Mostrar logs en tiempo real
echo "📋 Mostrando logs en tiempo real (Ctrl+C para salir):"
sudo journalctl -u sistema_vigilancia -f
EOF

chmod +x iniciar_sistema.sh

# Crear script de parada
print_status "Creando script de parada..."
cat > parar_sistema.sh << 'EOF'
#!/bin/bash
# Script de parada del sistema

echo "🛑 Deteniendo Sistema de Vigilancia Autónomo..."

sudo systemctl stop sistema_vigilancia
sudo systemctl status sistema_vigilancia

echo "✅ Sistema detenido"
EOF

chmod +x parar_sistema.sh

# Configurar red para mejor estabilidad
print_status "Configurando red..."
sudo tee -a /etc/dhcpcd.conf << 'EOF'

# Configuración para mejor estabilidad de red
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4
EOF

# Configurar para arranque automático
print_status "Configurando arranque automático..."
sudo systemctl enable ssh
sudo systemctl enable systemd-timesyncd

# Crear archivo de estado del sistema
print_status "Creando archivo de estado..."
cat > estado_sistema.txt << EOF
Sistema de Vigilancia Autónomo SADA
====================================
Fecha de instalación: $(date)
Versión: 1.0
Estado: Instalado correctamente

Comandos útiles:
- Iniciar sistema: ./iniciar_sistema.sh
- Parar sistema: ./parar_sistema.sh
- Ver estado: sudo systemctl status sistema_vigilancia
- Ver logs: sudo journalctl -u sistema_vigilancia -f
- Monitoreo: ./monitoreo_sistema.sh

Archivos importantes:
- Configuración: config_sistema.json
- Logs: logs/
- Servicio: /etc/systemd/system/sistema_vigilancia.service

Para reiniciar el sistema completo:
sudo reboot
EOF

print_status "✅ Instalación completada exitosamente!"
print_status "📋 Revisa el archivo estado_sistema.txt para más información"
print_warning "⚠️  Reinicia el sistema para aplicar todas las configuraciones: sudo reboot"

echo ""
echo "🎯 Próximos pasos:"
echo "1. Reiniciar el sistema: sudo reboot"
echo "2. Verificar instalación: ./iniciar_sistema.sh"
echo "3. Configurar horarios en config_sistema.json"
echo "4. Probar el sistema con la cámara"
echo ""
echo "🔧 Para personalizar el sistema, edita config_sistema.json"
