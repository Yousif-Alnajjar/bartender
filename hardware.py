import threading
import time
from gpiozero import LED

class Bartender:
    def __init__(self):
        self.is_pouring = False
        # STRICTLY HARDWARE MODE - NO SIMULATION
        # This drives your MOSFET gate on GPIO 17
        print("Initializing Hardware on GPIO 17...")
        self.valve = LED(17)
        # Ensure it's off initially
        self.valve.off()
        print("Hardware Initialized.")

    def pour_drink(self, drink_name):
        if self.is_pouring:
            return False, "Bartender is busy pouring another drink."
        
        # Start pouring in a separate thread to not block the web server
        thread = threading.Thread(target=self._pour_sequence, args=(drink_name,))
        thread.start()
        return True, f"Pouring {drink_name}..."

    def _pour_sequence(self, drink_name):
        self.is_pouring = True
        print(f"DEMO MODE: Starting to pour {drink_name} using GPIO 17")
        
        try:
            # Logic from test.py
            print("Solenoid sequence starting")
            
            # Make sure it starts off
            self.valve.off()
            time.sleep(1) 
            
            # Turn it on (originally for 30 seconds in test.py)
            print("Valve ON")
            self.valve.on()
            
            # Pour duration
            time.sleep(30) 
            
            # Turn it off
            print("Valve OFF")
            self.valve.off()
            time.sleep(1)
            
            print("Sequence complete")
                
        except Exception as e:
            print(f"Error pouring drink: {e}")
            # Ensure valve is off if error occurs
            try:
                self.valve.off()
            except:
                pass
        finally:
            self.is_pouring = False
            print(f"Finished pouring {drink_name}")

# Global instance
bartender = Bartender()
