import logging 
import sys # Ruben Note = What is sys used for?

def setup_logging():

    root_logger = logging.getLogger() #Root logger creation
    root_logger.setLevel(logging.DEBUG) # Set the base logging level to DEBUG

    #Format for the log messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    #File handler creation
    # This only will send info logs or higher to 'sistema_log_snow.log'
    file_handler = logging.FileHandler('sistema_log_snow.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO) # Set the file handler to log INFO level and above
    file_handler.setFormatter(formatter) # Set the formatter for the file handler

    root_logger.addHandler(file_handler) # Add the file handler to the root logger

    #Stream handler creation
    # This will send Wargning or higher logs to the console
    stream_handler = logging.StreamHandler(sys.stdout) 
    stream_handler.setLevel(logging.WARNING) # Set the stream handler to log WARNING level and above
    stream_handler.setFormatter(formatter) # Set the formatter for the stream handler

    root_logger.addHandler(stream_handler) # Add the stream handler to the root logger

    logging.info("Logging setup complete. INFO and higher logs will be written to 'sistema_log_snow.log' but only WARNING and higher logs will be displayed in the console.")

# --- Ejemplo de uso del módulo ---
if __name__ == "__main__":
    setup_logging()
    
    # Una vez que el logger está configurado, podemos usar logging.info(), .warning(), etc.
    logging.info("Este es un mensaje informativo que verás en el archivo, pero no en la consola.")
    logging.warning("Este es un mensaje de advertencia. Lo verás en ambos lugares: archivo y consola.")
    logging.error("Este es un mensaje de error. Lo verás en ambos lugares.")
    logging.critical("Este es un mensaje crítico. Lo verás en ambos lugares.")