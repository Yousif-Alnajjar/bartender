"""
Comprehensive tests for hardware control module
Tests GPIO control, reservoir management, and refilling logic
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import threading

import config
from hardware import BartenderHardware


class TestBartenderHardware(unittest.TestCase):
    """Test suite for BartenderHardware class"""

    def setUp(self):
        """Set up test fixtures"""
        # Always run in simulation mode for testing
        self.hw = BartenderHardware(simulation_mode=True)

    def tearDown(self):
        """Clean up after tests"""
        self.hw.cleanup()

    # Initialization Tests

    def test_initialization(self):
        """Test hardware initialization"""
        self.assertTrue(self.hw.simulation_mode)
        self.assertIsNone(self.hw.gpio_handle)
        self.assertTrue(self.hw.running)
        self.assertIsNotNone(self.hw.monitor_thread)

    def test_initial_reservoir_levels(self):
        """Test that reservoirs start at full capacity"""
        for reservoir_num in range(1, 5):
            self.assertEqual(
                self.hw.reservoir_levels[reservoir_num],
                config.RESERVOIR_CAPACITY_ML,
                f"Reservoir {reservoir_num} should start full"
            )

    def test_initial_refilling_status(self):
        """Test that no reservoirs are refilling at start"""
        for reservoir_num in range(1, 5):
            self.assertFalse(
                self.hw.refilling[reservoir_num],
                f"Reservoir {reservoir_num} should not be refilling at start"
            )

    # Pump Control Tests

    def test_activate_pump_valid(self):
        """Test activating a valid pump"""
        for pump_num in range(1, 5):
            # Should not raise any exception
            self.hw.activate_pump(pump_num)

    def test_deactivate_pump_valid(self):
        """Test deactivating a valid pump"""
        for pump_num in range(1, 5):
            # Should not raise any exception
            self.hw.deactivate_pump(pump_num)

    def test_activate_pump_invalid(self):
        """Test activating invalid pump number raises error"""
        with self.assertRaises(ValueError):
            self.hw.activate_pump(0)
        with self.assertRaises(ValueError):
            self.hw.activate_pump(5)

    def test_deactivate_pump_invalid(self):
        """Test deactivating invalid pump number raises error"""
        with self.assertRaises(ValueError):
            self.hw.deactivate_pump(0)
        with self.assertRaises(ValueError):
            self.hw.deactivate_pump(99)

    # Valve Control Tests

    def test_open_valve_valid(self):
        """Test opening a valid valve"""
        for valve_num in range(1, 5):
            # Should not raise any exception
            self.hw.open_valve(valve_num)

    def test_close_valve_valid(self):
        """Test closing a valid valve"""
        for valve_num in range(1, 5):
            # Should not raise any exception
            self.hw.close_valve(valve_num)

    def test_open_valve_invalid(self):
        """Test opening invalid valve number raises error"""
        with self.assertRaises(ValueError):
            self.hw.open_valve(-1)
        with self.assertRaises(ValueError):
            self.hw.open_valve(10)

    def test_close_valve_invalid(self):
        """Test closing invalid valve number raises error"""
        with self.assertRaises(ValueError):
            self.hw.close_valve(0)
        with self.assertRaises(ValueError):
            self.hw.close_valve(100)

    # Float Switch Tests

    def test_read_float_switch_valid(self):
        """Test reading valid float switch"""
        for sensor_num in range(1, 5):
            result = self.hw.read_float_switch(sensor_num)
            self.assertIsInstance(result, bool)

    def test_read_float_switch_invalid(self):
        """Test reading invalid float switch raises error"""
        with self.assertRaises(ValueError):
            self.hw.read_float_switch(0)
        with self.assertRaises(ValueError):
            self.hw.read_float_switch(5)

    def test_float_switch_simulation_logic(self):
        """Test float switch simulation logic based on level"""
        # Set level above threshold
        self.hw.reservoir_levels[1] = config.REFILL_THRESHOLD_ML + 50
        self.assertTrue(self.hw.read_float_switch(1))

        # Set level below threshold
        self.hw.reservoir_levels[1] = config.REFILL_THRESHOLD_ML - 50
        self.assertFalse(self.hw.read_float_switch(1))

    # Pour Tests

    def test_pour_basic(self):
        """Test basic pour operation"""
        initial_level = self.hw.reservoir_levels[1]
        pour_amount = 50

        self.hw.pour(1, pour_amount)

        # Check that level decreased
        expected_level = initial_level - pour_amount
        self.assertEqual(self.hw.reservoir_levels[1], expected_level)

    def test_pour_all_valves(self):
        """Test pouring from all valves"""
        for valve_num in range(1, 5):
            initial_level = self.hw.reservoir_levels[valve_num]
            pour_amount = 30

            self.hw.pour(valve_num, pour_amount)

            expected_level = initial_level - pour_amount
            self.assertEqual(self.hw.reservoir_levels[valve_num], expected_level)

    def test_pour_zero_amount(self):
        """Test that pouring 0ml does nothing"""
        initial_level = self.hw.reservoir_levels[1]

        self.hw.pour(1, 0)

        self.assertEqual(self.hw.reservoir_levels[1], initial_level)

    def test_pour_negative_amount(self):
        """Test that pouring negative amount does nothing"""
        initial_level = self.hw.reservoir_levels[1]

        self.hw.pour(1, -50)

        self.assertEqual(self.hw.reservoir_levels[1], initial_level)

    def test_pour_level_cannot_go_negative(self):
        """Test that reservoir level doesn't go below zero"""
        self.hw.reservoir_levels[1] = 30

        self.hw.pour(1, 100)

        self.assertEqual(self.hw.reservoir_levels[1], 0)

    def test_pour_time_calculation(self):
        """Test that pour time is calculated correctly"""
        valve_num = 1
        ml = 80
        expected_time = ml / config.ML_PER_SECOND[valve_num]

        start_time = time.time()
        self.hw.pour(valve_num, ml)
        elapsed_time = time.time() - start_time

        # Allow 0.5s tolerance for processing time
        self.assertAlmostEqual(elapsed_time, expected_time, delta=0.5)

    def test_pour_max_time_limit(self):
        """Test that pour time is limited by MAX_POUR_TIME"""
        valve_num = 1
        # Request amount that would exceed max time
        excessive_ml = config.ML_PER_SECOND[valve_num] * (config.MAX_POUR_TIME + 10)

        start_time = time.time()
        self.hw.pour(valve_num, excessive_ml)
        elapsed_time = time.time() - start_time

        # Should be limited to MAX_POUR_TIME
        self.assertLess(elapsed_time, config.MAX_POUR_TIME + 1)

    def test_pour_invalid_valve(self):
        """Test pouring from invalid valve raises error"""
        with self.assertRaises(ValueError):
            self.hw.pour(0, 50)
        with self.assertRaises(ValueError):
            self.hw.pour(5, 50)

    # Refill Tests

    def test_refill_basic(self):
        """Test basic refill operation"""
        # Drain reservoir
        self.hw.reservoir_levels[1] = 100

        self.hw.refill_reservoir(1)

        # Should be back to full
        self.assertEqual(self.hw.reservoir_levels[1], config.RESERVOIR_CAPACITY_ML)

    def test_refill_all_reservoirs(self):
        """Test refilling all reservoirs"""
        # Drain all reservoirs
        for reservoir_num in range(1, 5):
            self.hw.reservoir_levels[reservoir_num] = 50

        # Refill all
        for reservoir_num in range(1, 5):
            self.hw.refill_reservoir(reservoir_num)
            # In simulation, allow small tolerance due to timing
            self.assertGreaterEqual(
                self.hw.reservoir_levels[reservoir_num],
                config.REFILL_THRESHOLD_ML
            )

    def test_refill_prevents_concurrent_refills(self):
        """Test that concurrent refills of same reservoir are prevented"""
        self.hw.reservoir_levels[1] = 50

        # Start first refill in thread
        thread1 = threading.Thread(target=self.hw.refill_reservoir, args=(1,))
        thread1.start()

        # Give it time to acquire lock
        time.sleep(0.1)

        # Try second refill (should return immediately due to lock)
        start_time = time.time()
        self.hw.refill_reservoir(1)
        elapsed = time.time() - start_time

        # Second call should return almost immediately (lock not acquired)
        self.assertLess(elapsed, 0.5)

        thread1.join()

    def test_refill_invalid_reservoir(self):
        """Test refilling invalid reservoir raises error"""
        with self.assertRaises(ValueError):
            self.hw.refill_reservoir(0)
        with self.assertRaises(ValueError):
            self.hw.refill_reservoir(5)

    def test_refill_status_tracking(self):
        """Test that refilling status is tracked correctly"""
        self.hw.reservoir_levels[1] = 50

        # Start refill in thread
        thread = threading.Thread(target=self.hw.refill_reservoir, args=(1,))
        thread.start()

        # Give it time to start
        time.sleep(0.1)

        # Should be refilling
        self.assertTrue(self.hw.refilling[1])

        # Wait for completion
        thread.join()

        # Should no longer be refilling
        self.assertFalse(self.hw.refilling[1])

    # Complete Recipe Tests

    def test_vodka_cranberry_recipe(self):
        """Test making Vodka Cranberry (50ml vodka + 100ml cranberry)"""
        initial_vodka = self.hw.reservoir_levels[1]
        initial_cranberry = self.hw.reservoir_levels[4]

        # Pour ingredients
        self.hw.pour(1, 50)   # Vodka
        self.hw.pour(4, 100)  # Cranberry

        self.assertEqual(self.hw.reservoir_levels[1], initial_vodka - 50)
        self.assertEqual(self.hw.reservoir_levels[4], initial_cranberry - 100)

    def test_screwdriver_recipe(self):
        """Test making Screwdriver (50ml vodka + 100ml OJ)"""
        initial_vodka = self.hw.reservoir_levels[1]
        initial_oj = self.hw.reservoir_levels[3]

        self.hw.pour(1, 50)   # Vodka
        self.hw.pour(3, 100)  # OJ

        self.assertEqual(self.hw.reservoir_levels[1], initial_vodka - 50)
        self.assertEqual(self.hw.reservoir_levels[3], initial_oj - 100)

    def test_rum_punch_recipe(self):
        """Test making Rum Punch (50ml rum + 75ml OJ + 75ml cranberry)"""
        initial_rum = self.hw.reservoir_levels[2]
        initial_oj = self.hw.reservoir_levels[3]
        initial_cranberry = self.hw.reservoir_levels[4]

        self.hw.pour(2, 50)  # Rum
        self.hw.pour(3, 75)  # OJ
        self.hw.pour(4, 75)  # Cranberry

        self.assertEqual(self.hw.reservoir_levels[2], initial_rum - 50)
        self.assertEqual(self.hw.reservoir_levels[3], initial_oj - 75)
        self.assertEqual(self.hw.reservoir_levels[4], initial_cranberry - 75)

    def test_multiple_drinks_sequence(self):
        """Test making multiple drinks in sequence"""
        # Make 3 Vodka Cranberries
        for _ in range(3):
            self.hw.pour(1, 50)
            self.hw.pour(4, 100)

        # Check levels
        expected_vodka = config.RESERVOIR_CAPACITY_ML - (50 * 3)
        expected_cranberry = config.RESERVOIR_CAPACITY_ML - (100 * 3)

        self.assertEqual(self.hw.reservoir_levels[1], expected_vodka)
        self.assertEqual(self.hw.reservoir_levels[4], expected_cranberry)

    # Monitoring Thread Tests

    def test_monitoring_thread_starts(self):
        """Test that monitoring thread starts on initialization"""
        self.assertTrue(self.hw.running)
        self.assertIsNotNone(self.hw.monitor_thread)
        self.assertTrue(self.hw.monitor_thread.is_alive())

    def test_monitoring_thread_stops_on_cleanup(self):
        """Test that monitoring thread stops on cleanup"""
        self.hw.cleanup()

        self.assertFalse(self.hw.running)
        # Give thread time to stop
        time.sleep(0.5)
        if self.hw.monitor_thread:
            self.assertFalse(self.hw.monitor_thread.is_alive())

    # Thread Safety Tests

    def test_concurrent_pours_different_valves(self):
        """Test concurrent pours from different valves"""
        def pour_task(valve_num, ml):
            self.hw.pour(valve_num, ml)

        threads = []
        for valve_num in range(1, 5):
            thread = threading.Thread(target=pour_task, args=(valve_num, 30))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All pours should complete successfully
        for reservoir_num in range(1, 5):
            expected = config.RESERVOIR_CAPACITY_ML - 30
            self.assertEqual(self.hw.reservoir_levels[reservoir_num], expected)

    # Configuration Tests

    def test_gpio_pin_mappings_complete(self):
        """Test that all GPIO pin mappings are configured"""
        self.assertEqual(len(config.PUMP_PINS), 4)
        self.assertEqual(len(config.VALVE_PINS), 4)
        self.assertEqual(len(config.FLOAT_PINS), 4)

    def test_ingredient_mappings_complete(self):
        """Test that all ingredients are mapped"""
        self.assertEqual(len(config.INGREDIENTS), 4)
        self.assertIn(1, config.INGREDIENTS)
        self.assertIn(2, config.INGREDIENTS)
        self.assertIn(3, config.INGREDIENTS)
        self.assertIn(4, config.INGREDIENTS)

    def test_calibration_values_exist(self):
        """Test that calibration values exist for all valves"""
        self.assertEqual(len(config.ML_PER_SECOND), 4)
        for valve_num in range(1, 5):
            self.assertIn(valve_num, config.ML_PER_SECOND)
            self.assertGreater(config.ML_PER_SECOND[valve_num], 0)


if __name__ == '__main__':
    unittest.main()
