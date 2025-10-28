"""
Smart Bartender Configuration
Contains all hardware mappings, calibration values, and system settings
"""

# GPIO Pin Mappings (BCM numbering)
PUMP_PINS = {
    1: 17,  # Pump 1 (Vodka)
    2: 27,  # Pump 2 (Rum)
    3: 22,  # Pump 3 (Orange Juice)
    4: 23   # Pump 4 (Cranberry Juice)
}

VALVE_PINS = {
    1: 24,  # Valve 1 (Vodka reservoir)
    2: 25,  # Valve 2 (Rum reservoir)
    3: 5,   # Valve 3 (Orange Juice reservoir)
    4: 6    # Valve 4 (Cranberry Juice reservoir)
}

FLOAT_PINS = {
    1: 16,  # Float Switch 1 (Vodka reservoir)
    2: 20,  # Float Switch 2 (Rum reservoir)
    3: 21,  # Float Switch 3 (Orange Juice reservoir)
    4: 26   # Float Switch 4 (Cranberry Juice reservoir)
}

# Ingredient Mapping
INGREDIENTS = {
    1: "Vodka",
    2: "Rum",
    3: "Orange Juice",
    4: "Cranberry Juice"
}

# Calibration Values (ml/second for gravity flow through valves)
# These should be adjusted after physical testing
ML_PER_SECOND = {
    1: 8.0,  # Valve 1: ~8ml/sec gravity flow
    2: 8.0,  # Valve 2: ~8ml/sec gravity flow
    3: 8.0,  # Valve 3: ~8ml/sec gravity flow
    4: 8.0   # Valve 4: ~8ml/sec gravity flow
}

# Reservoir Settings
RESERVOIR_CAPACITY_ML = 400      # Maximum capacity of each wall reservoir
REFILL_THRESHOLD_ML = 100        # Start refilling when level drops to this
PUMP_FLOW_RATE = 220             # ml/min (Kamoer KHPP260 specification)

# Safety Limits
MAX_POUR_TIME = 30               # Maximum seconds for a single pour operation
MAX_PUMP_TIME = 180              # Maximum seconds for pump operation
REFILL_TIMEOUT = 120             # Maximum seconds for refill operation

# Server Settings
HOST = '0.0.0.0'                 # Listen on all network interfaces
PORT = 5000                      # Flask server port
DEBUG = False                    # Set to True only during development

# GPIO Settings (for Raspberry Pi 5)
GPIO_CHIP = 'gpiochip4'          # GPIO chip device for Pi 5

# Logging Settings
LOG_FILE = 'logs/bartender.log'
LOG_LEVEL = 'INFO'
