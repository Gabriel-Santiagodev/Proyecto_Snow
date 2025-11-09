import logging

# Configuration settings for logging---------------------------------------------------
DEBUG = False # False for production mode, True for development mode
CONSOLE_LOG = logging.WARNING # Only WARNING and above will be shown in console
FILE_LOG = logging.INFO # INFO and above will be logged to file
#--------------------------------------------------------------------------------------

# Error buffer settings
ERROR_BUFFER_MAXLEN = 5 # Maximum number of error messages to store in the buffer

#--------------------------------------------------------------------------------------

# Valor de umbral para detectar obstrucciones en las camaras
THRESHOLD = 500000

#---------------------------------------------------------------------------------------
