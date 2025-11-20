from gpiozero import LED
from time import sleep
import threading

# Global valve variable, initialized to None
valve = None

# Lock to prevent multiple pours at the same time
pour_lock = threading.Lock()

def init_hardware():
    """
    Initializes the hardware connection.
    Returns (True, None) if successful, or (False, error_message) if failed.
    """
    global valve
    try:
        # Setup valve on GPIO17 as per test.py
        # using LED class as it was used in test.py for simple on/off control
        valve = LED(17)
        valve.off()
        print("Hardware initialized successfully")
        return True, None
    except Exception as e:
        error_msg = str(e)
        print(f"Failed to initialize hardware: {error_msg}")
        return False, error_msg

def pour_demo_sequence():
    """
    Runs the sequence defined in test.py:
    1. Ensure off
    2. Wait 1s
    3. Turn on for 30s (simulating pour)
    4. Turn off
    5. Wait 1s
    
    Note: Lock is acquired by the caller (start_pour) and released here.
    """
    global valve
    try:
        if valve is None:
            # Try to re-initialize if it wasn't ready
            success, _ = init_hardware()
            if not success:
                print("Cannot pour: Hardware not initialized")
                return

        print("Solenoid test starting")
        valve.off()
        sleep(1)
        
        print("Valve ON")
        valve.on()
        # The user's test.py had 30 seconds.
        sleep(30)
        
        print("Valve OFF")
        valve.off()
        sleep(1)
        print("Test complete")
    except Exception as e:
        print(f"Error during pour: {e}")
        # Ensure valve is off if error and valve exists
        if valve:
            try:
                valve.off()
            except:
                pass
    finally:
        # Always release the lock when done
        pour_lock.release()

def start_pour():
    """
    Starts the pour sequence in a background thread if not already running.
    Returns:
        (True, message) if started
        (False, message) if busy or error
    """
    # Check if hardware is ready
    if valve is None:
        success, error = init_hardware()
        if not success:
            return False, f"Hardware Error: {error}"

    # Try to acquire lock non-blocking
    if not pour_lock.acquire(blocking=False):
        return False, "System is busy pouring."
    
    try:
        t = threading.Thread(target=pour_demo_sequence)
        t.start()
        return True, "Pouring..."
    except Exception as e:
        print(f"Failed to start pour thread: {e}")
        pour_lock.release()
        return False, f"Internal Error: {e}"
