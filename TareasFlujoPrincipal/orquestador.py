import logging
import time
import ModulosGenerales.modulo_logging as modulo_logging 
"""
from TareasFlujoPrincipal import cameras_module, yolo_module, audio_module, 
from TareasSegundoPlano import oled_module
"""
modulo_logging.setup_logging()
logger = logging.getLogger("snow").getChild("orchestrator")

def run(stop_event):
    """
    Orchestrator: coordina el flujo entre cámaras, YOLO
    y audio, con o sin tracking.
    """

    logger.info("Orquestador iniciado")

    while not stop_event.is_set():
        try:
            """
            CAMARAS -> YOLO -> AUDIO

            toma_tu_frame = cameras_module.get_Frame()
            if toma_tu_frame is None:
                logger.info("No se pudo obtener el frame de la cámara")
                continue
            
            frames_analizados = yolo_module.analyze_frame(toma_tu_frame)

            if not frames_analizados:
                logger.info("No se detectaron objetos en el frame")
                continue
            
            if frames_analizados.get("confianza", 0) > 0.85:
                audio_module.play_audio()
                logger.info("Audio reproduciendose")
            else:
                logger.info("Confianza insuficiente, no se reproduce audio")
            
            time.sleep(0.1)  
            """
            # Con tracking--------------------------------------------------------------------
            """
            CAMARAS -> YOLO -> TRACKING -> AUDIO

            toma_tu_frame = cameras_module.get_Frame()
            if toma_tu_frame is None:
                logger.info("No se pudo obtener el frame de la cámara")
                continue
            
            frames_analizados = yolo_module.analyze_frame(toma_tu_frame)

            if not frames_analizados:
                logger.info("No se detectaron objetos en el frame")
                continue
                
            decision_tracking = tracking_module.apply_tracking(frames_analizados)
            if decision_tracking:
                audio_module.play_audio()
                logger.info("Audio reproduciendose")
            else:
                logger.info("Tracking no aceptado, no se reproduce audio")
            """
        except Exception as e:
            logger.error(f"Error en el orquestador: {e}")
            
    logger.info("Orquestador detenido")