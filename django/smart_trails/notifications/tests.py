import unittest
from datetime import datetime, timedelta
from notifications.alert_system import AlertAnalyzer, Alert


def make_sensor_data(
    temp=None, humidity=None, pressure=None,
    uv=None, lux=None,
    moisture=None,
    co2=None,
    is_raining=False, rain_last_hour=False,
    motion=0,
):
    """Build a sensor data dict matching the API payload structure."""
    return {
        'atmospheric': {
            'temperature': temp,
            'humidity': humidity,
            'pressure': pressure,
        },
        'light': {
            'uv_index': uv,
            'lux': lux,
        },
        'soil': {
            'moisture_percent': moisture,
        },
        'air_quality': {
            'co2_ppm': co2,
        },
        'precipitation': {
            'is_raining': is_raining,
            'rain_detected_last_hour': rain_last_hour,
        },
        'trail_activity': {
            'motion_count': motion,
        },
    }


class TestAlertAnalyzerBoundary(unittest.TestCase):
    """Boundary tests verify threshold comparisons at exact transition points."""

    def setUp(self):
        self.analyzer = AlertAnalyzer()

    def test_boundary_freezing_threshold_inclusive(self):
        """0.0°C, -0.1°C, and 0.1°C each produce the correct alert type."""
        # 0.0°C is < TEMP_FREEZING (0) → should NOT trigger freezing (it's not < 0)
        # Actually: TEMP_FREEZING = 0, check is `temp < self.TEMP_FREEZING`
        # So 0.0 is NOT < 0, falls to next elif: temp < 10 (hypothermia_wet check)

        # -0.1°C → freezing (warning)
        hazards = self.analyzer._check_thermal_hazards(-0.1, 50.0, False)
        self.assertEqual(len(hazards), 1)
        self.assertEqual(hazards[0]['type'], 'freezing')
        self.assertEqual(hazards[0]['severity'], 'warning')

        # 0.0°C → not freezing, falls to cold_dry (info) since 0 < 10 and dry
        hazards = self.analyzer._check_thermal_hazards(0.0, 50.0, False)
        self.assertEqual(len(hazards), 1)
        self.assertEqual(hazards[0]['type'], 'cold_dry')
        self.assertEqual(hazards[0]['severity'], 'info')

        # 0.1°C → also cold_dry (info), same bracket as 0.0
        hazards = self.analyzer._check_thermal_hazards(0.1, 50.0, False)
        self.assertEqual(len(hazards), 1)
        self.assertEqual(hazards[0]['type'], 'cold_dry')

    def test_boundary_humidity_triggers_hypothermia(self):
        """90.0% humidity at cold temperature triggers danger-level hypothermia."""
        # 5°C + humidity exactly 90% → is_wet = True (humidity > 90 is False,
        # but HUMIDITY_VERY_HIGH = 90, check is `humidity > self.HUMIDITY_VERY_HIGH`)
        # So 90.0 is NOT > 90 → is_wet = False → cold_dry
        hazards = self.analyzer._check_thermal_hazards(5.0, 90.0, False)
        self.assertEqual(hazards[0]['type'], 'cold_dry')

        # 90.1% → is_wet = True → hypothermia_wet (danger)
        hazards = self.analyzer._check_thermal_hazards(5.0, 90.1, False)
        self.assertEqual(hazards[0]['type'], 'hypothermia_wet')
        self.assertEqual(hazards[0]['severity'], 'danger')

    def test_boundary_pressure_storm_threshold(self):
        """Pressure at exactly the storm watch boundary behaves correctly."""
        # Storm threshold = 870 - 15 = 855
        # Check is `pressure < storm_threshold`, so 855.0 should NOT trigger
        hazards = self.analyzer._check_pressure_hazards(855.0)
        self.assertEqual(len(hazards), 0)

        # 854.9 → storm watch (warning)
        hazards = self.analyzer._check_pressure_hazards(854.9)
        self.assertEqual(len(hazards), 1)
        self.assertEqual(hazards[0]['type'], 'pressure_low')
        self.assertEqual(hazards[0]['severity'], 'warning')

    def test_boundary_uv_extreme_threshold(self):
        """UV index at exactly 11 triggers extreme (danger), 10.9 triggers very high (warning)."""
        # UV 11 → extreme (danger), check is `uv >= UV_EXTREME`
        hazards = self.analyzer._check_uv_exposure(11.0)
        self.assertEqual(len(hazards), 1)
        self.assertEqual(hazards[0]['type'], 'uv_extreme')
        self.assertEqual(hazards[0]['severity'], 'danger')

        # UV 10.9 → very high (warning)
        hazards = self.analyzer._check_uv_exposure(10.9)
        self.assertEqual(len(hazards), 1)
        self.assertEqual(hazards[0]['type'], 'uv_very_high')
        self.assertEqual(hazards[0]['severity'], 'warning')


class TestAlertAnalyzerDataResilience(unittest.TestCase):
    """Data resilience tests for incomplete or malformed sensor data."""

    def setUp(self):
        self.analyzer = AlertAnalyzer()

    def test_extract_sensor_data_missing_sections(self):
        """Empty payloads, partial sections, and missing fields resolve to None."""
        # Completely empty payload
        result = self.analyzer._extract_sensor_data({})
        self.assertIsNone(result['temp'])
        self.assertIsNone(result['humidity'])
        self.assertIsNone(result['pressure'])
        self.assertIsNone(result['uv'])
        self.assertIsNone(result['lux'])
        self.assertIsNone(result['co2'])
        self.assertIsNone(result['soil_moisture'])
        self.assertFalse(result['is_raining'])
        self.assertEqual(result['motion'], 0)

        # Partial payload — only atmospheric with one field
        result = self.analyzer._extract_sensor_data({
            'atmospheric': {'temperature': 15.0}
        })
        self.assertEqual(result['temp'], 15.0)
        self.assertIsNone(result['humidity'])
        self.assertIsNone(result['pressure'])
        self.assertIsNone(result['uv'])

    def test_extract_sensor_data_wrong_types(self):
        """Strings where floats are expected, int 1 where bool True is expected."""
        data = {
            'atmospheric': {
                'temperature': "not_a_number",
                'humidity': "high",
                'pressure': None,
            },
            'precipitation': {
                'is_raining': 1,  # int instead of bool
                'rain_detected_last_hour': 0,
            },
        }
        # Should not raise — _extract_sensor_data just passes values through
        result = self.analyzer._extract_sensor_data(data)
        self.assertEqual(result['temp'], "not_a_number")
        self.assertEqual(result['is_raining'], 1)  # truthy, will work in bool context

    def test_hypothermia_with_null_humidity(self):
        """When humidity is None, compound hypothermia logic falls back to cold_dry."""
        # 5°C, humidity=None, not raining → should be cold_dry, not hypothermia_wet
        hazards = self.analyzer._check_thermal_hazards(5.0, None, False)
        self.assertEqual(len(hazards), 1)
        self.assertEqual(hazards[0]['type'], 'cold_dry')
        self.assertEqual(hazards[0]['severity'], 'info')

        # Verify it doesn't crash or produce hypothermia_wet
        types = [h['type'] for h in hazards]
        self.assertNotIn('hypothermia_wet', types)


class TestAlertAnalyzerStatefulLogic(unittest.TestCase):
    """Stateful logic tests for pressure rate-of-change tracking."""

    def setUp(self):
        self.analyzer = AlertAnalyzer()

    def test_pressure_history_isolated_per_station(self):
        """Readings from one station do not contaminate calculations for another."""
        t0 = datetime(2026, 1, 1, 12, 0, 0)
        t1 = t0 + timedelta(minutes=30)

        # Station A: 870 → 864 (dropping fast)
        self.analyzer._get_pressure_rate('station-a', 870.0, t0)
        rate_a = self.analyzer._get_pressure_rate('station-a', 864.0, t1)

        # Station B: 870 → 872 (rising slightly)
        self.analyzer._get_pressure_rate('station-b', 870.0, t0)
        rate_b = self.analyzer._get_pressure_rate('station-b', 872.0, t1)

        # Station A should show negative rate, Station B positive
        self.assertIsNotNone(rate_a)
        self.assertLess(rate_a, 0)
        self.assertIsNotNone(rate_b)
        self.assertGreater(rate_b, 0)

        # Station A's rate should not be affected by Station B
        self.assertAlmostEqual(rate_a, -12.0, places=1)
        self.assertAlmostEqual(rate_b, 4.0, places=1)

    def test_pressure_rate_calculation_math(self):
        """870 hPa dropping to 864 hPa over 30 minutes yields -12 hPa/hour."""
        t0 = datetime(2026, 1, 1, 12, 0, 0)
        t1 = t0 + timedelta(minutes=30)

        # First reading stores history
        self.analyzer._get_pressure_rate('test-station', 870.0, t0)

        # Second reading calculates rate
        rate = self.analyzer._get_pressure_rate('test-station', 864.0, t1)

        # (864 - 870) / 0.5 hours = -12 hPa/hour
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, -12.0, places=1)

    def test_pressure_first_reading_stores_without_alert(self):
        """First-ever reading for a new station stores history without generating alert."""
        t0 = datetime(2026, 1, 1, 12, 0, 0)

        # Very low pressure on first reading — should still return None (no rate yet)
        rate = self.analyzer._get_pressure_rate('new-station', 830.0, t0)
        self.assertIsNone(rate)

        # Verify history was stored
        self.assertIn('new-station', self.analyzer._pressure_history)
        self.assertEqual(self.analyzer._pressure_history['new-station'][0], 830.0)

        # Full analyze() should not produce pressure rate alerts on first reading
        data = make_sensor_data(pressure=830.0)
        alerts = self.analyzer.analyze(
            data, station_name="Test", station_id="first-read-station", timestamp=t0
        )
        rate_alerts = [a for a in alerts if 'dropping' in a.title.lower()]
        self.assertEqual(len(rate_alerts), 0)


class TestAlertAnalyzerConsistency(unittest.TestCase):
    """Consistency tests ensuring different parts of the system agree."""

    def setUp(self):
        self.analyzer = AlertAnalyzer()

    def test_danger_flags_consistent_with_alerts(self):
        """Any condition triggering warning/danger alert also sets the UI flag to True."""
        test_cases = [
            # Freezing → temperature_is_dangerous
            make_sensor_data(temp=-5.0),
            # Hypothermia wet → temperature_is_dangerous
            make_sensor_data(temp=5.0, humidity=95.0, is_raining=True),
            # Heat → temperature_is_dangerous
            make_sensor_data(temp=32.0),
            # Low pressure → pressure_is_dangerous
            make_sensor_data(pressure=850.0),
            # Rain → is_raining_is_dangerous
            make_sensor_data(is_raining=True),
            # High CO2 → co2_ppm_is_dangerous
            make_sensor_data(co2=3000),
            # Saturated soil → moisture_percent_is_dangerous
            make_sensor_data(moisture=85.0),
        ]

        for data in test_cases:
            alerts = self.analyzer.analyze(data, station_name="Test")
            flags = self.analyzer.get_is_dangerous_flags(data)

            warning_or_danger = [a for a in alerts if a.severity in ('danger', 'warning')]

            for alert in warning_or_danger:
                if alert.category == 'temperature':
                    self.assertTrue(flags['temperature_is_dangerous'],
                                    f"Alert {alert.title} but temperature flag is False")
                elif alert.category == 'weather' and 'pressure' in alert.title.lower():
                    self.assertTrue(flags['pressure_is_dangerous'],
                                    f"Alert {alert.title} but pressure flag is False")
                elif alert.category == 'air_quality':
                    self.assertTrue(flags['co2_ppm_is_dangerous'],
                                    f"Alert {alert.title} but co2 flag is False")
                elif alert.category == 'trail' and 'mud' in alert.body.lower() or 'flood' in alert.body.lower():
                    self.assertTrue(flags['moisture_percent_is_dangerous'],
                                    f"Alert {alert.title} but moisture flag is False")

    def test_heat_and_cold_mutually_exclusive(self):
        """The elif chain prevents simultaneous heat and cold alerts."""
        # Test across a wide temperature range
        for temp in range(-20, 50):
            hazards = self.analyzer._check_thermal_hazards(float(temp), 50.0, False)
            types = [h['type'] for h in hazards]

            cold_types = {'severe_cold', 'freezing', 'hypothermia_wet', 'cold_dry'}
            heat_types = {'heat_stroke', 'heat_warning', 'heat_monitor'}

            has_cold = bool(cold_types & set(types))
            has_heat = bool(heat_types & set(types))

            self.assertFalse(has_cold and has_heat,
                             f"At {temp}°C got both cold ({types}) and heat alerts")
            # Should have at most one hazard
            self.assertLessEqual(len(hazards), 1,
                                 f"At {temp}°C got multiple hazards: {types}")

    def test_co2_thresholds_non_overlapping(self):
        """Every CO2 value produces exactly zero or one hazard, never two."""
        # Test across the full CO2 range including all threshold boundaries
        test_values = list(range(0, 50000, 100))
        # Add exact boundary values
        test_values.extend([999, 1000, 1001, 1499, 1500, 1501,
                           2499, 2500, 2501, 4999, 5000, 5001,
                           29999, 30000, 30001, 39999, 40000, 40001])

        for co2 in test_values:
            hazards = self.analyzer._check_air_quality(co2)
            self.assertLessEqual(len(hazards), 1,
                                 f"CO2 {co2} ppm produced {len(hazards)} hazards: "
                                 f"{[h['type'] for h in hazards]}")


class TestAlertAnalyzerStructural(unittest.TestCase):
    """Structural tests validating alert objects and return types."""

    def setUp(self):
        self.analyzer = AlertAnalyzer()

    def test_alert_object_has_required_fields(self):
        """Every generated alert contains severity, title, body, emoji, category."""
        # Use data that triggers multiple alert types
        test_scenarios = [
            make_sensor_data(temp=-15.0),                          # severe cold
            make_sensor_data(temp=36.0),                           # heat stroke
            make_sensor_data(pressure=840.0),                      # severe weather
            make_sensor_data(is_raining=True),                     # rain
            make_sensor_data(uv=12.0),                             # extreme UV
            make_sensor_data(co2=50000),                           # CO2 IDLH
            make_sensor_data(lux=5, humidity=95.0),                # poor visibility
            make_sensor_data(moisture=90.0),                       # saturated soil
            make_sensor_data(temp=2.0, rain_last_hour=True),       # slippery
        ]

        required_fields = {'severity', 'title', 'body', 'emoji', 'category'}

        for data in test_scenarios:
            alerts = self.analyzer.analyze(data, station_name="Test")
            for alert in alerts:
                for field in required_fields:
                    self.assertTrue(
                        hasattr(alert, field) and getattr(alert, field) is not None,
                        f"Alert missing or None field '{field}': {alert}"
                    )
                # Verify severity is one of the expected values
                self.assertIn(alert.severity, ('danger', 'warning', 'info'),
                              f"Unexpected severity: {alert.severity}")

    def test_analyze_returns_empty_list_not_none(self):
        """Safe conditions return an empty list rather than None."""
        # Perfectly safe conditions: mild temp, normal pressure, no rain, no UV
        safe_data = make_sensor_data(temp=18.0, humidity=50.0, pressure=870.0)
        result = self.analyzer.analyze(safe_data, station_name="Test")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
