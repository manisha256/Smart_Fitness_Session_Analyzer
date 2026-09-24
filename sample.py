"""Scenario Runner for Smart Fitness Session Analyzer.

Executes all 5 mandated assignment test scenarios and outputs console reports.
"""

from main import run_session_analysis

SCENARIOS = [
    ("resting", 42),
    ("moderate_activity", 42),
    ("high_activity", 42),
    ("recovery", 42),
    ("poor_quality", 42),
]

def main():
    print("\n==================================================")
    print("  RUNNING ALL 5 REQUIRED ASSIGNMENT SCENARIOS  ")
    print("==================================================")
    for scenario, seed in SCENARIOS:
        print(f"\n>>> Executing Scenario: [{scenario.upper()}] <<<")
        run_session_analysis(scenario_name=scenario, seed=seed)

if __name__ == "__main__":
    main()