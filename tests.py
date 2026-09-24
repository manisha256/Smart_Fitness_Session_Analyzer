"""Unit tests for Fitness Session Analyzer standard library modules."""

import unittest
from main import (
    ParticipantProfile,
    SensorObservation,
    FitnessSession,
    validate_measurement,
    calculate_summary_stats,
    compute_percentage_change,
)


class TestFitnessAnalyzer(unittest.TestCase):

    def test_validate_measurement(self):
        self.assertTrue(validate_measurement(100, 35, 205))
        self.assertFalse(validate_measurement(None, 35, 205))
        self.assertFalse(validate_measurement(265, 35, 205))
        self.assertFalse(validate_measurement(-10, 0, 1))

    def test_summary_stats(self):
        data = [10.0, 20.0, 30.0]
        stats = calculate_summary_stats(data)
        self.assertEqual(stats["avg"], 20.0)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 30.0)

    # FIX: Added 'def' keyword here
    def test_empty_stats(self):
        stats = calculate_summary_stats([])
        self.assertIsNone(stats["avg"])

    def test_percentage_change(self):
        self.assertEqual(compute_percentage_change(60.0, 90.0), 50.0)
        self.assertEqual(compute_percentage_change(100.0, 80.0), -20.0)

    def test_observation_validation(self):
        valid_obs = SensorObservation(0, 70, 1.5, 32.0, 0.2, 0.95)
        self.assertTrue(valid_obs.validate()[0])

        invalid_obs = SensorObservation(1, None, 1.5, 32.0, -0.5, 0.40)
        is_valid, errors = invalid_obs.validate()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_recovery_detection_static_method(self):
        declining_hr = [140, 130, 110, 90, 75, 70]
        steady_hr = [120, 122, 119, 121, 120, 118]
        self.assertTrue(FitnessSession.is_recovering_trend(declining_hr))
        self.assertFalse(FitnessSession.is_recovering_trend(steady_hr))


if __name__ == "__main__":
    unittest.main()