import logging
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import time
import psutil
import ModulosGenerales.modulo_logging as modulo_logging
from ModulosGenerales.error_buffer import get_recent_errors, get_dropped_errors_count

modulo_logging.setup_logging()
logger = logging.getLogger("snow").getChild("oled_module")

class OLEDSimulator:
    def __init__(self, width=256, height=128):
        self.width = width
        self.height = height
        self.window_name = "Simulador OLED"
        
        try:
            self.font = ImageFont.truetype("arial.ttf", 16)
            self.font_small = ImageFont.truetype("arial.ttf", 11)
            self.font_tiny = ImageFont.truetype("arial.ttf", 10)
        except IOError:
            self.font = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()
            logger.warning("Arial font not found. Using default Pillow font.")
        
        self.COLOR_BG = (0, 0, 0)
        self.COLOR_TEXT = (180, 255, 180)
        self.COLOR_ERROR = (255, 120, 120)
        self.COLOR_WARNING = (255, 200, 100)
        self.COLOR_OK = (100, 255, 100)
        
        cv2.namedWindow(self.window_name)
        logger.info("OLED Simulator initialized.")

    def _pil_to_cv2(self, pil_image):
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _create_image(self):
        return Image.new('RGB', (self.width, self.height), self.COLOR_BG)

    def _get_system_stats(self):
        """Obtiene estadísticas del sistema usando psutil"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': cpu_percent,
                'memory': memory.percent,
                'disk': disk.percent,
                'cpu_warning': cpu_percent > 90,
                'memory_warning': memory.percent > 85,
                'disk_warning': disk.percent > 90
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del sistema: {e}")
            return None

    def display_main_screen(self):
        """Pantalla principal con título y estadísticas del sistema"""
        image = self._create_image()
        draw = ImageDraw.Draw(image)
        
        # Título "PROYECTO SNOW" centrado arriba
        text = "PROYECTO SNOW"
        text_bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        title_x = (self.width - text_width) / 2
        draw.text((title_x, 10), text, font=self.font, fill=self.COLOR_TEXT)
        
        # Obtener estadísticas del sistema
        stats = self._get_system_stats()
        
        if stats:
            # Posición inicial para las estadísticas (debajo del título)
            y_start = 40
            spacing = 18
            
            # CPU
            cpu_color = self.COLOR_WARNING if stats['cpu_warning'] else self.COLOR_OK
            cpu_text = f"CPU: {stats['cpu']:.1f}%"
            if stats['cpu_warning']:
                cpu_text += " ⚠"
            cpu_bbox = draw.textbbox((0, 0), cpu_text, font=self.font_small)
            cpu_width = cpu_bbox[2] - cpu_bbox[0]
            draw.text(((self.width - cpu_width) / 2, y_start), cpu_text, 
                     font=self.font_small, fill=cpu_color)
            
            # Memoria
            memory_color = self.COLOR_WARNING if stats['memory_warning'] else self.COLOR_OK
            memory_text = f"Memoria: {stats['memory']:.1f}%"
            if stats['memory_warning']:
                memory_text += " ⚠"
            memory_bbox = draw.textbbox((0, 0), memory_text, font=self.font_small)
            memory_width = memory_bbox[2] - memory_bbox[0]
            draw.text(((self.width - memory_width) / 2, y_start + spacing), 
                     memory_text, font=self.font_small, fill=memory_color)
            
            # Disco
            disk_color = self.COLOR_WARNING if stats['disk_warning'] else self.COLOR_OK
            disk_text = f"Disco: {stats['disk']:.1f}%"
            if stats['disk_warning']:
                disk_text += " ⚠"
            disk_bbox = draw.textbbox((0, 0), disk_text, font=self.font_small)
            disk_width = disk_bbox[2] - disk_bbox[0]
            draw.text(((self.width - disk_width) / 2, y_start + spacing * 2), 
                     disk_text, font=self.font_small, fill=disk_color)
            
            # Mostrar mensaje si hay alguna advertencia
            if stats['cpu_warning'] or stats['memory_warning'] or stats['disk_warning']:
                warning_text = "¡Sistema con carga alta!"
                warning_bbox = draw.textbbox((0, 0), warning_text, font=self.font_tiny)
                warning_width = warning_bbox[2] - warning_bbox[0]
                draw.text(((self.width - warning_width) / 2, self.height - 15), 
                         warning_text, font=self.font_tiny, fill=self.COLOR_WARNING)
        else:
            # Si no se pueden obtener estadísticas, mostrar mensaje de error
            error_text = "Error obteniendo datos"
            error_bbox = draw.textbbox((0, 0), error_text, font=self.font_small)
            error_width = error_bbox[2] - error_bbox[0]
            draw.text(((self.width - error_width) / 2, 60), error_text, 
                     font=self.font_small, fill=self.COLOR_ERROR)
        
        cv2.imshow(self.window_name, self._pil_to_cv2(image))

    def display_error_screen(self, errors, dropped_count):
        """Pantalla de errores detectados"""
        image = self._create_image()
        draw = ImageDraw.Draw(image)
        draw.text((10, 5), "--- ERRORES DETECTADOS ---", font=self.font, fill=self.COLOR_ERROR)
        y_pos = 30
        max_y = self.height - 20
        
        for error_msg in errors:
            if y_pos + 15 > max_y:
                break
            draw.text((10, y_pos), f"- {error_msg}", font=self.font_small, fill=self.COLOR_TEXT)
            y_pos += 15

        if dropped_count > 0:
            plus_e_text = f"+E (Cantidad de errores: {dropped_count})"
            draw.text((10, y_pos), plus_e_text, font=self.font_small, fill=self.COLOR_ERROR)
        cv2.imshow(self.window_name, self._pil_to_cv2(image))

def run(stop_event):
    oled = OLEDSimulator()
    logger.info("Modulo 'oled_module' iniciado")

    while not stop_event.is_set():
        error_list = get_recent_errors()
        dropped_count = get_dropped_errors_count()
        
        if error_list:
            oled.display_error_screen(error_list, dropped_count)
        else:
            oled.display_main_screen()
        
        key = cv2.waitKey(10) & 0xFF
        if key == 27:
            stop_event.set()
        time.sleep(0.1)

    logger.info("Modulo 'oled_module' detenido")