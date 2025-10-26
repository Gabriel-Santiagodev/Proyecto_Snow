# 1. Replace battery import (Line ~40)
# from simulador_bateria import SimuladorBateria
from sensor_bateria_real import SensorBateriaReal

# 2. Change battery initialization (Line ~58)
# self.bateria = SimuladorBateria()
self.bateria = SensorBateriaReal()

# 3. Fix camera initialization (Line ~192)
# self.camara2 = self.camara1
self.camara2 = cv2.VideoCapture(1)  # Real second camera

# 4. Remove test prints (Lines ~130-132)
# Delete or comment out print statements

# 5. Enable battery display if needed (Line ~154)
# Uncomment if you want console output

# 6. Delete cv2.Windows

Hardware checklist:

 Connect INA219 battery sensor
 Install library: pip3 install pi-ina219
 Connect 2 USB cameras
 Test camera indices with ls /dev/video*
 Calibrate umbral_obstruccion threshold
 Set correct timezone on Raspberry Pi

