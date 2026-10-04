"""Core domain classes for the Smart Fitness Session Analyzer."""

import re
from typing import Dict, List, Optional, Tuple
from error_exception import InvalidIdentifierError


def validate_measurement(value: Optional[float], min_val: float, max_val: float) -> bool:
    """Validate whether a sensor measurement is non-null and within expected limits."""
    if value is None:
        return False
    return min_val <= value <= max_val


class ParticipantProfile:
    """Encapsulates personal baseline physical characteristics."""

    def __init__(
        self,
        participant_id: str,
        baseline_heart_rate: float,
        baseline_skin_response: float,
        baseline_temperature: float,
    ):
        # Regex validation: 'P' followed by exactly 3 digits (e.g., P001)
        if not re.match(r"^P\d{3}$", participant_id):
            raise InvalidIdentifierError(
                f"Invalid Participant ID format: '{participant_id}' (Expected PXXX)"
            )

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
            baseline_heart_rate=float(profile_dict["baseline_heart_rate"]),
            baseline_skin_response=float(profile_dict["baseline_skin_response"]),
            baseline_temperature=float(profile_dict["baseline_temperature"]),
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
        """Factory method creating an observation from dictionary input."""
        return cls(
            timestamp=int(data.get("timestamp", 0)),
            heart_rate=float(data["heart_rate"]) if data.get("heart_rate") is not None else None,
            skin_response=float(data["skin_response"]) if data.get("skin_response") is not None else None,
            temperature=float(data["temperature"]) if data.get("temperature") is not None else None,
            activity_level=float(data["activity_level"]) if data.get("activity_level") is not None else None,
            signal_quality=float(data["signal_quality"]) if data.get("signal_quality") is not None else None,
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

    def is_valid(self) -> bool:
        """Helper returning True if observation passes validation."""
        valid, _ = self.validate()
        return valid


class FitnessSession:
    """Manages session observations and composes ParticipantProfile and SensorObservation objects."""

    def __init__(self, session_id: str, participant: ParticipantProfile):
        # Regex validation: 'FIT-YYYY-NNN' format (e.g., FIT-2024-001)
        if not re.match(r"^FIT-\d{4}-\d{3}$", session_id):
            raise InvalidIdentifierError(
                f"Invalid Session ID format: '{session_id}' (Expected FIT-YYYY-NNN)"
            )

        self.session_id = session_id
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

    def get_valid_observations(self) -> List[SensorObservation]:
        return self.valid_observations

    def get_invalid_observations(self) -> List[Tuple[SensorObservation, List[str]]]:
        return self.invalid_observations