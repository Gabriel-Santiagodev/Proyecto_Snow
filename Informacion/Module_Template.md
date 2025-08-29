# 📝 Module Template — Project SNOW

This template defines the **standard structure** for any module in Project SNOW.  
It ensures consistent logging, proper thread management, and clean integration into the main program.

---

## 📌 How to use

1. **Copy this file** into `/Proyecto_Snow/MainFlowTasks/` or `/Proyecto_Snow/BackgroundTasks/` (Background is for background tasks) in your respective file  
   _(e.g., `cameras_module.py`, `yolo_module.py`, `audio_module.py`,  etc.)_.

2. **Change `module_name`** to match the actual module_name in:
   - The logger definition
   - The log messages for "started" and "stopped"

3. **Place your main logic** inside the `while not stop_event.is_set():` loop.  
   - This loop runs in its own thread, separate from the rest of the system.  
   - It will keep running until the `stop_event` is triggered by the main program (e.g., in emergency stop or maintenance mode).

4. **Use the provided `logger`** instead of `print()`.  
   - `INFO` and above will be saved in the log file.  
   - `WARNING` and above will also appear in the console.  
   - `ERROR` and `CRITICAL` will be shown on the OLED.

---

## 📄 Template Code

```python
import logging

# 🔧 Logger setup
# Change "module_name" to the actual name of your module (e.g., "cameras_module", "yolo_module", "audio_module", etc.)
logger = logging.getLogger("snow").getChild("module_name")

def run(stop_event):
    """
    General information about this function:
    Entry point and main loop for this module.

    Place ALL the specific code and logic for your module inside this function.
    This loop runs in its own thread and will remain active until `stop_event`
    is triggered by the main program (e.g., when the system enters maintenance mode
    or the emergency stop button is pressed).

    Examples:
      - In a camera module: code to capture and process video frames.
      - In an audio module: code to queue and play audio instructions.
    """

    # 1️⃣ Log that the module has started (useful for debugging and tracking activity)
    logger.info("Module 'module_name' started")  # Change 'module_name' to your actual module name

    # 2️⃣ Main loop for your module
    while not stop_event.is_set():
        # 💡 Place your module’s main code here
        # This is where all processing, decision-making, or device control will happen
        pass  # Remove this line when adding your actual code

    # 3️⃣ Log that the module has stopped
    logger.info("Module 'module_name' stopped")  # Change 'module_name' to your actual module name
