import threading
import time
from gpiozero import LED

class Bartender:
    def __init__(self):
        self.is_pouring = False
        try:
            # This drives your MOSFET gate on GPIO 17
            self.valve = LED(17)
        except Exception as e:
            print(f"GPIO initialization failed (running in simulation mode?): {e}")
            self.valve = None

    def pour_drink(self, drink_name):
        if self.is_pouring:
            return False, "Bartender is busy pouring another drink."
        
        # Start pouring in a separate thread to not block the web server
        thread = threading.Thread(target=self._pour_sequence, args=(drink_name,))
        thread.start()
        return True, f"Pouring {drink_name}..."

    def _pour_sequence(self, drink_name):
        self.is_pouring = True
        print(f"Starting to pour {drink_name}")
        
        try:
            if self.valve:
                # Logic from test.py
                print("Solenoid test starting")
                
                # Make sure it starts off
                self.valve.off()
                # Reduced initial sleep for better UX, originally 5s in test.py
                time.sleep(1) 
                
                # Turn it on (originally for 30 seconds in test.py)
                print("Valve ON")
                self.valve.on()
                
                # Emulating the 30s pour from test.py
                # In a real scenario, this duration would depend on the recipe
                time.sleep(30) 
                
                # Turn it off
                print("Valve OFF")
                self.valve.off()
                time.sleep(1)
                
                print("Test complete")
            else:
                # Simulation mode
                print("Simulating Valve ON")
                time.sleep(30)
                print("Simulating Valve OFF")
                
        except Exception as e:
            print(f"Error pouring drink: {e}")
        finally:
            if self.valve:
                self.valve.off()
            self.is_pouring = False
            print(f"Finished pouring {drink_name}")

# Global instance
bartender = Bartender()

