"""Analysis engine for calculating statistics and classifying fitness sessions."""

import statistics
from typing import Dict, List, Optional


def calculate_summary_stats(values: List[float]) -> Dict[str, Optional[float]]:
    """Calculate average, minimum, maximum, and standard deviation for a numeric series."""
    if not values:
        return {"avg": None, "min": None, "max": None, "std_dev": None}
    mean_val = statistics.mean(values)
    std_val = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "avg": round(mean_val, 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "std_dev": round(std_val, 2),
    }


def compute_percentage_change(baseline: float, current: float) -> float:
    """Calculate the relative percentage difference from baseline."""
    if baseline == 0:
        return 0.0
    return round(((current - baseline) / baseline) * 100, 2)


class SessionAnalyzer:
    """Performs statistical analysis, recovery evaluation, and classification on a session."""

    def __init__(self, session):
        self.session = session

    @staticmethod
    def is_recovering_trend(values: List[float], min_decline_ratio: float = 0.15) -> bool:
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

    def evaluate_session(self, total_rows_attempted: Optional[int] = None) -> Dict:
        """Perform comprehensive data analysis and return structured results dictionary."""
        total = total_rows_attempted if total_rows_attempted is not None else len(self.session.raw_observations)
        valid_obs = self.session.get_valid_observations()
        usable = len(valid_obs)
        usable_pct = round((usable / total * 100), 1) if total > 0 else 0.0

        data_quality = {
            "total_observations": total,
            "usable_observations": usable,
            "rejected_observations": total - usable,
            "usable_percentage": usable_pct,
        }

        # Insufficient data rule (<50% valid records or <4 total valid)
        if total == 0 or (usable / total) < 0.50 or usable < 4:
            return {
                "session_id": self.session.session_id,
                "participant_id": self.session.participant.participant_id,
                "total_windows": total,
                "usable_windows": usable,
                "classification": "insufficient data",
                "explanation": (
                    f"Only {usable}/{total} observations were valid ({usable_pct}%). "
                    "Minimum 50% valid data required for classification."
                ),
                "data_quality": data_quality,
                "summaries": {},
                "baseline_comparisons": {},
            }

        # Collect metrics across valid windows
        hrs = [o.heart_rate for o in valid_obs]
        skins = [o.skin_response for o in valid_obs]
        temps = [o.temperature for o in valid_obs]
        acts = [o.activity_level for o in valid_obs]

        hr_stats = calculate_summary_stats(hrs)
        skin_stats = calculate_summary_stats(skins)
        temp_stats = calculate_summary_stats(temps)
        act_stats = calculate_summary_stats(acts)

        p = self.session.participant

        # Baseline comparative metrics using ParticipantProfile properties
        hr_diff = round(hr_stats["avg"] - p.baseline_heart_rate, 2)
        hr_pct = compute_percentage_change(p.baseline_heart_rate, hr_stats["avg"])

        # Detect recovery indicators
        is_hr_recovering = self.is_recovering_trend(hrs)
        is_act_recovering = self.is_recovering_trend(acts)
        has_recovery = is_hr_recovering and is_act_recovering

        # Classification rules
        if has_recovery and (hrs[0] - hrs[-1]) > 15:
            classification = "recovering"
            explanation = "Heart rate and activity levels showed systematic decline toward baseline near end of session."
        elif act_stats["avg"] >= 0.65 or hr_stats["avg"] >= (p.baseline_heart_rate + 45):
            classification = "high activity"
            explanation = "High mean activity levels and substantial heart rate elevation above baseline."
        elif act_stats["avg"] >= 0.30 or hr_stats["avg"] >= (p.baseline_heart_rate + 15):
            classification = "moderate activity"
            explanation = "Moderate heart rate elevation and steady physical movement detected."
        else:
            classification = "resting"
            explanation = "Heart rate remained close to resting baseline with minimal physical movement."

        return {
            "session_id": self.session.session_id,
            "participant_id": p.participant_id,
            "total_windows": total,
            "usable_windows": usable,
            "classification": classification,
            "explanation": explanation,
            "data_quality": data_quality,
            "summaries": {
                "heart_rate": hr_stats,
                "skin_response": skin_stats,
                "temperature": temp_stats,
                "activity_level": act_stats,
            },
            "baseline_comparisons": {
                "baseline_hr": p.baseline_heart_rate,
                "avg_hr": hr_stats["avg"],
                "hr_difference": hr_diff,
                "hr_percentage_change": hr_pct,
            },
        }