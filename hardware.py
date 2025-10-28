"""
Hardware Control Module for Smart Bartender
Manages GPIO control for pumps, valves, and float switches
"""

import time
import logging
import threading
from typing import Dict, Optional

try:
    import lgpio
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("WARNING: lgpio not available. Running in simulation mode.")

import config


class BartenderHardware:
    """
    Controls all hardware components of the Smart Bartender system.
    Manages pumps, valves, float switches, and automatic reservoir refilling.
    """

    def __init__(self, simulation_mode: bool = False):
        """
        Initialize hardware control.

        Args:
            simulation_mode: If True, simulate hardware without actual GPIO
        """
        self.simulation_mode = simulation_mode or not GPIO_AVAILABLE
        self.gpio_handle = None
        self.running = False
        self.monitor_thread = None

        # Track reservoir levels (estimated)
        self.reservoir_levels: Dict[int, float] = {
            1: config.RESERVOIR_CAPACITY_ML,
            2: config.RESERVOIR_CAPACITY_ML,
            3: config.RESERVOIR_CAPACITY_ML,
            4: config.RESERVOIR_CAPACITY_ML
        }

        # Track refilling status
        self.refilling: Dict[int, bool] = {
            1: False,
            2: False,
            3: False,
            4: False
        }

        # Thread locks for safety
        self.refill_locks: Dict[int, threading.Lock] = {
            1: threading.Lock(),
            2: threading.Lock(),
            3: threading.Lock(),
            4: threading.Lock()
        }

        # Setup logging
        logging.basicConfig(
            filename=config.LOG_FILE,
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize GPIO
        self._init_gpio()

        # Start background monitoring
        self._start_monitoring()

    def _init_gpio(self):
        """Initialize GPIO pins and set default states"""
        if self.simulation_mode:
            self.logger.info("Running in SIMULATION MODE - no actual GPIO control")
            return

        try:
            # Open GPIO chip (gpiochip4 for Raspberry Pi 5)
            self.gpio_handle = lgpio.gpiochip_open(0)  # Usually 0 maps to gpiochip4
            self.logger.info(f"GPIO chip opened: {self.gpio_handle}")

            # Configure pump pins (outputs, initially HIGH = relay OFF)
            for pump_num, pin in config.PUMP_PINS.items():
                lgpio.gpio_claim_output(self.gpio_handle, pin, 1)  # 1 = HIGH = OFF
                self.logger.info(f"Pump {pump_num} pin {pin} initialized (OFF)")

            # Configure valve pins (outputs, initially HIGH = relay OFF)
            for valve_num, pin in config.VALVE_PINS.items():
                lgpio.gpio_claim_output(self.gpio_handle, pin, 1)  # 1 = HIGH = OFF
                self.logger.info(f"Valve {valve_num} pin {pin} initialized (OFF)")

            # Configure float switch pins (inputs with pull-ups)
            for sensor_num, pin in config.FLOAT_PINS.items():
                lgpio.gpio_claim_input(self.gpio_handle, pin, lgpio.SET_PULL_UP)
                self.logger.info(f"Float switch {sensor_num} pin {pin} initialized")

            self.logger.info("All GPIO pins initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {e}")
            self.simulation_mode = True
            self.logger.warning("Falling back to simulation mode")

    def activate_pump(self, pump_num: int):
        """Turn on a pump (set GPIO LOW to activate relay)"""
        if pump_num not in config.PUMP_PINS:
            raise ValueError(f"Invalid pump number: {pump_num}")

        if self.simulation_mode:
            self.logger.info(f"[SIM] Pump {pump_num} activated")
            return

        try:
            pin = config.PUMP_PINS[pump_num]
            lgpio.gpio_write(self.gpio_handle, pin, 0)  # LOW = relay ON
            self.logger.info(f"Pump {pump_num} activated (pin {pin} LOW)")
        except Exception as e:
            self.logger.error(f"Failed to activate pump {pump_num}: {e}")

    def deactivate_pump(self, pump_num: int):
        """Turn off a pump (set GPIO HIGH to deactivate relay)"""
        if pump_num not in config.PUMP_PINS:
            raise ValueError(f"Invalid pump number: {pump_num}")

        if self.simulation_mode:
            self.logger.info(f"[SIM] Pump {pump_num} deactivated")
            return

        try:
            pin = config.PUMP_PINS[pump_num]
            lgpio.gpio_write(self.gpio_handle, pin, 1)  # HIGH = relay OFF
            self.logger.info(f"Pump {pump_num} deactivated (pin {pin} HIGH)")
        except Exception as e:
            self.logger.error(f"Failed to deactivate pump {pump_num}: {e}")

    def open_valve(self, valve_num: int):
        """Open a valve (set GPIO LOW to activate relay)"""
        if valve_num not in config.VALVE_PINS:
            raise ValueError(f"Invalid valve number: {valve_num}")

        if self.simulation_mode:
            self.logger.info(f"[SIM] Valve {valve_num} opened")
            return

        try:
            pin = config.VALVE_PINS[valve_num]
            lgpio.gpio_write(self.gpio_handle, pin, 0)  # LOW = relay ON
            self.logger.info(f"Valve {valve_num} opened (pin {pin} LOW)")
        except Exception as e:
            self.logger.error(f"Failed to open valve {valve_num}: {e}")

    def close_valve(self, valve_num: int):
        """Close a valve (set GPIO HIGH to deactivate relay)"""
        if valve_num not in config.VALVE_PINS:
            raise ValueError(f"Invalid valve number: {valve_num}")

        if self.simulation_mode:
            self.logger.info(f"[SIM] Valve {valve_num} closed")
            return

        try:
            pin = config.VALVE_PINS[valve_num]
            lgpio.gpio_write(self.gpio_handle, pin, 1)  # HIGH = relay OFF
            self.logger.info(f"Valve {valve_num} closed (pin {pin} HIGH)")
        except Exception as e:
            self.logger.error(f"Failed to close valve {valve_num}: {e}")

    def read_float_switch(self, sensor_num: int) -> bool:
        """
        Read float switch state.

        Returns:
            True if level is OK (HIGH), False if level is low (LOW)
        """
        if sensor_num not in config.FLOAT_PINS:
            raise ValueError(f"Invalid float switch number: {sensor_num}")

        if self.simulation_mode:
            # In simulation, assume level is low if below threshold
            level_ok = self.reservoir_levels[sensor_num] > config.REFILL_THRESHOLD_ML
            self.logger.debug(f"[SIM] Float switch {sensor_num}: {level_ok}")
            return level_ok

        try:
            pin = config.FLOAT_PINS[sensor_num]
            state = lgpio.gpio_read(self.gpio_handle, pin)
            # HIGH (1) = level OK, LOW (0) = level low
            return state == 1
        except Exception as e:
            self.logger.error(f"Failed to read float switch {sensor_num}: {e}")
            return True  # Assume OK on error

    def pour(self, valve_num: int, ml: float):
        """
        Pour a specified amount through a valve.

        Args:
            valve_num: Valve number (1-4)
            ml: Milliliters to pour
        """
        if ml <= 0:
            return

        if valve_num not in config.VALVE_PINS:
            raise ValueError(f"Invalid valve number: {valve_num}")

        # Calculate pour time
        flow_rate = config.ML_PER_SECOND[valve_num]
        pour_time = ml / flow_rate

        # Apply safety limit
        if pour_time > config.MAX_POUR_TIME:
            self.logger.warning(f"Pour time {pour_time:.1f}s exceeds max {config.MAX_POUR_TIME}s")
            pour_time = config.MAX_POUR_TIME

        self.logger.info(f"Pouring {ml}ml through valve {valve_num} ({pour_time:.1f}s)")

        # Pour
        self.open_valve(valve_num)
        time.sleep(pour_time)
        self.close_valve(valve_num)

        # Update reservoir level
        self.reservoir_levels[valve_num] -= ml
        if self.reservoir_levels[valve_num] < 0:
            self.reservoir_levels[valve_num] = 0

        self.logger.info(f"Pour complete. Reservoir {valve_num} level: {self.reservoir_levels[valve_num]:.0f}ml")

    def refill_reservoir(self, reservoir_num: int):
        """
        Refill a reservoir from floor bottle.
        Runs until float switch indicates full or timeout.

        Args:
            reservoir_num: Reservoir number (1-4)
        """
        if reservoir_num not in config.PUMP_PINS:
            raise ValueError(f"Invalid reservoir number: {reservoir_num}")

        # Prevent concurrent refills of same reservoir
        if not self.refill_locks[reservoir_num].acquire(blocking=False):
            self.logger.warning(f"Reservoir {reservoir_num} already refilling")
            return

        try:
            self.refilling[reservoir_num] = True
            self.logger.info(f"Starting refill of reservoir {reservoir_num}")

            # Calculate expected refill time
            ml_needed = config.RESERVOIR_CAPACITY_ML - self.reservoir_levels[reservoir_num]
            expected_time = (ml_needed / config.PUMP_FLOW_RATE) * 60  # Convert to seconds
            timeout = min(expected_time * 1.5, config.REFILL_TIMEOUT)  # 1.5x expected or max

            self.logger.info(f"Refilling {ml_needed:.0f}ml, timeout: {timeout:.0f}s")

            # Start pump
            self.activate_pump(reservoir_num)
            start_time = time.time()

            # Monitor float switch
            while True:
                elapsed = time.time() - start_time

                # Check timeout
                if elapsed > timeout:
                    self.logger.warning(f"Refill timeout for reservoir {reservoir_num}")
                    break

                # Check float switch
                if self.read_float_switch(reservoir_num):
                    self.logger.info(f"Reservoir {reservoir_num} full (float switch)")
                    break

                time.sleep(0.5)  # Check every 500ms

            # Stop pump
            self.deactivate_pump(reservoir_num)

            # Reset reservoir level to full
            self.reservoir_levels[reservoir_num] = config.RESERVOIR_CAPACITY_ML

            self.logger.info(f"Refill complete for reservoir {reservoir_num}")

        except Exception as e:
            self.logger.error(f"Error during refill of reservoir {reservoir_num}: {e}")
        finally:
            self.refilling[reservoir_num] = False
            self.refill_locks[reservoir_num].release()

    def _monitor_levels(self):
        """Background thread to monitor reservoir levels and trigger refills"""
        self.logger.info("Level monitoring thread started")

        while self.running:
            try:
                for reservoir_num in range(1, 5):
                    # Check float switch
                    level_ok = self.read_float_switch(reservoir_num)

                    # If level is low and not already refilling, start refill
                    if not level_ok and not self.refilling[reservoir_num]:
                        self.logger.info(f"Low level detected in reservoir {reservoir_num}, starting refill")
                        # Spawn refill in separate thread
                        refill_thread = threading.Thread(
                            target=self.refill_reservoir,
                            args=(reservoir_num,),
                            daemon=True
                        )
                        refill_thread.start()

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                self.logger.error(f"Error in monitoring thread: {e}")
                time.sleep(5)  # Wait longer on error

        self.logger.info("Level monitoring thread stopped")

    def _start_monitoring(self):
        """Start the background monitoring thread"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_levels, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Background monitoring started")

    def cleanup(self):
        """Clean up GPIO and stop monitoring"""
        self.logger.info("Cleaning up hardware...")

        # Stop monitoring
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        if self.simulation_mode:
            self.logger.info("Simulation mode cleanup complete")
            return

        try:
            # Turn off all pumps and valves
            for pump_num in config.PUMP_PINS.keys():
                self.deactivate_pump(pump_num)

            for valve_num in config.VALVE_PINS.keys():
                self.close_valve(valve_num)

            # Close GPIO chip
            if self.gpio_handle is not None:
                lgpio.gpiochip_close(self.gpio_handle)
                self.logger.info("GPIO chip closed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

        self.logger.info("Hardware cleanup complete")
