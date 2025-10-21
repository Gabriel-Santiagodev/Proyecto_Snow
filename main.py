"""General imports"""

import logging
import ModulosGenerales.modulo_logging as modulo_logging 
import threading
import queue

""" Modules import"""
#---------------------------------------------------------

from TareasFlujoPrincipal import cameras_module
from TareasFlujoPrincipal import audio_module
from TareasFlujoPrincipal import orquestador
from TareasSegundoPlano import oled_module

#---------------------------------------------------------

""" Variables globales """
#---------------------------------------------------------

cola_frames = queue.Queue()
cola_audio = queue.Queue()

#---------------------------------------------------------

def main():
    """
    Main function to initialize and run the application.
    Launches all modules in separate threads and creates the event of stop event.
    
    """
    # Initialize logging----------------------------------
    modulo_logging.setup_logging()
    main_logger = logging.getLogger("snow").getChild("module_name")
    main_logger.info("Starting the application")
    #-----------------------------------------------------
    
    # Create a stop event for threads---------------------
    stop_event = threading.Event()
    #-----------------------------------------------------
    
    # Made and start threads for each module--------------

    #Oled thread------------------------------------------
    
    oled_thread = threading.Thread(
        target=oled_module.run,
        name="OLED",
        args=(stop_event,),
        daemon=False
    )
    oled_thread.start()
   
    #-----------------------------------------------------

    # Cameras thread---------------------------------------

    cameras_thread = threading.Thread(
        target=cameras_module.run,
        name="CAMERAS",
        args=(stop_event,cola_frames,),
        daemon=False
    )
    cameras_thread.start()
    
    # -----------------------------------------------------

    # Audio thread-----------------------------------------
   
    audio_thread = threading.Thread(
        target=audio_module.run,
        name="AUDIO",
        args=(stop_event,cola_audio,),
        daemon=False
    )
    audio_thread.start()
   
    # -----------------------------------------------------

    # Hilo del orquestador--------------------------------
    
    hilo_orquestador = threading.Thread(
        target=orquestador.run,
        name="orquestador",
        args=(stop_event,cola_frames,cola_audio,),
        daemon=False
    )
    hilo_orquestador.start()

    # Keep the main thread alive until interrupted---------
    
    try:
        oled_thread.join()
        cameras_thread.join() 
        audio_thread.join() 
        hilo_orquestador.join()
       
    except KeyboardInterrupt:
        main_logger.info("Shutting down the application")
        stop_event.set() 
        oled_thread.join() 
        cameras_thread.join() 
        audio_thread.join() 
        hilo_orquestador.join() 
        
    
    main_logger.info("Application has been shut down")


    #------------------------------------------------------
if __name__ == "__main__":
    main()