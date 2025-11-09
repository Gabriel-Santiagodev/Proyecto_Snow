import logging
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import time
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
            self.font = ImageFont.truetype("arial.ttf", 14)
            self.font_small = ImageFont.truetype("arial.ttf", 12)
        except IOError:
            self.font = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            logger.warning("Arial font not found. Using default Pillow font.")
        
        self.COLOR_BG = (0, 0, 0)
        self.COLOR_TEXT = (180, 255, 180)
        self.COLOR_ERROR = (255, 120, 120)
        cv2.namedWindow(self.window_name)
        logger.info("OLED Simulator initialized.")

    def _pil_to_cv2(self, pil_image):
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _create_image(self):
        return Image.new('RGB', (self.width, self.height), self.COLOR_BG)

    def display_main_screen(self):
        image = self._create_image()
        draw = ImageDraw.Draw(image)
        text = "PROYECTO SNOW"
        text_bbox = draw.textbbox((0, 0), text, font=self.font)
        position = ((self.width - (text_bbox[2] - text_bbox[0])) / 2, (self.height - (text_bbox[3] - text_bbox[1])) / 2)
        draw.text(position, text, font=self.font, fill=self.COLOR_TEXT)
        cv2.imshow(self.window_name, self._pil_to_cv2(image))

    def display_error_screen(self, errors, dropped_count):
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
    logger.info("Module 'oled_module' started")

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

    logger.info("Module 'oled_module' stopped")
    cv2.destroyAllWindows()