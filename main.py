"""Smart Fitness Session Analyzer - Main Entry Point."""

import argparse
import csv
import sys
from pathlib import Path

from analyzer import SessionAnalyzer
from modules import FitnessSession, ParticipantProfile, SensorObservation
from error_exception import InvalidIdentifierError, InvalidRecordError


def load_profiles(file_path: Path) -> dict:
    """Loads participant baseline profiles from a CSV file."""
    participants = {}

    try:
        with open(file_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                try:
                    p_id = row["participant_id"]
                    p = ParticipantProfile(
                        participant_id=p_id,
                        baseline_heart_rate=float(row["baseline_heart_rate"]),
                        baseline_skin_response=float(row["baseline_skin_response"]),
                        baseline_temperature=float(row["baseline_temperature"]),
                    )
                    participants[p_id] = p
                except (ValueError, KeyError, InvalidIdentifierError) as e:
                    print(f"Warning: Ignoring invalid profile on row {idx}: {e}")
    except FileNotFoundError:
        print(f"Error: Profile file not found at {file_path}")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied for {file_path}")
        sys.exit(1)

    return participants


def process_sessions(session_files: list, participants: dict) -> tuple:
    """Reads session CSV files, casts string inputs, groups records, and logs rejected rows."""
    sessions = {}
    session_row_counts = {}
    rejected_records = []
    accepted_count = 0

    for file_path in session_files:
        try:
            with open(file_path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                expected_fields = len(reader.fieldnames) if reader.fieldnames else 0

                for row_num, row in enumerate(reader, start=2):
                    if len(row) != expected_fields:
                        rejected_records.append((file_path.name, row_num, "Row Format", "Unexpected row length"))
                        continue

                    session_id = row.get("session_id")
                    p_id = row.get("participant_id")

                    try:
                        if not session_id or not p_id:
                            raise InvalidRecordError("Missing session or participant identifiers.")

                        if p_id not in participants:
                            raise InvalidRecordError(f"Participant ID '{p_id}' not found in profiles.")

                        session_row_counts[session_id] = session_row_counts.get(session_id, 0) + 1

                        # Type casting raw strings from CSV DictReader into floats/ints
                        obs = SensorObservation(
                            timestamp=int(row["timestamp"]),
                            heart_rate=float(row["heart_rate"]) if row.get("heart_rate") else None,
                            skin_response=float(row["skin_response"]) if row.get("skin_response") else None,
                            temperature=float(row["temperature"]) if row.get("temperature") else None,
                            activity_level=float(row["activity_level"]) if row.get("activity_level") else None,
                            signal_quality=float(row["signal_quality"]) if row.get("signal_quality") else None,
                        )

                        is_valid, errs = obs.validate()
                        if not is_valid:
                            raise InvalidRecordError(f"Measurement validation failed: {', '.join(errs)}")

                        if session_id not in sessions:
                            sessions[session_id] = FitnessSession(session_id, participants[p_id])

                        sessions[session_id].add_observation(obs)
                        accepted_count += 1

                    except KeyError as e:
                        rejected_records.append((file_path.name, row_num, "Missing Field", f"Missing column: {e}"))
                    except (ValueError, TypeError) as e:
                        rejected_records.append((file_path.name, row_num, "Type Conversion", f"Failed conversion: {e}"))
                    except (InvalidIdentifierError, InvalidRecordError) as e:
                        rejected_records.append((file_path.name, row_num, "Validation", str(e)))

        except (FileNotFoundError, PermissionError) as e:
            print(f"Error accessing session file {file_path}: {e}")

    return sessions, session_row_counts, rejected_records, accepted_count


def generate_reports(sessions: dict, session_row_counts: dict, rejected_records: list, out_dir: Path):
    """Outputs analysis_summary.csv, analysis_report.txt, and rejected_records.txt."""
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "analysis_summary.csv"
    report_path = out_dir / "analysis_report.txt"
    rejected_path = out_dir / "rejected_records.txt"

    with open(summary_path, mode="w", encoding="utf-8", newline="") as sf, open(
        report_path, mode="w", encoding="utf-8"
    ) as rf:

        writer = csv.DictWriter(
            sf, fieldnames=["session_id", "participant_id", "classification", "usable_windows", "total_windows"]
        )
        writer.writeheader()

        rf.write("FITNESS SESSION ANALYSIS REPORT\n")
        rf.write("=" * 50 + "\n\n")

        for s_id, session in sessions.items():
            analyzer = SessionAnalyzer(session)
            result = analyzer.evaluate_session(session_row_counts.get(s_id, 0))

            writer.writerow({
                "session_id": result["session_id"],
                "participant_id": result["participant_id"],
                "classification": result["classification"],
                "usable_windows": result["data_quality"]["usable_observations"],
                "total_windows": result["data_quality"]["total_observations"],
            })

            rf.write(f"Session ID  : {result['session_id']}\n")
            rf.write(f"Participant : {result['participant_id']}\n")
            rf.write(f"Result      : {result['classification'].upper()}\n")
            rf.write(f"Explanation : {result['explanation']}\n")
            rf.write("-" * 50 + "\n")

    with open(rejected_path, mode="w", encoding="utf-8") as rj:
        rj.write("REJECTED RECORDS LOG\n")
        rj.write("=" * 60 + "\n")
        for rec in rejected_records:
            rj.write(f"File: {rec[0]:<25} | Row: {rec[1]:<4} | Field: {rec[2]:<15} | Reason: {rec[3]}\n")

    return len(sessions), len(rejected_records)


def main():
    parser = argparse.ArgumentParser(description="Smart Fitness Session Analyzer")
    parser.add_argument("--profiles", required=True, type=Path, help="Participant profiles CSV")
    parser.add_argument("--sessions", required=True, nargs="+", type=Path, help="Session observation CSV files")
    parser.add_argument("--output", required=True, type=Path, help="Output folder directory")

    args = parser.parse_args()

    participants = load_profiles(args.profiles)
    sessions, session_row_counts, rejected_records, accepted_count = process_sessions(
        args.sessions, participants
    )

    processed_sessions, rejected_count = generate_reports(
        sessions, session_row_counts, rejected_records, args.output
    )

    print("\n--- Execution Summary ---")
    print(f"Accepted Observations : {accepted_count}")
    print(f"Rejected Rows         : {rejected_count}")
    print(f"Sessions Processed    : {processed_sessions}")
    print(f"Report Directory      : {args.output.resolve()}")


if __name__ == "__main__":
    main()