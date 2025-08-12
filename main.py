import logging_module
import logging

logging_module.setup_logging() 

def main():
    logging.info("Starting the main function.")

    #Here would be the main logic of the entire application such as cameras, ML model, audio system, etc.

    try:
    # Simulate camera initialization
        logging.info("Cámaras inicializadas correctamente.")
        
        # Simulate one camera is turned off
        logging.warning("Camara 1 apagada.")
        
        # force some error in the main logic
        raise ValueError("Simulando un error: Fallo al leer datos del sensor de temperatura.")
    
    except ValueError as e:
        # Log the error
        logging.error("Se produjo un error durante la ejecución: %s", e)
    
    logging.info("El programa principal ha finalizado.") 

if __name__ == "__main__":
    main()
