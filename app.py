"""
Smart Bartender Flask Application
Web server and REST API for controlling the bartender system
"""

import json
import threading
import logging
from flask import Flask, render_template, jsonify, request
from hardware import BartenderHardware
import config

# Initialize Flask app
app = Flask(__name__)

# Initialize hardware
hw = BartenderHardware(simulation_mode=False)

# Global status tracking
status = {
    "pouring": False,
    "current_drink": None,
    "reservoir_levels": {
        "1": config.RESERVOIR_CAPACITY_ML,
        "2": config.RESERVOIR_CAPACITY_ML,
        "3": config.RESERVOIR_CAPACITY_ML,
        "4": config.RESERVOIR_CAPACITY_ML
    },
    "refilling": {
        "1": False,
        "2": False,
        "3": False,
        "4": False
    }
}

# Test mode tracking
test_state = {
    "valve_active": False,
    "pump_active": False,
    "valve_timer": None,
    "pump_timer": None
}

# Load recipes
try:
    with open('recipes.json', 'r') as f:
        recipes = json.load(f)
    print(f"Loaded {len(recipes)} recipes")
except Exception as e:
    print(f"Error loading recipes: {e}")
    recipes = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html', recipes=recipes)


@app.route('/api/status')
def get_status():
    """Get current system status"""
    # Update reservoir levels from hardware
    status["reservoir_levels"] = {
        str(i): hw.reservoir_levels[i] for i in range(1, 5)
    }

    # Update refilling status from hardware
    status["refilling"] = {
        str(i): hw.refilling[i] for i in range(1, 5)
    }

    return jsonify(status)


@app.route('/api/recipes')
def get_recipes():
    """Get all drink recipes"""
    return jsonify(recipes)


@app.route('/api/pour/<drink_name>', methods=['POST'])
def pour_drink(drink_name):
    """
    Pour a specific drink.

    Args:
        drink_name: Name of the drink from recipes.json
    """
    # Check if already pouring
    if status["pouring"]:
        return jsonify({"error": "Already pouring a drink"}), 400

    # Validate drink exists
    if drink_name not in recipes:
        return jsonify({"error": f"Unknown drink: {drink_name}"}), 404

    # Get recipe
    recipe = recipes[drink_name]

    # Start pouring in background thread
    def pour_thread():
        try:
            status["pouring"] = True
            status["current_drink"] = drink_name
            logger.info(f"Starting to pour: {drink_name}")

            # Pour each ingredient
            for reservoir_str, ml in recipe.items():
                reservoir_num = int(reservoir_str)
                if ml > 0:
                    logger.info(f"Pouring {ml}ml from reservoir {reservoir_num}")
                    hw.pour(reservoir_num, ml)
                    # Small delay between ingredients
                    threading.Event().wait(0.5)

            logger.info(f"Finished pouring: {drink_name}")

        except Exception as e:
            logger.error(f"Error pouring {drink_name}: {e}")

        finally:
            status["pouring"] = False
            status["current_drink"] = None

    # Spawn thread
    thread = threading.Thread(target=pour_thread, daemon=True)
    thread.start()

    return jsonify({"message": f"Pouring {drink_name}"}), 200


@app.route('/api/refill/<int:reservoir_num>', methods=['POST'])
def manual_refill(reservoir_num):
    """
    Manually trigger reservoir refill.

    Args:
        reservoir_num: Reservoir number (1-4)
    """
    if reservoir_num < 1 or reservoir_num > 4:
        return jsonify({"error": "Invalid reservoir number"}), 400

    # Start refill in background thread
    def refill_thread():
        try:
            logger.info(f"Manual refill requested for reservoir {reservoir_num}")
            hw.refill_reservoir(reservoir_num)
        except Exception as e:
            logger.error(f"Error refilling reservoir {reservoir_num}: {e}")

    thread = threading.Thread(target=refill_thread, daemon=True)
    thread.start()

    return jsonify({"message": f"Refilling reservoir {reservoir_num}"}), 200


# Optional: Manual control endpoints for testing

@app.route('/api/manual/valve/<int:valve_num>/<action>', methods=['POST'])
def manual_valve(valve_num, action):
    """
    Manually control a valve (for testing).

    Args:
        valve_num: Valve number (1-4)
        action: "open" or "close"
    """
    if valve_num < 1 or valve_num > 4:
        return jsonify({"error": "Invalid valve number"}), 400

    if action not in ["open", "close"]:
        return jsonify({"error": "Invalid action"}), 400

    try:
        if action == "open":
            hw.open_valve(valve_num)
        else:
            hw.close_valve(valve_num)

        return jsonify({"message": f"Valve {valve_num} {action}ed"}), 200

    except Exception as e:
        logger.error(f"Error controlling valve {valve_num}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/manual/pump/<int:pump_num>/<action>', methods=['POST'])
def manual_pump(pump_num, action):
    """
    Manually control a pump (for testing).

    Args:
        pump_num: Pump number (1-4)
        action: "on" or "off"
    """
    if pump_num < 1 or pump_num > 4:
        return jsonify({"error": "Invalid pump number"}), 400

    if action not in ["on", "off"]:
        return jsonify({"error": "Invalid action"}), 400

    try:
        if action == "on":
            hw.activate_pump(pump_num)
        else:
            hw.deactivate_pump(pump_num)

        return jsonify({"message": f"Pump {pump_num} turned {action}"}), 200

    except Exception as e:
        logger.error(f"Error controlling pump {pump_num}: {e}")
        return jsonify({"error": str(e)}), 500


# Test Mode Routes

@app.route('/test')
def test_page():
    """Serve the test page"""
    return render_template('test.html')


@app.route('/api/test/status')
def test_status():
    """Get test mode status"""
    return jsonify(test_state)


@app.route('/api/test/valve/start', methods=['POST'])
def test_valve_start():
    """Start valve (GPIO 24) for 60 seconds"""
    import time

    def valve_auto_stop():
        time.sleep(60)
        if test_state["valve_active"]:
            hw.close_valve(1)
            test_state["valve_active"] = False
            test_state["valve_timer"] = None
            logger.info("Test valve auto-stopped after 60s")

    # Stop existing timer if any
    if test_state["valve_timer"]:
        test_state["valve_timer"] = None

    # Open valve
    hw.open_valve(1)
    test_state["valve_active"] = True

    # Start timer thread
    timer = threading.Thread(target=valve_auto_stop, daemon=True)
    timer.start()
    test_state["valve_timer"] = timer

    logger.info("Test valve started")
    return jsonify({"message": "Valve started"}), 200


@app.route('/api/test/valve/stop', methods=['POST'])
def test_valve_stop():
    """Stop valve immediately"""
    hw.close_valve(1)
    test_state["valve_active"] = False
    test_state["valve_timer"] = None

    logger.info("Test valve stopped")
    return jsonify({"message": "Valve stopped"}), 200


@app.route('/api/test/pump/start', methods=['POST'])
def test_pump_start():
    """Start pump (GPIO 17) for 60 seconds"""
    import time

    def pump_auto_stop():
        time.sleep(60)
        if test_state["pump_active"]:
            hw.deactivate_pump(1)
            test_state["pump_active"] = False
            test_state["pump_timer"] = None
            logger.info("Test pump auto-stopped after 60s")

    # Stop existing timer if any
    if test_state["pump_timer"]:
        test_state["pump_timer"] = None

    # Activate pump
    hw.activate_pump(1)
    test_state["pump_active"] = True

    # Start timer thread
    timer = threading.Thread(target=pump_auto_stop, daemon=True)
    timer.start()
    test_state["pump_timer"] = timer

    logger.info("Test pump started")
    return jsonify({"message": "Pump started"}), 200


@app.route('/api/test/pump/stop', methods=['POST'])
def test_pump_stop():
    """Stop pump immediately"""
    hw.deactivate_pump(1)
    test_state["pump_active"] = False
    test_state["pump_timer"] = None

    logger.info("Test pump stopped")
    return jsonify({"message": "Pump stopped"}), 200


def main():
    """Main entry point"""
    print("=" * 60)
    print("Smart Bartender Server Starting")
    print("=" * 60)
    print(f"\nServer Configuration:")
    print(f"  Host: {config.HOST}")
    print(f"  Port: {config.PORT}")
    print(f"  Debug: {config.DEBUG}")
    print(f"\nRecipes loaded: {len(recipes)}")
    for drink in recipes.keys():
        print(f"  - {drink}")
    print(f"\nAccess the bartender at:")
    print(f"  http://localhost:{config.PORT}")
    print(f"  http://<raspberry-pi-ip>:{config.PORT}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)

    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=False  # Prevent double initialization
        )
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        hw.cleanup()
        print("Goodbye!")


if __name__ == '__main__':
    main()
