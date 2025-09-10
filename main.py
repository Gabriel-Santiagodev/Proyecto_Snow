"""General imports"""

import logging
import ModulosGenerales.modulo_logging as modulo_logging 
import threading
import queue

""" Modules import"""
#---------------------------------------------------------

from TareasFlujoPrincipal import cameras_module
#from TareasFlujoPrincipal import yolo_module
#from TareasFlujoPrincipal import audio_module

#---------------------------------------------------------

""" Variables globales """
#---------------------------------------------------------

cola_frames = queue.Queue()

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
    """ Remove this line for enabling cameras module
    oled_thread = threading.Thread(
        target=oled_module.run,
        name="OLED",
        args=(stop_event,),
        daemon=False
    )
    oled_thread.start()
    Remove this line for enabling cameras module"""
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

    # Yolo thread------------------------------------------
    """ Remove this line for enabling cameras module
    yolo_thread = threading.Thread(
        target=yolo_module.run,
        name="YOLO",
        args=(stop_event,),
        daemon=False
    )
    yolo_thread.start()
    Remove this line for enabling cameras module"""
    # -----------------------------------------------------

    # Audio thread-----------------------------------------
    """ Remove this line for enabling cameras module
    audio_thread = threading.Thread(
        target=audio_module.run,
        name="AUDIO",
        args=(stop_event,),
        daemon=False
    )
    audio_thread.start()
    Remove this line for enabling cameras module"""
    # -----------------------------------------------------

    # Tracking thread(Optional)----------------------------
    """ Remove this line for enabling cameras module
    tracking_thread = threading.Thread(
        target=tracking_module.run,
        name="TRACKING",
        args=(stop_event,),
        daemon=False
    )
    tracking_thread.start()
    Remove this line for enabling cameras module"""
    # -----------------------------------------------------

    # Hilo del orquestador--------------------------------
    """ Remove this line for enabling cameras module
    hilo_orquestador = threading.Thread(
        target=orquestador.run,
        name="orquestador",
        args=(stop_event,),
        daemon=False
    )
    hilo_orquestador.start()
    Remove this line for enabling cameras module"""
    #------------------------------------------------------

    #------------------------------------------------------

    # Keep the main thread alive until interrupted---------
    
    try:
        #oled_thread.join() # Uncomment this line when oled module is enabled
        cameras_thread.join() # Uncomment this line when cameras module is enabled
        #yolo_thread.join() # Uncomment this line when yolo module is enabled
        #audio_thread.join() # Uncomment this line when audio module is enabled
        #tracking_thread.join() # Uncomment this line when tracking module is enabled
        #hilo_orquestador.join() # Uncomment this line when orquestador module is enabled
        pass # remove this line when all modules are enabled
    except KeyboardInterrupt:
        main_logger.info("Shutting down the application")
        stop_event.set() 
        #oled_thread.join() # Uncomment this line when oled module is enabled
        cameras_thread.join() 
        #yolo_thread.join() # Uncomment this line when yolo module is enabled
        #audio_thread.join() # Uncomment this line when audio module is enabled
        #tracking_thread.join() # Uncomment this line when tracking module is enabled
        #hilo_orquestador.join() # Uncomment this line when orquestador module is enabled
        
    
    main_logger.info("Application has been shut down")

    if __name__ == "__main__":
        main()
    #------------------------------------------------------