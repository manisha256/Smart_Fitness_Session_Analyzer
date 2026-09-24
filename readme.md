Name - Manisha Amit Chougule
Student Number - 416276

# Option A: Smart Fitness Session Analyzer

## Application Overview
This application processes physiological sensor data gathered from wearable activity trackers during training sessions. It validates incoming raw data streams, flags impossible or corrupted readings, calculates statistical summaries, compares metrics against individual participant baseline values, evaluates recovery trends, and outputs structured session reports.

## Architecture & Object-Oriented Design

### Class Responsibilities
1. `ParticipantProfile`: Represents baseline reference values (resting heart rate, skin response, body temperature) for a specific user.
2. `BaseObservation`: Abstracted base class managing timestamp and hardware signal reliability indicators.
3. `SensorObservation` (Inherits from `BaseObservation`): Holds physiological measurements and performs threshold-based domain validation.
4. `FitnessSession`: Primary orchestrator class that manages individual observations, computes comparative metrics, runs recovery algorithms, and executes session classification logic.

### OOP Concepts Demonstrated
* **Composition**: `FitnessSession` contains and manages collections of `SensorObservation` objects.
* **Encapsulation**: Baseline properties in `ParticipantProfile` (`_baseline_heart_rate`, etc.) are protected attributes accessible via read-only `@property` methods.
* **Inheritance & Method Overriding**: `SensorObservation` inherits from `BaseObservation` and overrides/extends validation capabilities.
* **Class & Static Methods**:
  * `ParticipantProfile.from_dict()` & `SensorObservation.from_dict()` (`@classmethod` factory constructors).
  * `FitnessSession.is_recovering_trend()` (`@staticmethod` utility for trend analysis).
* **Standalone Utility Functions**:
  * `validate_measurement()`
  * `calculate_summary_stats()`
  * `compute_percentage_change()`
  * `format_report_header()`

## Classification Logic & Assumptions
* **`insufficient data`**: Assigned when < 50% of observation windows in a session pass validation or when fewer than 4 total valid windows exist.
* **`recovering`**: Triggered when both heart rate and activity exhibit a declining trend (>= 15% drop across session halves) and net heart rate drop exceeds 15 bpm.
* **`high activity`**: Assigned if mean activity >= 0.65 or mean heart rate is >= 45 bpm over resting baseline.
* **`moderate activity`**: Assigned if mean activity >= 0.30 or mean heart rate is >= 15 bpm over resting baseline.
* **`resting`**: Default state when physical activity and heart rate remain near baseline.

## Execution Instructions

Clone repository and execute scripts using standard Python 3:

```bash
# Run main entry point
python3 main.py

# Run all 5 required test scenarios
python3 sample_data.py

# Run unit tests
python3 tests.py