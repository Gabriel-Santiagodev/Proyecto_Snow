import logging 
from logging.handlers import RotatingFileHandler
import sys 
from config import DEBUG, CONSOLE_LOG, FILE_LOG
from ModulosGenerales.error_buffer import add_error



# In order to use the logging system in any module, it is necessary to write
# logging.getLogger(“snow”).getChild(“Yerik”)

class ErrorBufferHandler(logging.Handler):

        """
        Custom handler that only stores error and critical logs in a buffer. When an error or critical log is added, it also adds it to the error buffer.

        """

        def __init__(self, level=logging.ERROR):
            super().__init__(level)

        def emit(self, record: logging.LogRecord) -> None:
            """
            This method is called when a log record is emitted.
            """

            try:
                msg = self.format(record)
                add_error(msg) # Add the error message to the error buffer
            except Exception:
                self.handleError(record) # Handle any exceptions that occur during logging

def setup_logging(app_name: str = "snow"):

    logger = logging.getLogger(app_name) #Logger creation
    if logger.handlers:
        return logger  # Logger already configured
    
    logger.setLevel(logging.DEBUG) # Set the base logging level to DEBUG
    logger.propagate = False # Prevent log messages from being propagated to the root logger

    #Format for the log messages
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    err_buffer_handler = ErrorBufferHandler(level=logging.ERROR) # Custom handler to store error and critical logs in a buffer
    err_buffer_handler.setFormatter(logging.Formatter( fmt="%(levelname)s | %(message)s")) # Set the formatter for the error buffer handler
    logger.addHandler(err_buffer_handler) # Add the error buffer handler to the root logger

    #file handler creation
    # This only will send info logs or higher to 'sistema_log_snow.log'
    file_handler = RotatingFileHandler(
        'sistema_log_snow.log',
        maxBytes=1_000_000, # Maximum file size of 1MB
        backupCount=5,      # Keep up to 5 backup files
        encoding='utf-8'    # Ensure the log file is written in UTF-8 encoding
    )

    file_handler.setLevel(logging.DEBUG if DEBUG else FILE_LOG) # Set the file handler to log INFO level and above
    file_handler.setFormatter(formatter) # Set the formatter for the file handler

    logger.addHandler(file_handler) # Add the file handler to the root logger

    #Stream handler creation
    # This will send Wargning or higher logs to the console
    stream_handler = logging.StreamHandler(sys.stdout) 
    stream_handler.setLevel(logging.DEBUG if DEBUG else CONSOLE_LOG) # Set the stream handler to log WARNING level and above
    stream_handler.setFormatter(formatter) # Set the formatter for the stream handler

    logger.addHandler(stream_handler) # Add the stream handler to the root logger

    logging.info("Logging setup complete. INFO and higher logs will be written to 'sistema_log_snow.log' but only WARNING and higher logs will be displayed in the console.")



    return logger 

# Example usage
if __name__ == "__main__":
    mi_logger = setup_logging()
    
    # log messages for testing
    mi_logger.info("Este es un mensaje informativo que verás en el archivo, pero no en la consola.")
    mi_logger.warning("Este es un mensaje de advertencia. Lo verás en ambos lugares: archivo y consola.")
    mi_logger.error("Este es un mensaje de error. Lo verás en ambos lugares.")
    mi_logger.critical("Este es un mensaje crítico. Lo verás en ambos lugares.")


