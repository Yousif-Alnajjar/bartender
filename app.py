from flask import Flask, render_template, jsonify, request
import threading
import time
import os
import platform

app = Flask(__name__)

# Check if we are on a Raspberry Pi or similar environment
# If not, we'll use a mock or print-only approach for development
IS_RPI = False
try:
    from gpiozero import LED
    # Try to initialize to check if it works (e.g. on non-Pi this might fail depending on config)
    # For development on macOS, we might want to mock this if not present
    if platform.system() == "Linux": # Simple check, can be improved
        IS_RPI = True
except (ImportError, Exception):
    pass

# Mock LED class for development
class MockLED:
    def __init__(self, pin):
        self.pin = pin
        self.is_lit = False
    
    def on(self):
        self.is_lit = True
        print(f"Mock GPIO {self.pin} ON")
    
    def off(self):
        self.is_lit = False
        print(f"Mock GPIO {self.pin} OFF")

if IS_RPI:
    try:
        valve = LED(17)
    except Exception as e:
        print(f"Error initializing LED: {e}, falling back to mock")
        valve = MockLED(17)
else:
    print("Not running on Raspberry Pi (detected), using Mock LED")
    valve = MockLED(17)

# Lock to prevent multiple dispenses at the same time
dispense_lock = threading.Lock()

def run_dispense_cycle():
    """
    Runs the dispense cycle logic from the original test.py
    """
    with dispense_lock:
        print("Solenoid test starting")
        
        # Make sure it starts off
        valve.off()
        time.sleep(5)
        
        # Turn it on
        print("Valve ON")
        valve.on()
        
        # Original code had sleep(30), comment said 2 seconds. 
        # Keeping code behavior (30s) as requested.
        time.sleep(30)
        
        # Turn it off
        print("Valve OFF")
        valve.off()
        time.sleep(1)
        
        print("Test complete")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dispense', methods=['POST'])
def dispense():
    data = request.json
    drink_name = data.get('drink')
    
    if dispense_lock.locked():
        return jsonify({"status": "busy", "message": "Dispenser is currently busy"}), 409
    
    # Start dispense in background thread to not block the UI
    thread = threading.Thread(target=run_dispense_cycle)
    thread.start()
    
    return jsonify({"status": "success", "message": f"Dispensing {drink_name}", "duration": 30})

if __name__ == '__main__':
    # Run on all interfaces so it can be accessed from other devices
    app.run(host='0.0.0.0', port=5000, debug=True)

