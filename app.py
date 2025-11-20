from flask import Flask, render_template, jsonify, request
import hardware

app = Flask(__name__)

DRINKS = [
    "Vodka Cranberry",
    "Screwdriver",
    "Rum Punch",
    "Madras",
    "Bay Breeze"
]

@app.route('/')
def index():
    return render_template('index.html', drinks=DRINKS)

@app.route('/pour', methods=['POST'])
def pour():
    data = request.get_json()
    drink_name = data.get('drink')
    
    if not drink_name:
        return jsonify({"status": "error", "message": "No drink specified"}), 400
        
    # For now, all drinks trigger the demo sequence
    print(f"Received request for {drink_name}")
    
    success = hardware.start_pour()
    if success:
        return jsonify({"status": "success", "message": f"Pouring {drink_name}...", "duration": 30})
    else:
        return jsonify({"status": "busy", "message": "System is busy pouring."}), 429

if __name__ == '__main__':
    # Host on 0.0.0.0 to be accessible on the network
    app.run(host='0.0.0.0', port=5000, debug=True)

