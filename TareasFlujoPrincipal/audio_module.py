from os import environ
environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import logging, pygame, time
import ModulosGenerales.modulo_logging as modulo_logging

modulo_logging.setup_logging()
logger = logging.getLogger("snow").getChild("audio_module")

class AudioSystem:
    def __init__(self, audio_file):
        pygame.init()
        pygame.mixer.init()
        self.audio_file = audio_file
        self.cola_de_reproduccion = 0
        logger.info("[AudioSystem] Sistema inicializado.")
        logger.info(f"[AudioSystem] Archivo de audio configurado: {self.audio_file}")

    def activar_reproduccion(self):
        logger.info("\n=> [AudioSystem] Señal de activación recibida.")
        if pygame.mixer.music.get_busy():
            self.cola_de_reproduccion += 1
            logger.info(f"[AudioSystem] Audio en curso. Encolando. Pendientes: {self.cola_de_reproduccion}")
        else:
            try:
                pygame.mixer.music.load(self.audio_file)
                pygame.mixer.music.set_volume(0.01)
                pygame.mixer.music.play()
                logger.info("[AudioSystem] Reproduciendo instrucción.")
            except pygame.error as e:
                logger.error(f"[AudioSystem] No se pudo cargar o reproducir el audio: {e}")

    def gestionar_cola(self):
        if not pygame.mixer.music.get_busy() and self.cola_de_reproduccion > 0:
            print("[AudioSystem] Audio terminado, reproduciendo siguiente de la cola...")
            self.cola_de_reproduccion -= 1
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
            logger.info(f"[AudioSystem] Audios pendientes: {self.cola_de_reproduccion}")

    def cerrar(self):
        pygame.quit()
        logger.info("[AudioSystem] Sistema de audio cerrado.")
                
def run(stop_event,cola_audio):
    logger.info("Module 'audio_module' started")    
    
    pygame.init()
    pygame.mixer.init()
    reproductor = AudioSystem(audio_file="audio.mp3")
    while not stop_event.is_set():
        if not cola_audio.empty():
            cola_audio.get()
            signal = cola_audio.get()
            if signal == "reproducir":
                reproductor.activar_reproduccion()
        reproductor.gestionar_cola()
        time.sleep(0.1)
               
    logger.info("Module 'audio_module' stopped")
    reproductor.cerrar()