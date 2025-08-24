import logging 
from logging.handlers import RotatingFileHandler
import sys 

# In order to use the logging system in any module, it is necessary to write
# logging.getLogger(“snow”).getChild(“Yerik”)


def setup_logging(app_name: str = "snow"):

    logger = logging.getLogger(app_name) #Logger creation
    if logger.handlers:
        return logger  # Logger already configured
    
    logger.setLevel(logging.DEBUG) # Set the base logging level to DEBUG
    logger.propagate = False # Prevent log messages from being propagated to the root logger

    #Format for the log messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(levelname)s - %(message)s - %(threadName)s')

    #file handler creation
    # This only will send info logs or higher to 'sistema_log_snow.log'
    file_handler = RotatingFileHandler(
        'sistema_log_snow.log',
        maxBytes=1_000_000, # Maximum file size of 1MB
        backupCount=5,      # Keep up to 5 backup files
        encoding='utf-8'    # Ensure the log file is written in UTF-8 encoding
    )

    file_handler.setLevel(logging.INFO) # Set the file handler to log INFO level and above
    file_handler.setFormatter(formatter) # Set the formatter for the file handler

    logger.addHandler(file_handler) # Add the file handler to the root logger

    #Stream handler creation
    # This will send Wargning or higher logs to the console
    stream_handler = logging.StreamHandler(sys.stdout) 
    stream_handler.setLevel(logging.WARNING) # Set the stream handler to log WARNING level and above
    stream_handler.setFormatter(formatter) # Set the formatter for the stream handler

    logger.addHandler(stream_handler) # Add the stream handler to the root logger

    logging.info("Logging setup complete. INFO and higher logs will be written to 'sistema_log_snow.log' but only WARNING and higher logs will be displayed in the console.")
    return logger 

# --- Ejemplo de uso del módulo ---
if __name__ == "__main__":
    setup_logging()
    
    # Una vez que el logger está configurado, podemos usar logging.info(), .warning(), etc.
    logging.info("Este es un mensaje informativo que verás en el archivo, pero no en la consola.")
    logging.warning("Este es un mensaje de advertencia. Lo verás en ambos lugares: archivo y consola.")
    logging.error("Este es un mensaje de error. Lo verás en ambos lugares.")
    logging.critical("Este es un mensaje crítico. Lo verás en ambos lugares.")