from gpiozero import LED
from time import sleep
import threading

# Setup valve on GPIO17 as per test.py
# using LED class as it was used in test.py for simple on/off control
valve = LED(17)
valve.off()

# Lock to prevent multiple pours at the same time
pour_lock = threading.Lock()

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
    try:
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
        # Ensure valve is off if error
        valve.off()
    finally:
        # Always release the lock when done
        pour_lock.release()

def start_pour():
    """
    Starts the pour sequence in a background thread if not already running.
    Returns True if started, False if busy.
    """
    # Try to acquire lock non-blocking
    if not pour_lock.acquire(blocking=False):
        return False
    
    try:
        t = threading.Thread(target=pour_demo_sequence)
        t.start()
        return True
    except Exception as e:
        print(f"Failed to start pour thread: {e}")
        pour_lock.release()
        return False
