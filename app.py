from flask import Flask, render_template, jsonify, request
from hardware import bartender

app = Flask(__name__)

DRINKS = [
    {"id": "vodka_cranberry", "name": "Vodka Cranberry", "image": "vodka_cran.png", "color": "#C1272D"},
    {"id": "screwdriver", "name": "Screwdriver", "image": "screwdriver.png", "color": "#F7931E"},
    {"id": "rum_punch", "name": "Rum Punch", "image": "rum_punch.png", "color": "#D9381E"},
    {"id": "madras", "name": "Madras", "image": "madras.png", "color": "#E05C5C"},
    {"id": "bay_breeze", "name": "Bay Breeze", "image": "bay_breeze.png", "color": "#00A99D"},
]

@app.route('/')
def index():
    return render_template('index.html', drinks=DRINKS)

@app.route('/pour', methods=['POST'])
def pour():
    data = request.json
    drink_id = data.get('drink_id')
    drink = next((d for d in DRINKS if d['id'] == drink_id), None)
    
    if not drink:
        return jsonify({"status": "error", "message": "Invalid drink selection"}), 400
        
    success, message = bartender.pour_drink(drink['name'])
    
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "busy", "message": message}), 409

@app.route('/status')
def status():
    return jsonify({"is_pouring": bartender.is_pouring})

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)

