from gpiozero import LED
import time

# Initialize GPIO 17 immediately, just like test.py
# If this fails with BadPinFactory, it means the environment lacks GPIO access (e.g. running on Mac)
valve = LED(17)

def pour_drink(drink_name):
    print(f"Pouring {drink_name}")
    
    # Exact logic from test.py
    valve.off()
    time.sleep(1)
    
    valve.on()
    time.sleep(30)
    
    valve.off()
    time.sleep(1)
    
    print("Pour complete")
fix