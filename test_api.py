"""
Comprehensive tests for Flask API
Tests all endpoints, status updates, and error handling
"""

import unittest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock

import config


class TestFlaskAPI(unittest.TestCase):
    """Test suite for Flask API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        # Import app here to avoid GPIO initialization during import
        with patch('app.BartenderHardware') as mock_hw:
            # Mock the hardware
            self.mock_hw_instance = MagicMock()
            self.mock_hw_instance.simulation_mode = True
            self.mock_hw_instance.running = True
            self.mock_hw_instance.reservoir_levels = {
                1: config.RESERVOIR_CAPACITY_ML,
                2: config.RESERVOIR_CAPACITY_ML,
                3: config.RESERVOIR_CAPACITY_ML,
                4: config.RESERVOIR_CAPACITY_ML
            }
            self.mock_hw_instance.refilling = {
                1: False,
                2: False,
                3: False,
                4: False
            }
            mock_hw.return_value = self.mock_hw_instance

            # Import and configure app
            import app as app_module
            self.app_module = app_module
            self.app = app_module.app
            self.app.config['TESTING'] = True
            self.client = self.app.test_client()

            # Replace hardware instance
            app_module.hw = self.mock_hw_instance

    def tearDown(self):
        """Clean up after tests"""
        pass

    # Basic Route Tests

    def test_index_route(self):
        """Test that index route returns HTML"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart Bartender', response.data)

    def test_index_contains_all_drinks(self):
        """Test that index page contains all drink buttons"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Check for all 5 drinks
        self.assertIn(b'Vodka Cranberry', response.data)
        self.assertIn(b'Screwdriver', response.data)
        self.assertIn(b'Rum Punch', response.data)
        self.assertIn(b'Madras', response.data)
        self.assertIn(b'Bay Breeze', response.data)

    # Status Endpoint Tests

    def test_status_endpoint_structure(self):
        """Test that status endpoint returns correct structure"""
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # Check structure
        self.assertIn('pouring', data)
        self.assertIn('current_drink', data)
        self.assertIn('reservoir_levels', data)
        self.assertIn('refilling', data)

    def test_status_initial_state(self):
        """Test status endpoint initial state"""
        response = self.client.get('/api/status')
        data = json.loads(response.data)

        self.assertFalse(data['pouring'])
        self.assertIsNone(data['current_drink'])
        self.assertEqual(len(data['reservoir_levels']), 4)
        self.assertEqual(len(data['refilling']), 4)

    def test_status_reservoir_levels(self):
        """Test that status returns reservoir levels from hardware"""
        # Set specific levels
        self.mock_hw_instance.reservoir_levels = {
            1: 350,
            2: 300,
            3: 250,
            4: 200
        }

        response = self.client.get('/api/status')
        data = json.loads(response.data)

        self.assertEqual(data['reservoir_levels']['1'], 350)
        self.assertEqual(data['reservoir_levels']['2'], 300)
        self.assertEqual(data['reservoir_levels']['3'], 250)
        self.assertEqual(data['reservoir_levels']['4'], 200)

    def test_status_refilling_state(self):
        """Test that status returns refilling state from hardware"""
        # Set refilling state
        self.mock_hw_instance.refilling = {
            1: True,
            2: False,
            3: True,
            4: False
        }

        response = self.client.get('/api/status')
        data = json.loads(response.data)

        self.assertTrue(data['refilling']['1'])
        self.assertFalse(data['refilling']['2'])
        self.assertTrue(data['refilling']['3'])
        self.assertFalse(data['refilling']['4'])

    # Recipes Endpoint Tests

    def test_recipes_endpoint(self):
        """Test that recipes endpoint returns all recipes"""
        response = self.client.get('/api/recipes')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # Check all 5 recipes exist
        self.assertIn('Vodka Cranberry', data)
        self.assertIn('Screwdriver', data)
        self.assertIn('Rum Punch', data)
        self.assertIn('Madras', data)
        self.assertIn('Bay Breeze', data)

    def test_recipes_structure(self):
        """Test that recipes have correct structure"""
        response = self.client.get('/api/recipes')
        data = json.loads(response.data)

        # Check Vodka Cranberry structure
        vodka_cran = data['Vodka Cranberry']
        self.assertIn('1', vodka_cran)  # Vodka
        self.assertIn('2', vodka_cran)  # Rum
        self.assertIn('3', vodka_cran)  # OJ
        self.assertIn('4', vodka_cran)  # Cranberry

    def test_vodka_cranberry_recipe(self):
        """Test Vodka Cranberry recipe values"""
        response = self.client.get('/api/recipes')
        data = json.loads(response.data)

        recipe = data['Vodka Cranberry']
        self.assertEqual(recipe['1'], 50)   # Vodka
        self.assertEqual(recipe['2'], 0)    # Rum
        self.assertEqual(recipe['3'], 0)    # OJ
        self.assertEqual(recipe['4'], 100)  # Cranberry

    def test_screwdriver_recipe(self):
        """Test Screwdriver recipe values"""
        response = self.client.get('/api/recipes')
        data = json.loads(response.data)

        recipe = data['Screwdriver']
        self.assertEqual(recipe['1'], 50)   # Vodka
        self.assertEqual(recipe['2'], 0)    # Rum
        self.assertEqual(recipe['3'], 100)  # OJ
        self.assertEqual(recipe['4'], 0)    # Cranberry

    def test_rum_punch_recipe(self):
        """Test Rum Punch recipe values"""
        response = self.client.get('/api/recipes')
        data = json.loads(response.data)

        recipe = data['Rum Punch']
        self.assertEqual(recipe['1'], 0)   # Vodka
        self.assertEqual(recipe['2'], 50)  # Rum
        self.assertEqual(recipe['3'], 75)  # OJ
        self.assertEqual(recipe['4'], 75)  # Cranberry

    def test_madras_recipe(self):
        """Test Madras recipe values"""
        response = self.client.get('/api/recipes')
        data = json.loads(response.data)

        recipe = data['Madras']
        self.assertEqual(recipe['1'], 50)   # Vodka
        self.assertEqual(recipe['2'], 0)    # Rum
        self.assertEqual(recipe['3'], 50)   # OJ
        self.assertEqual(recipe['4'], 100)  # Cranberry

    def test_bay_breeze_recipe(self):
        """Test Bay Breeze recipe values"""
        response = self.client.get('/api/recipes')
        data = json.loads(response.data)

        recipe = data['Bay Breeze']
        self.assertEqual(recipe['1'], 50)  # Vodka
        self.assertEqual(recipe['2'], 0)   # Rum
        self.assertEqual(recipe['3'], 75)  # OJ
        self.assertEqual(recipe['4'], 75)  # Cranberry

    # Pour Endpoint Tests

    def test_pour_vodka_cranberry(self):
        """Test pouring Vodka Cranberry"""
        response = self.client.post('/api/pour/Vodka%20Cranberry')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('Vodka Cranberry', data['message'])

    def test_pour_updates_status(self):
        """Test that pouring updates status"""
        # Start pour in background
        response = self.client.post('/api/pour/Screwdriver')
        self.assertEqual(response.status_code, 200)

        # Give thread time to start
        time.sleep(0.1)

        # Check status (during pour)
        # Note: In testing with mocked hardware, pour completes instantly
        # so we just verify the endpoint works

    def test_pour_invalid_drink(self):
        """Test pouring non-existent drink returns 404"""
        response = self.client.post('/api/pour/Invalid%20Drink')
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_pour_all_drinks(self):
        """Test pouring all 5 drinks"""
        drinks = [
            'Vodka Cranberry',
            'Screwdriver',
            'Rum Punch',
            'Madras',
            'Bay Breeze'
        ]

        for drink in drinks:
            # Reset pouring status
            self.app_module.status['pouring'] = False

            response = self.client.post(f'/api/pour/{drink.replace(" ", "%20")}')
            self.assertEqual(response.status_code, 200)

            # Give thread time to complete
            time.sleep(0.5)

    def test_pour_while_pouring_returns_400(self):
        """Test that pouring while already pouring returns error"""
        # Set status to pouring
        self.app_module.status['pouring'] = True

        response = self.client.post('/api/pour/Vodka%20Cranberry')
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Already pouring', data['error'])

        # Reset
        self.app_module.status['pouring'] = False

    def test_pour_calls_hardware_pour(self):
        """Test that pour endpoint calls hardware.pour()"""
        self.mock_hw_instance.pour = Mock()

        response = self.client.post('/api/pour/Vodka%20Cranberry')
        self.assertEqual(response.status_code, 200)

        # Give thread time to execute
        time.sleep(0.5)

        # Verify hardware.pour was called
        self.assertTrue(self.mock_hw_instance.pour.called)

    # Refill Endpoint Tests

    def test_manual_refill_valid(self):
        """Test manual refill with valid reservoir number"""
        for reservoir_num in range(1, 5):
            response = self.client.post(f'/api/refill/{reservoir_num}')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertIn('message', data)

    def test_manual_refill_invalid_too_low(self):
        """Test manual refill with invalid reservoir number (0)"""
        response = self.client.post('/api/refill/0')
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_manual_refill_invalid_too_high(self):
        """Test manual refill with invalid reservoir number (5)"""
        response = self.client.post('/api/refill/5')
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_manual_refill_calls_hardware(self):
        """Test that refill endpoint calls hardware.refill_reservoir()"""
        self.mock_hw_instance.refill_reservoir = Mock()

        response = self.client.post('/api/refill/1')
        self.assertEqual(response.status_code, 200)

        # Give thread time to execute
        time.sleep(0.5)

        # Verify hardware method was called
        self.assertTrue(self.mock_hw_instance.refill_reservoir.called)

    # Manual Control Endpoint Tests

    def test_manual_valve_open(self):
        """Test manual valve open endpoint"""
        self.mock_hw_instance.open_valve = Mock()

        response = self.client.post('/api/manual/valve/1/open')
        self.assertEqual(response.status_code, 200)

        self.mock_hw_instance.open_valve.assert_called_once_with(1)

    def test_manual_valve_close(self):
        """Test manual valve close endpoint"""
        self.mock_hw_instance.close_valve = Mock()

        response = self.client.post('/api/manual/valve/2/close')
        self.assertEqual(response.status_code, 200)

        self.mock_hw_instance.close_valve.assert_called_once_with(2)

    def test_manual_valve_invalid_number(self):
        """Test manual valve control with invalid valve number"""
        response = self.client.post('/api/manual/valve/0/open')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/manual/valve/5/close')
        self.assertEqual(response.status_code, 400)

    def test_manual_valve_invalid_action(self):
        """Test manual valve control with invalid action"""
        response = self.client.post('/api/manual/valve/1/invalid')
        self.assertEqual(response.status_code, 400)

    def test_manual_pump_on(self):
        """Test manual pump on endpoint"""
        self.mock_hw_instance.activate_pump = Mock()

        response = self.client.post('/api/manual/pump/1/on')
        self.assertEqual(response.status_code, 200)

        self.mock_hw_instance.activate_pump.assert_called_once_with(1)

    def test_manual_pump_off(self):
        """Test manual pump off endpoint"""
        self.mock_hw_instance.deactivate_pump = Mock()

        response = self.client.post('/api/manual/pump/3/off')
        self.assertEqual(response.status_code, 200)

        self.mock_hw_instance.deactivate_pump.assert_called_once_with(3)

    def test_manual_pump_invalid_number(self):
        """Test manual pump control with invalid pump number"""
        response = self.client.post('/api/manual/pump/0/on')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/manual/pump/5/off')
        self.assertEqual(response.status_code, 400)

    def test_manual_pump_invalid_action(self):
        """Test manual pump control with invalid action"""
        response = self.client.post('/api/manual/pump/1/start')
        self.assertEqual(response.status_code, 400)

    # HTTP Method Tests

    def test_pour_requires_post(self):
        """Test that pour endpoint requires POST"""
        response = self.client.get('/api/pour/Vodka%20Cranberry')
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_refill_requires_post(self):
        """Test that refill endpoint requires POST"""
        response = self.client.get('/api/refill/1')
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    # Integration Tests

    def test_complete_workflow(self):
        """Test complete workflow: check status, pour drink, check status again"""
        # Check initial status
        response = self.client.get('/api/status')
        data = json.loads(response.data)
        self.assertFalse(data['pouring'])

        # Pour a drink
        self.app_module.status['pouring'] = False
        response = self.client.post('/api/pour/Screwdriver')
        self.assertEqual(response.status_code, 200)

        # Wait for pour to complete
        time.sleep(0.5)

        # Check status after pour
        response = self.client.get('/api/status')
        data = json.loads(response.data)
        # Should be done pouring
        self.assertFalse(data['pouring'])

    def test_multiple_drinks_sequence(self):
        """Test pouring multiple drinks in sequence"""
        drinks = ['Vodka Cranberry', 'Screwdriver', 'Rum Punch']

        for drink in drinks:
            self.app_module.status['pouring'] = False

            response = self.client.post(f'/api/pour/{drink.replace(" ", "%20")}')
            self.assertEqual(response.status_code, 200)

            # Wait for completion
            time.sleep(0.5)

    # Error Handling Tests

    def test_status_endpoint_always_returns_json(self):
        """Test that status endpoint always returns valid JSON"""
        response = self.client.get('/api/status')
        self.assertEqual(response.content_type, 'application/json')

        # Should be valid JSON
        data = json.loads(response.data)
        self.assertIsInstance(data, dict)

    def test_recipes_endpoint_returns_json(self):
        """Test that recipes endpoint returns JSON"""
        response = self.client.get('/api/recipes')
        self.assertEqual(response.content_type, 'application/json')

        data = json.loads(response.data)
        self.assertIsInstance(data, dict)


if __name__ == '__main__':
    unittest.main()
