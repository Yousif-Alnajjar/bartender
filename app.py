from flask import Flask, render_template, jsonify, request
import hardware
import sys

app = Flask(__name__)

DRINKS = [
    "Vodka Cranberry",
    "Screwdriver",
    "Rum Punch",
    "Madras",
    "Bay Breeze"
]

# Global status for UI to query hardware state on load
HARDWARE_STATUS = {"ready": False, "error": None}

@app.route('/')
def index():
    return render_template('index.html', drinks=DRINKS, hw_status=HARDWARE_STATUS)

@app.route('/pour', methods=['POST'])
def pour():
    data = request.get_json()
    drink_name = data.get('drink')
    
    if not drink_name:
        return jsonify({"status": "error", "message": "No drink specified"}), 400
        
    # For now, all drinks trigger the demo sequence
    print(f"Received request for {drink_name}")
    
    success, message = hardware.start_pour()
    if success:
        return jsonify({"status": "success", "message": f"{message} ({drink_name})", "duration": 30})
    elif "busy" in message.lower():
        return jsonify({"status": "busy", "message": message}), 429
    else:
        return jsonify({"status": "error", "message": message}), 500

if __name__ == '__main__':
    # Initialize hardware on startup
    print("Initializing hardware...")
    success, error = hardware.init_hardware()
    HARDWARE_STATUS["ready"] = success
    HARDWARE_STATUS["error"] = error
    
    if not success:
        print(f"WARNING: Hardware initialization failed: {error}")
        print("App will run, but pouring will fail until GPIO is free.")
    
    # Host on 0.0.0.0 to be accessible on the network
    # use_reloader=False prevents the Flask debug reloader from starting a second process
    # which would cause a 'GPIO busy' error by trying to initialize the hardware twice.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
