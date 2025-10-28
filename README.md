# Smart Bartender

An automated cocktail dispensing system powered by Raspberry Pi 5, featuring a web-based interface for selecting and pouring drinks.

## Features

- 4 ingredient reservoirs (Vodka, Rum, Orange Juice, Cranberry Juice)
- 5 pre-programmed cocktails
- Automatic reservoir refilling
- Touch-friendly web interface
- Real-time status updates
- Safe GPIO control with timeout protection

## Cocktails Available

1. **Vodka Cranberry** - 50ml Vodka + 100ml Cranberry Juice
2. **Screwdriver** - 50ml Vodka + 100ml Orange Juice
3. **Rum Punch** - 50ml Rum + 75ml Orange Juice + 75ml Cranberry Juice
4. **Madras** - 50ml Vodka + 50ml Orange Juice + 100ml Cranberry Juice
5. **Bay Breeze** - 50ml Vodka + 75ml Orange Juice + 75ml Cranberry Juice

## Hardware Requirements

- Raspberry Pi 5
- 7" touchscreen display
- 4x Kamoer KHPP260 peristaltic pumps (220ml/min)
- 4x 12V solenoid valves
- 4x float switches
- 8-channel relay board (active LOW)
- 12V 5A power supply
- Power distribution block
- 4x 400ml wall-mounted reservoirs
- 4x floor bottles (1-1.75L)
- Tubing (4mm ID)

## GPIO Pin Mapping

### Outputs (Relays)
- GPIO 17 → Pump 1 (Vodka)
- GPIO 27 → Pump 2 (Rum)
- GPIO 22 → Pump 3 (Orange Juice)
- GPIO 23 → Pump 4 (Cranberry Juice)
- GPIO 24 → Valve 1 (Vodka)
- GPIO 25 → Valve 2 (Rum)
- GPIO 5  → Valve 3 (Orange Juice)
- GPIO 6  → Valve 4 (Cranberry Juice)

### Inputs (Float Switches)
- GPIO 16 → Float Switch 1 (Vodka)
- GPIO 20 → Float Switch 2 (Rum)
- GPIO 21 → Float Switch 3 (Orange Juice)
- GPIO 26 → Float Switch 4 (Cranberry Juice)

## Installation

### 1. Clone or Copy Files

Transfer all files to your Raspberry Pi 5:
```bash
cd ~
mkdir smart_bartender
cd smart_bartender
# Copy all project files here
```

### 2. Install System Dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-venv python3-lgpio -y
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure GPIO Permissions

Add your user to the gpio group:
```bash
sudo usermod -a -G gpio $USER
```

Log out and back in for the changes to take effect.

### 6. Test Installation

Run in simulation mode first (no hardware required):
```bash
python3 app.py
```

Open a browser and navigate to:
```
http://localhost:5000
```

## Configuration

Edit [config.py](config.py) to customize:

- **GPIO pins** - If you use different pin assignments
- **ML_PER_SECOND** - Calibrate pour rates after testing
- **RESERVOIR_CAPACITY_ML** - Adjust for your reservoir size
- **REFILL_THRESHOLD_ML** - When to trigger automatic refilling
- **Safety timeouts** - Maximum operation times

### Calibration

To calibrate pour rates:
1. Manually open a valve for exactly 10 seconds
2. Measure how many ml were dispensed
3. Calculate: `ML_PER_SECOND = measured_ml / 10`
4. Update [config.py](config.py) with the new value
5. Repeat for each valve

## Usage

### Starting the Server

```bash
cd ~/smart_bartender
source venv/bin/activate
python3 app.py
```

The web interface will be available at:
- Local: `http://localhost:5000`
- Network: `http://<raspberry-pi-ip>:5000`

### Web Interface

1. Open the web interface on the Pi's touchscreen or any browser
2. Click a drink button to start pouring
3. Status messages show pouring and refilling progress
4. Buttons are disabled during pouring
5. Automatic refilling happens in the background

### REST API Endpoints

- `GET /` - Web interface
- `GET /api/status` - Current system status
- `GET /api/recipes` - List all recipes
- `POST /api/pour/<drink_name>` - Pour a drink
- `POST /api/refill/<reservoir_num>` - Manual refill

### Manual Control (Testing)

For testing individual components:
- `POST /api/manual/valve/<num>/open` - Open valve
- `POST /api/manual/valve/<num>/close` - Close valve
- `POST /api/manual/pump/<num>/on` - Turn on pump
- `POST /api/manual/pump/<num>/off` - Turn off pump

## Running at Startup

### Option 1: systemd Service

Create `/etc/systemd/system/bartender.service`:

```ini
[Unit]
Description=Smart Bartender Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart_bartender
Environment="PATH=/home/pi/smart_bartender/venv/bin"
ExecStart=/home/pi/smart_bartender/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable bartender
sudo systemctl start bartender
```

### Option 2: Autostart (Desktop)

Add to `~/.config/autostart/bartender.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Smart Bartender
Exec=/home/pi/smart_bartender/venv/bin/python3 /home/pi/smart_bartender/app.py
Terminal=false
```

## Adding New Recipes

Edit [recipes.json](recipes.json):

```json
{
  "New Drink Name": {
    "1": 50,   // Vodka ml
    "2": 0,    // Rum ml
    "3": 100,  // Orange Juice ml
    "4": 50    // Cranberry Juice ml
  }
}
```

Then update [templates/index.html](templates/index.html) to add a button:

```html
<button class="drink-btn" onclick="pourDrink('New Drink Name')">
    New Drink Name
</button>
```

Restart the server to apply changes.

## Troubleshooting

### GPIO Permission Denied
```bash
sudo usermod -a -G gpio $USER
# Log out and back in
```

### lgpio Not Found
```bash
sudo apt install python3-lgpio
pip install lgpio
```

### Pumps/Valves Not Working
- Check relay board connections
- Verify 12V power supply is connected
- Test relays manually using manual control endpoints
- Check logs in `logs/bartender.log`

### Float Switches Not Responding
- Verify float switches are wired correctly (normally open)
- Check GPIO pins with pull-up resistors enabled
- Test with multimeter to ensure switch changes state

### Web Interface Not Loading
- Verify Flask is running: `sudo netstat -tulpn | grep 5000`
- Check firewall: `sudo ufw allow 5000`
- Try accessing via IP address instead of hostname

## Safety Features

- **Maximum pour time** - Prevents overflow (30s default)
- **Maximum pump time** - Prevents dry running (180s default)
- **Refill timeout** - Prevents stuck pumps (120s default)
- **Automatic cleanup** - GPIO pins reset on shutdown
- **Thread-safe refilling** - Prevents concurrent refills of same reservoir

## Logs

Logs are written to [logs/bartender.log](logs/bartender.log):
```bash
tail -f logs/bartender.log
```

## Project Structure

```
smart_bartender/
├── app.py                 # Flask application & API
├── hardware.py            # GPIO control class
├── config.py              # Configuration constants
├── recipes.json           # Drink recipes database
├── static/
│   ├── style.css         # Styling
│   └── script.js         # Frontend logic
├── templates/
│   └── index.html        # Main UI
├── logs/
│   └── bartender.log     # Event logging
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## License

This project is provided as-is for educational and personal use.

## Credits

Built according to specifications in [INSTRUCTIONS.MD](INSTRUCTIONS.MD)

---

**Enjoy your automated cocktails responsibly!**
