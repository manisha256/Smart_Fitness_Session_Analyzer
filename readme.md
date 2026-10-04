# Smart Fitness Session Analyzer (Assignment 2)

## Application Overview
The **Smart Fitness Session Analyzer** processes physiological sensor data collected from wearable fitness trackers. The system reads raw session CSV logs and participant profiles, parses and validates sensor readings against biological and hardware limits, calculates summary statistics, evaluates recovery trends against baseline metrics, and generates comprehensive reports.

---

## Repository Structure

```text

├── exceptions.py      # Custom exception definitions (InvalidIdentifierError, InvalidRecordError)
├── core_modules.py    # Domain models (ParticipantProfile, BaseObservation, SensorObservation, FitnessSession)
├── analyzer.py        # Statistical calculations, trend analysis, and session classification logic
├── main.py            # CLI parser, CSV file loader, exception handler, and report writer
└── README.md          # Project documentation and execution instructions

```


---

## Command

 python3 main.py --profiles data/participants.csv --sessions data/fitness_sessions.csv data/fitness_sessions_invalid.csv --output output
