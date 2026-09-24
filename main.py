"""Smart Fitness Session Analyzer.

This module processes wearable fitness tracker data, validates sensor measurements,
calculates statistical summaries, compares readings to personal baselines,
detects recovery trends, and classifies overall session intensity.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math
import statistics

from data_generator import generate_fitness_data


# ============================================================================
# STANDALONE UTILITY FUNCTIONS
# ============================================================================

def validate_measurement(
    value: Optional[float], min_val: float, max_val: float
) -> bool:
    """Validate whether a sensor measurement is non-null and within expected limits."""
    if value is None:
        return False
    return min_val <= value <= max_val


def calculate_summary_stats(values: List[float]) -> Dict[str, Optional[float]]:
    """Calculate average, minimum, and maximum for a numeric series."""
    if not values:
        return {"avg": None, "min": None, "max": None}
    return {
        "avg": round(statistics.mean(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
    }


def compute_percentage_change(baseline: float, current: float) -> float:
    """Calculate the relative percentage difference from baseline."""
    if baseline == 0:
        return 0.0
    return round(((current - baseline) / baseline) * 100, 2)


def format_report_header(title: str, width: int = 60) -> str:
    """Format a decorative ASCII header for console reporting."""
    border = "=" * width
    return f"\n{border}\n{title.center(width)}\n{border}"


# ============================================================================
# DOMAIN CLASSES
# ============================================================================

class ParticipantProfile:
    """Encapsulates personal baseline physical characteristics."""

    def __init__(
        self,
        participant_id: str,
        baseline_heart_rate: float,
        baseline_skin_response: float,
        baseline_temperature: float,
    ):
        self.participant_id = participant_id
        self._baseline_heart_rate = baseline_heart_rate
        self._baseline_skin_response = baseline_skin_response
        self._baseline_temperature = baseline_temperature

    @property
    def baseline_heart_rate(self) -> float:
        return self._baseline_heart_rate

    @property
    def baseline_skin_response(self) -> float:
        return self._baseline_skin_response

    @property
    def baseline_temperature(self) -> float:
        return self._baseline_temperature

    @classmethod
    def from_dict(cls, profile_dict: Dict) -> "ParticipantProfile":
        """Factory method to instantiate profile from generator dictionary."""
        return cls(
            participant_id=profile_dict["participant_id"],
            baseline_heart_rate=profile_dict["baseline_heart_rate"],
            baseline_skin_response=profile_dict["baseline_skin_response"],
            baseline_temperature=profile_dict["baseline_temperature"],
        )

    def to_dict(self) -> Dict:
        """Export profile attributes as a standard dictionary."""
        return {
            "participant_id": self.participant_id,
            "baseline_heart_rate": self._baseline_heart_rate,
            "baseline_skin_response": self._baseline_skin_response,
            "baseline_temperature": self._baseline_temperature,
        }


class BaseObservation:
    """Base class for sensor observation windows."""

    def __init__(self, timestamp: int, signal_quality: Optional[float]):
        self.timestamp = timestamp
        self.signal_quality = signal_quality

    def is_signal_reliable(self, threshold: float = 0.55) -> bool:
        """Check if overall signal quality meets operational standard."""
        return self.signal_quality is not None and self.signal_quality >= threshold


class SensorObservation(BaseObservation):
    """Specific observation containing wearable physiological readings."""

    HR_BOUNDS = (35.0, 205.0)
    SKIN_BOUNDS = (0.0, 10.0)
    TEMP_BOUNDS = (25.0, 42.0)
    ACTIVITY_BOUNDS = (0.0, 1.0)

    def __init__(
        self,
        timestamp: int,
        heart_rate: Optional[float],
        skin_response: Optional[float],
        temperature: Optional[float],
        activity_level: Optional[float],
        signal_quality: Optional[float],
    ):
        super().__init__(timestamp, signal_quality)
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level

    @classmethod
    def from_dict(cls, data: Dict) -> "SensorObservation":
        """Factory method creating an observation from raw dictionary input."""
        return cls(
            timestamp=data.get("timestamp", 0),
            heart_rate=data.get("heart_rate"),
            skin_response=data.get("skin_response"),
            temperature=data.get("temperature"),
            activity_level=data.get("activity_level"),
            signal_quality=data.get("signal_quality"),
        )

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate observation readings against biological and hardware bounds."""
        errors = []
        if not self.is_signal_reliable():
            errors.append(f"Low signal quality: {self.signal_quality}")

        if not validate_measurement(self.heart_rate, *self.HR_BOUNDS):
            errors.append(f"Invalid heart rate: {self.heart_rate}")

        if not validate_measurement(self.skin_response, *self.SKIN_BOUNDS):
            errors.append(f"Invalid skin response: {self.skin_response}")

        if not validate_measurement(self.temperature, *self.TEMP_BOUNDS):
            errors.append(f"Invalid temperature: {self.temperature}")

        if not validate_measurement(self.activity_level, *self.ACTIVITY_BOUNDS):
            errors.append(f"Invalid activity level: {self.activity_level}")

        return (len(errors) == 0, errors)


class FitnessSession:
    """Manages session observations and performs statistical and classification analysis.

    Demonstrates COMPOSITION by storing multiple SensorObservation instances.
    """

    def __init__(self, participant: ParticipantProfile):
        self.participant = participant
        self.raw_observations: List[SensorObservation] = []
        self.valid_observations: List[SensorObservation] = []
        self.invalid_observations: List[Tuple[SensorObservation, List[str]]] = []

    def add_observation(self, obs: SensorObservation) -> None:
        """Process and route individual observation window."""
        self.raw_observations.append(obs)
        is_valid, errors = obs.validate()
        if is_valid:
            self.valid_observations.append(obs)
        else:
            self.invalid_observations.append((obs, errors))

    @staticmethod
    def is_recovering_trend(
        values: List[float], min_decline_ratio: float = 0.15
    ) -> bool:
        """Static helper analyzing whether a numeric sequence exhibits a declining trend."""
        if len(values) < 4:
            return False
        midpoint = len(values) // 2
        first_half_avg = statistics.mean(values[:midpoint])
        second_half_avg = statistics.mean(values[midpoint:])

        if first_half_avg == 0:
            return False

        decline = (first_half_avg - second_half_avg) / first_half_avg
        return decline >= min_decline_ratio

    def evaluate_session(self) -> Dict:
        """Perform comprehensive data analysis and return structured results dictionary."""
        total = len(self.raw_observations)
        usable = len(self.valid_observations)

        # Handle edge case: Insufficient data (<50% valid records or <4 total valid)
        if total == 0 or (usable / total) < 0.50 or usable < 4:
            return {
                "participant_id": self.participant.participant_id,
                "total_windows": total,
                "usable_windows": usable,
                "classification": "insufficient data",
                "explanation": (
                    f"Only {usable}/{total} observations were valid. Minimum 50% "
                    "valid data required for classification."
                ),
                "summaries": {},
                "baseline_comparisons": {},
            }

        # Collect metrics across valid windows
        hrs = [o.heart_rate for o in self.valid_observations]
        skins = [o.skin_response for o in self.valid_observations]
        temps = [o.temperature for o in self.valid_observations]
        acts = [o.activity_level for o in self.valid_observations]

        hr_stats = calculate_summary_stats(hrs)
        skin_stats = calculate_summary_stats(skins)
        temp_stats = calculate_summary_stats(temps)
        act_stats = calculate_summary_stats(acts)

        # Baseline comparative metrics
        hr_diff = round(hr_stats["avg"] - self.participant.baseline_heart_rate, 2)
        hr_pct = compute_percentage_change(
            self.participant.baseline_heart_rate, hr_stats["avg"]
        )

        # Detect recovery indicators
        is_hr_recovering = self.is_recovering_trend(hrs)
        is_act_recovering = self.is_recovering_trend(acts)
        has_recovery = is_hr_recovering and is_act_recovering

        # Classification rules
        if has_recovery and (hrs[0] - hrs[-1]) > 15:
            classification = "recovering"
            explanation = "Heart rate and activity levels showed systematic decline toward baseline near end of session."
        elif act_stats["avg"] >= 0.65 or hr_stats["avg"] >= (
            self.participant.baseline_heart_rate + 45
        ):
            classification = "high activity"
            explanation = "High mean activity levels and substantial heart rate elevation above baseline."
        elif act_stats["avg"] >= 0.30 or hr_stats["avg"] >= (
            self.participant.baseline_heart_rate + 15
        ):
            classification = "moderate activity"
            explanation = "Moderate heart rate elevation and steady physical movement detected."
        else:
            classification = "resting"
            explanation = "Heart rate remained close to resting baseline with minimal physical movement."

        return {
            "participant_id": self.participant.participant_id,
            "total_windows": total,
            "usable_windows": usable,
            "classification": classification,
            "explanation": explanation,
            "summaries": {
                "heart_rate": hr_stats,
                "skin_response": skin_stats,
                "temperature": temp_stats,
                "activity_level": act_stats,
            },
            "baseline_comparisons": {
                "baseline_hr": self.participant.baseline_heart_rate,
                "avg_hr": hr_stats["avg"],
                "hr_difference": hr_diff,
                "hr_percentage_change": hr_pct,
            },
        }

    def print_console_report(self) -> None:
        """Print a clean summary report."""
        res = self.evaluate_session()
        print(format_report_header(f"FITNESS SESSION ANALYSIS REPORT: {res['participant_id']}"))
        print(f"Usable Data Windows : {res['usable_windows']} / {res['total_windows']}")
        print(f"Session Classification: {res['classification'].upper()}")
        print(f"Classification Basis  : {res['explanation']}")

        if res["classification"] != "insufficient data":
            bc = res["baseline_comparisons"]
            print("\n--- BASELINE COMPARISON ---")
            print(f"Resting HR Baseline   : {bc['baseline_hr']} bpm")
            print(f"Session Average HR    : {bc['avg_hr']} bpm ({bc['hr_difference']:+} bpm / {bc['hr_percentage_change']:+}% )")

            print("\n--- SENSOR SUMMARIES ---")
            for metric, stats in res["summaries"].items():
                m_name = metric.replace("_", " ").title()
                print(f"{m_name:<18}: Avg = {stats['avg']}, Min = {stats['min']}, Max = {stats['max']}")

        if self.invalid_observations:
            print(f"\n--- FLAGGED/REJECTED OBSERVATIONS ({len(self.invalid_observations)}) ---")
            for obs, errs in self.invalid_observations:
                print(f"Window {obs.timestamp:02d} | Issues: {', '.join(errs)}")
        print("=" * 60)


# ============================================================================
# MAIN APPLICATION EXECUTION
# ============================================================================

def run_session_analysis(scenario_name: str = "moderate_activity", seed: int = 42):
    """Load data, build objects, analyze, and print."""
    profile_dict, obs_dicts = generate_fitness_data(
        participant_id="P001",
        scenario=scenario_name,
        seed=seed,
        number_of_windows=12,
    )

    participant = ParticipantProfile.from_dict(profile_dict)
    session = FitnessSession(participant)

    for o_dict in obs_dicts:
        obs = SensorObservation.from_dict(o_dict)
        session.add_observation(obs)

    session.print_console_report()
    return session.evaluate_session()


if __name__ == "__main__":
    run_session_analysis("moderate_activity", seed=42)