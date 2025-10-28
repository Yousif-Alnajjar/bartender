# Smart Bartender - Complete Implementation Plan

---

## Overview

**System Type:** Web-based interface on Raspberry Pi 5
**4 Ingredients:** Vodka, Rum, Orange Juice, Cranberry Juice
**5 Cocktails:** Vodka Cranberry, Screwdriver, Rum Punch, Madras, Bay Breeze

---

## 1. Hardware Architecture

### Physical Layout
```
FLOOR UNIT:
├── Bottle 1: Vodka (1-1.75L)
│   └── Pump 1 (Kamoer KHPP260, 220ml/min)
│       └── 4mm ID tubing → UP to wall
├── Bottle 2: Rum
│   └── Pump 2 → UP to wall
├── Bottle 3: Orange Juice
│   └── Pump 3 → UP to wall
└── Bottle 4: Cranberry Juice
    └── Pump 4 → UP to wall

WALL UNIT:
├── Reservoir 1: Vodka (400ml)
│   ├── Float Switch 1 (detects low level)
│   ├── Inlet from Pump 1
│   └── Valve 1 (outlet) → DOWN to cup
├── Reservoir 2: Rum (400ml)
│   ├── Float Switch 2
│   └── Valve 2 → DOWN to cup
├── Reservoir 3: Orange Juice (400ml)
│   ├── Float Switch 3
│   └── Valve 3 → DOWN to cup
├── Reservoir 4: Cranberry (400ml)
│   ├── Float Switch 4
│   └── Valve 4 → DOWN to cup
├── Raspberry Pi 5
├── 7" Touchscreen
├── 8-Channel Relay Board
└── 12V Power Distribution Block
```

### Electrical Connections

**GPIO Pin Mapping (BCM numbering):**
```
Outputs (Control Relays):
- GPIO 17 → Relay 1 → Pump 1 (floor)
- GPIO 27 → Relay 2 → Pump 2 (floor)
- GPIO 22 → Relay 3 → Pump 3 (floor)
- GPIO 23 → Relay 4 → Pump 4 (floor)
- GPIO 24 → Relay 5 → Valve 1 (wall)
- GPIO 25 → Relay 6 → Valve 2 (wall)
- GPIO 5  → Relay 7 → Valve 3 (wall)
- GPIO 6  → Relay 8 → Valve 4 (wall)

Inputs (Read Float Switches):
- GPIO 16 → Float Switch 1
- GPIO 20 → Float Switch 2
- GPIO 21 → Float Switch 3
- GPIO 26 → Float Switch 4

Power Connections:
- Pi GPIO 5V → Relay Board VCC
- Pi GPIO GND → Relay Board GND
- Float switches → GPIO pins + GND (use internal pull-ups)
```

**Relay Behavior:**
- Active LOW (GPIO LOW = relay ON, GPIO HIGH = relay OFF)
- Initialize all relays to HIGH (OFF) on startup

**Float Switch Behavior:**
- Float switch OPEN (high liquid) = GPIO reads HIGH
- Float switch CLOSED (low liquid) = GPIO reads LOW
- Use internal pull-up resistors in software

**Power Distribution:**
```
12V 5A Power Supply
    ↓
Power Distribution Block
    ├── Pump 1 (+/-)
    ├── Pump 2 (+/-)
    ├── Pump 3 (+/-)
    ├── Pump 4 (+/-)
    ├── Valve 1 (+/-)
    ├── Valve 2 (+/-)
    ├── Valve 3 (+/-)
    └── Valve 4 (+/-)
```

---

## 2. Software Architecture

### Tech Stack
- **Backend:** Python 3 + Flask web framework
- **Hardware Control:** `lgpio` library (Pi 5 compatible)
- **Frontend:** HTML5 + CSS3 + Vanilla JavaScript
- **Communication:** REST API (JSON)
- **Concurrency:** Python threading for background tasks

### Project Structure
```
/home/pi/smart_bartender/
├── app.py                 # Flask application & API
├── hardware.py            # GPIO control class
├── config.py              # Configuration constants
├── recipes.json           # Drink recipes database
├── static/
│   ├── style.css         # Styling
│   ├── script.js         # Frontend logic
│   └── favicon.ico       # (optional)
├── templates/
│   └── index.html        # Main UI
├── logs/
│   └── bartender.log     # Event logging
└── requirements.txt       # Python dependencies
```

---

## 3. Backend Implementation Details

### 3.1 Configuration (config.py)

**Constants to define:**
```python
# GPIO pins
PUMP_PINS = {1: 17, 2: 27, 3: 22, 4: 23}
VALVE_PINS = {1: 24, 2: 25, 3: 5, 4: 6}
FLOAT_PINS = {1: 16, 2: 20, 3: 21, 4: 26}

# Ingredient mapping
INGREDIENTS = {
    1: "Vodka",
    2: "Rum", 
    3: "Orange Juice",
    4: "Cranberry Juice"
}

# Calibration values (adjust after testing)
ML_PER_SECOND = {
    1: 8.0,  # Valve 1: ~8ml/sec gravity flow
    2: 8.0,
    3: 8.0,
    4: 8.0
}

# Reservoir settings
RESERVOIR_CAPACITY_ML = 400
REFILL_THRESHOLD_ML = 100  # Start refill at 100ml
PUMP_FLOW_RATE = 220       # ml/min (Kamoer spec)

# Safety limits
MAX_POUR_TIME = 30      # Seconds
MAX_PUMP_TIME = 180     # Seconds
REFILL_TIMEOUT = 120    # Seconds

# Server settings
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000
DEBUG = False      # Set True only during development
```

### 3.2 Hardware Control Class (hardware.py)

**Class: BartenderHardware**

**Responsibilities:**
1. Initialize GPIO (lgpio for Pi 5)
2. Control pumps (on/off)
3. Control valves (open/close)
4. Read float switches
5. Track estimated reservoir levels
6. Auto-refill monitoring (background thread)
7. Safety timeouts
8. Cleanup on shutdown

**Key Methods:**

```
__init__()
    - Open GPIO chip (gpiochip4 on Pi 5)
    - Set all GPIO outputs to HIGH (relays off)
    - Set GPIO inputs with pull-ups
    - Initialize reservoir level tracking
    - Start background monitoring thread

activate_pump(pump_num)
    - Set GPIO LOW to turn relay ON
    - Log action

deactivate_pump(pump_num)
    - Set GPIO HIGH to turn relay OFF
    - Log action

open_valve(valve_num)
    - Set GPIO LOW to turn relay ON
    - Log action

close_valve(valve_num)
    - Set GPIO HIGH to turn relay OFF
    - Log action

read_float_switch(sensor_num) → bool
    - Read GPIO pin state
    - Return True if HIGH (level OK)
    - Return False if LOW (level low)

pour(valve_num, ml)
    - Calculate time: ml / ML_PER_SECOND[valve_num]
    - Apply MAX_POUR_TIME safety limit
    - Open valve
    - Sleep for calculated time
    - Close valve
    - Decrement estimated reservoir level
    - Log pour event

refill_reservoir(reservoir_num)
    - Check if already refilling (prevent double-refill)
    - Set refill_active flag
    - Calculate refill time based on level deficit
    - Apply REFILL_TIMEOUT safety limit
    - Activate pump
    - Loop: check float switch every 0.5s
    - Stop when float indicates full OR timeout
    - Deactivate pump
    - Reset reservoir level to CAPACITY
    - Clear refill_active flag
    - Log refill event

_monitor_levels() [background thread]
    - Loop continuously while system running
    - Every 2 seconds:
        - For each reservoir 1-4:
            - Read float switch
            - If LOW and not already refilling:
                - Spawn refill_reservoir() in new thread
    - Sleep 2 seconds

cleanup()
    - Stop monitoring thread
    - Set all GPIO outputs HIGH (relays off)
    - Close GPIO chip
    - Log shutdown
```

**Threading Considerations:**
- Background monitor thread runs continuously
- Each refill spawns its own thread
- Pouring happens in API request thread (blocking is OK)
- Use thread locks if modifying shared state

**Error Handling:**
- Catch GPIO errors (log and retry)
- Timeout protection on all pump/valve operations
- Graceful degradation if hardware fails

### 3.3 Flask API (app.py)

**Global State:**
```python
hw = BartenderHardware()  # Hardware instance

status = {
    "pouring": False,           # Is a drink being made?
    "current_drink": None,      # Name of drink being made
    "reservoir_levels": {...},  # Estimated ml in each reservoir
    "refilling": {1: False, 2: False, 3: False, 4: False}
}

recipes = {...}  # Loaded from recipes.json
```

**API Endpoints:**

**1. GET /** 
- Serve index.html template
- Pass recipes to template

**2. GET /api/status**
- Return current system status as JSON
- Update reservoir levels from hardware
- Update refilling status from hardware
- Response:
  ```json
  {
    "pouring": false,
    "current_drink": null,
    "reservoir_levels": {
      "1": 350,
      "2": 400,
      "3": 250,
      "4": 320
    },
    "refilling": {
      "1": false,
      "2": false,
      "3": true,
      "4": false
    }
  }
  ```

**3. POST /api/pour/<drink_name>**
- Check if already pouring (return 400 if yes)
- Validate drink_name exists in recipes (return 404 if not)
- Get recipe from recipes.json
- Spawn background thread for pouring
- Set status.pouring = True
- For each ingredient in recipe:
    - If ml > 0: call hw.pour(reservoir_num, ml)
    - Small delay between ingredients (0.5s)
- Set status.pouring = False when done
- Return 200 with success message immediately

**4. POST /api/refill/<int:reservoir_num>**
- Validate reservoir_num (1-4)
- Spawn thread to call hw.refill_reservoir(reservoir_num)
- Return 200 immediately

**5. GET /api/recipes**
- Return all recipes as JSON

**Optional: Manual Control Endpoints (for testing)**

**6. POST /api/manual/valve/<int:valve_num>/<action>**
- action = "open" or "close"
- Call hw.open_valve() or hw.close_valve()
- Return success message

**7. POST /api/manual/pump/<int:pump_num>/<action>**
- action = "on" or "off"
- Call hw.activate_pump() or hw.deactivate_pump()
- Return success message

**Server Startup:**
- Load recipes.json
- Initialize hardware
- Print access URLs (localhost, Pi hostname)
- Run Flask on 0.0.0.0:5000
- Catch KeyboardInterrupt for clean shutdown
- Call hw.cleanup() on exit

---

# 4. Frontend Implementation Details (Simplified)

## 4.1 HTML Structure (templates/index.html)

**Minimal Layout:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Bartender</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Smart Bartender</h1>
        
        <!-- Status Messages -->
        <div class="status-container">
            <p id="pour-status" class="hidden">Pouring: <span id="current-drink"></span></p>
            <p id="refill-status" class="hidden">Refilling: <span id="refill-reservoirs"></span></p>
        </div>
        
        <!-- Drink Buttons -->
        <div class="drinks-container">
            <button class="drink-btn" onclick="pourDrink('Vodka Cranberry')">
                Vodka Cranberry
            </button>
            <button class="drink-btn" onclick="pourDrink('Screwdriver')">
                Screwdriver
            </button>
            <button class="drink-btn" onclick="pourDrink('Rum Punch')">
                Rum Punch
            </button>
            <button class="drink-btn" onclick="pourDrink('Madras')">
                Madras
            </button>
            <button class="drink-btn" onclick="pourDrink('Bay Breeze')">
                Bay Breeze
            </button>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
```

**Elements:**
- `#pour-status`: Shows "Pouring: [drink name]" when making a drink
- `#refill-status`: Shows "Refilling: Reservoir 1, 3" when refilling
- `.drink-btn`: 5 buttons, one per cocktail
- `.hidden` class: CSS class to hide/show status messages

---

## 4.2 CSS Styling (static/style.css)

**Keep It Simple:**
```css
/* Basic styling - plain and functional */

body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h1 {
    text-align: center;
    margin-bottom: 30px;
    color: #333;
}

/* Status Messages */
.status-container {
    margin-bottom: 30px;
    min-height: 60px;
}

#pour-status,
#refill-status {
    padding: 15px;
    margin: 10px 0;
    border-radius: 4px;
    font-size: 18px;
    font-weight: bold;
}

#pour-status {
    background-color: #e3f2fd;
    color: #1976d2;
    border: 2px solid #1976d2;
}

#refill-status {
    background-color: #fff3e0;
    color: #f57c00;
    border: 2px solid #f57c00;
}

.hidden {
    display: none;
}

/* Drink Buttons */
.drinks-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.drink-btn {
    padding: 20px;
    font-size: 20px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.drink-btn:hover {
    background-color: #45a049;
}

.drink-btn:active {
    background-color: #3d8b40;
}

.drink-btn:disabled {
    background-color: #cccccc;
    color: #666666;
    cursor: not-allowed;
}

/* Touch-friendly sizing for Pi touchscreen */
@media (max-width: 800px) {
    .drink-btn {
        padding: 25px;
        font-size: 22px;
    }
}
```

**Design Notes:**
- Plain colored buttons (green)
- Large, touch-friendly (20px+ padding)
- Clear visual states (hover, active, disabled)
- Status messages in colored boxes
- Minimal decorative elements

---

## 4.3 JavaScript Logic (static/script.js)

**Implementation:**

```javascript
// Poll interval (milliseconds)
const POLL_INTERVAL = 2000;

// Start polling when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateStatus();
    setInterval(updateStatus, POLL_INTERVAL);
});

/**
 * Fetch current system status and update UI
 */
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update pour status
        if (data.pouring && data.current_drink) {
            document.getElementById('pour-status').classList.remove('hidden');
            document.getElementById('current-drink').textContent = data.current_drink;
            disableAllButtons();
        } else {
            document.getElementById('pour-status').classList.add('hidden');
            enableAllButtons();
        }
        
        // Update refill status
        const refillingReservoirs = [];
        for (let i = 1; i <= 4; i++) {
            if (data.refilling[i]) {
                refillingReservoirs.push(`Reservoir ${i}`);
            }
        }
        
        if (refillingReservoirs.length > 0) {
            document.getElementById('refill-status').classList.remove('hidden');
            document.getElementById('refill-reservoirs').textContent = refillingReservoirs.join(', ');
        } else {
            document.getElementById('refill-status').classList.add('hidden');
        }
        
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

/**
 * Order a drink
 */
async function pourDrink(drinkName) {
    try {
        const response = await fetch(`/api/pour/${encodeURIComponent(drinkName)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            console.log(`Ordered: ${drinkName}`);
            // Status polling will update UI automatically
        } else {
            const error = await response.json();
            alert(`Error: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Error ordering drink:', error);
        alert('Failed to order drink. Please try again.');
    }
}

/**
 * Disable all drink buttons
 */
function disableAllButtons() {
    const buttons = document.querySelectorAll('.drink-btn');
    buttons.forEach(button => {
        button.disabled = true;
    });
}

/**
 * Enable all drink buttons
 */
function enableAllButtons() {
    const buttons = document.querySelectorAll('.drink-btn');
    buttons.forEach(button => {
        button.disabled = false;
    });
}
```

**Function Breakdown:**

**1. updateStatus()**
- Calls `/api/status` every 2 seconds
- Checks `data.pouring`:
  - If true: Show "Pouring: [drink name]", disable buttons
  - If false: Hide pour message, enable buttons
- Checks `data.refilling` for each reservoir (1-4):
  - Build list of refilling reservoirs
  - If any refilling: Show "Refilling: Reservoir X, Y..."
  - If none: Hide refill message

**2. pourDrink(drinkName)**
- POST to `/api/pour/<drinkName>`
- If successful: do nothing (status polling will update UI)
- If error: show alert with error message
- Don't manually update UI - let status polling handle it

**3. disableAllButtons()**
- Set `disabled = true` on all `.drink-btn` elements
- Called when `data.pouring === true`

**4. enableAllButtons()**
- Set `disabled = false` on all `.drink-btn` elements
- Called when `data.pouring === false`

---

## 4.4 User Experience Flow

**Idle State:**
```
┌─────────────────────────────┐
│    Smart Bartender          │
├─────────────────────────────┤
│ (no status messages shown)  │
├─────────────────────────────┤
│ [Vodka Cranberry]           │ ← All buttons enabled
│ [Screwdriver]               │
│ [Rum Punch]                 │
│ [Madras]                    │
│ [Bay Breeze]                │
└─────────────────────────────┘
```

**User Clicks "Rum Punch":**
```
┌─────────────────────────────┐
│    Smart Bartender          │
├─────────────────────────────┤
│ Pouring: Rum Punch          │ ← Blue status box
├─────────────────────────────┤
│ [Vodka Cranberry]  (grayed) │ ← All buttons disabled
│ [Screwdriver]      (grayed) │
│ [Rum Punch]        (grayed) │
│ [Madras]           (grayed) │
│ [Bay Breeze]       (grayed) │
└─────────────────────────────┘
```

**While Pouring, Reservoir 2 Goes Low:**
```
┌─────────────────────────────┐
│    Smart Bartender          │
├─────────────────────────────┤
│ Pouring: Rum Punch          │ ← Blue box
│ Refilling: Reservoir 2      │ ← Orange box
├─────────────────────────────┤
│ [Vodka Cranberry]  (grayed) │
│ [Screwdriver]      (grayed) │
│ [Rum Punch]        (grayed) │
│ [Madras]           (grayed) │
│ [Bay Breeze]       (grayed) │
└─────────────────────────────┘
```

**Pour Complete, Still Refilling:**
```
┌─────────────────────────────┐
│    Smart Bartender          │
├─────────────────────────────┤
│ Refilling: Reservoir 2      │ ← Only orange box
├─────────────────────────────┤
│ [Vodka Cranberry]           │ ← Buttons re-enabled
│ [Screwdriver]               │
│ [Rum Punch]                 │
│ [Madras]                    │
│ [Bay Breeze]                │
└─────────────────────────────┘
```

**Multiple Reservoirs Refilling:**
```
┌─────────────────────────────┐
│    Smart Bartender          │
├─────────────────────────────┤
│ Refilling: Reservoir 1, 3   │ ← Shows multiple
├─────────────────────────────┤
│ [Vodka Cranberry]           │ ← Can still order
│ [Screwdriver]               │
│ [Rum Punch]                 │
│ [Madras]                    │
│ [Bay Breeze]                │
└─────────────────────────────┘
```

---

## 4.5 Key Behaviors

**Button Behavior:**
- Enabled: Green, clickable
- Disabled: Gray, not clickable, cursor changes
- Buttons only disabled during pouring, NOT during refilling
- User can order drinks while reservoirs refill in background

**Status Message Behavior:**
- Hidden by default (no status messages in idle state)
- Pour status: Only shows during active pour, hides when complete
- Refill status: Only shows while at least one reservoir refilling
- Both can show simultaneously
- Messages update every 2 seconds via polling

**Error Handling:**
- If API call fails: Show browser alert with error
- If server unreachable: Console error (don't crash page)
- Buttons remain functional even if status polling fails

**No Loading Spinners:**
- Keep it simple - just show/hide status text
- No animations, no fancy transitions
- Just plain text updates

---

## 5. Recipes Database (recipes.json)

**Structure:**
```json
{
  "Vodka Cranberry": {
    "1": 50,    // Vodka: 50ml
    "2": 0,     // Rum: 0ml
    "3": 0,     // OJ: 0ml
    "4": 100    // Cran: 100ml
  },
  "Screwdriver": {
    "1": 50,
    "2": 0,
    "3": 100,
    "4": 0
  },
  "Rum Punch": {
    "1": 0,
    "2": 50,
    "3": 75,
    "4": 75
  },
  "Madras": {
    "1": 50,
    "2": 0,
    "3": 50,
    "4": 100
  },
  "Bay Breeze": {
    "1": 50,
    "2": 0,
    "3": 75,
    "4": 75
  }
}
```

**Notes:**
- Keys are ingredient reservoir numbers (as strings)
- Values are milliliters (integers)
- Easy to add more recipes later
- Can be edited without code changes