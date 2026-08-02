"""
test_framework.py
------------------
Minimal automation framework around the RRC state machine.

What it does (mirrors the JD's "Automation framework development",
"test strategies and test plans", "field log analysis" bullets):

1. Loads declarative test cases from test_cases.json (so new test cases
   can be added without touching framework code -- a real test bed
   design principle).
2. Executes each test case against a fresh RRCStateMachine instance.
3. Writes a human-readable, timestamped log for every message exchanged
   (this is the stand-in for a "field log" a real modem would produce).
4. Compares actual vs expected outcome -> PASS/FAIL verdict.
5. Persists a structured result per test into SQLite (results.db) so
   results can be queried/trended across runs, like a real test
   dashboard would.
"""

import json
import sqlite3
import time
from datetime import datetime

from rrc_state_machine import RRCStateMachine, RRCEvent

LOG_PATH = "field_log.txt"
DB_PATH = "results.db"


def load_test_cases(path="test_cases.json"):
    with open(path) as f:
        return json.load(f)


def init_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            run_ts TEXT,
            test_name TEXT,
            sim_id TEXT,
            expected_state TEXT,
            actual_state TEXT,
            status TEXT,
            rejected_events INTEGER,
            power_units INTEGER
        )
    """)
    conn.commit()
    return conn


def run_test_case(tc, log_file):
    sm = RRCStateMachine(sim_id=tc["sim_id"])
    for event_name in tc["events"]:
        event = RRCEvent[event_name]
        status = sm.handle_event(event)

    rejected_events = sum(1 for h in sm.history if h[5] == "REJECTED")

    # write every transition to the field log
    for ts, sim_id, event_name, from_state, to_state, status in sm.history:
        line = (f"[{datetime.fromtimestamp(ts).isoformat()}] "
                f"{sim_id} | {tc['name']} | {event_name} | "
                f"{from_state} -> {to_state} | {status}")
        log_file.write(line + "\n")

    expected_state = tc["expected_final_state"]
    actual_state = sm.state.value

    # A test passes if the final state matches expectations. For explicit
    # fault-injection cases we additionally require at least one REJECTED
    # event, otherwise the "fault" was silently accepted -- a real bug.
    passed = actual_state == expected_state
    if tc.get("expect_rejection"):
        passed = passed and rejected_events > 0

    return {
        "test_name": tc["name"],
        "sim_id": tc["sim_id"],
        "expected_state": expected_state,
        "actual_state": actual_state,
        "status": "PASS" if passed else "FAIL",
        "rejected_events": rejected_events,
        "power_units": sm.power_units,
    }


def run_all(test_cases_path="test_cases.json"):
    test_cases = load_test_cases(test_cases_path)
    conn = init_db()
    run_ts = datetime.now().isoformat()

    results = []
    with open(LOG_PATH, "w") as log_file:
        for tc in test_cases:
            result = run_test_case(tc, log_file)
            results.append(result)
            conn.execute(
                "INSERT INTO results VALUES (?,?,?,?,?,?,?,?)",
                (run_ts, result["test_name"], result["sim_id"],
                 result["expected_state"], result["actual_state"],
                 result["status"], result["rejected_events"],
                 result["power_units"])
            )
    conn.commit()
    conn.close()
    return results


def print_summary(results):
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    print(f"{'TEST NAME':<40}{'SIM':<8}{'EXPECTED':<16}{'ACTUAL':<16}{'STATUS':<8}")
    print("-" * 88)
    for r in results:
        print(f"{r['test_name']:<40}{r['sim_id']:<8}{r['expected_state']:<16}"
              f"{r['actual_state']:<16}{r['status']:<8}")
    print("-" * 88)
    print(f"TOTAL: {len(results)}  PASS: {passed}  FAIL: {failed}\n")


if __name__ == "__main__":
    results = run_all()
    print_summary(results)
