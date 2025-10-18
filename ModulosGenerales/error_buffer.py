from collections import deque 
import threading
from config import ERROR_BUFFER_MAXLEN 

_error_buffer = deque()
_dropped_errors_count = 0
_error_buffer_lock = threading.Lock()

def add_error(error_msg: str):
    
    """
    Adds an error message to the buffer. If the buffer is full, the oldest message is dropped.

    """

    global _dropped_errors_count 
    with _error_buffer_lock:
        if len(_error_buffer) >= ERROR_BUFFER_MAXLEN:
            _error_buffer.popleft()  # Remove the oldest error message
            _dropped_errors_count += 1 # Increment the dropped errors count
        _error_buffer.append(error_msg) # Add the new error message

def get_recent_errors() -> list[str]:

    """
    Returns a list of all error messages in the buffer from oldest to newest.

    """
    
    with _error_buffer_lock:
        return list(_error_buffer)
    
def get_dropped_errors_count() -> int:

    """
    Returns the total number of dropped error messages due to buffer overflow.

    """

    with _error_buffer_lock:
        return _dropped_errors_count