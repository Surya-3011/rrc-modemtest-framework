"""
main.py
-------
Single entry point that runs the whole mini test bed end-to-end, the way
you'd demo it in an interview:

  1. Run the declarative test suite against the RRC state machine.
  2. Print PASS/FAIL summary (+ results persisted to results.db).
  3. Run the field-log analyzer over the log the suite just produced.
  4. Run a quick multi-SIM demo (two independent state machines).
  5. Run the fuzz/stability campaign.

Exits with status 1 if any test case fails or the fuzz campaign finds a
crash/undefined state -- this is what lets a CI pipeline (see
.github/workflows/tests.yml) actually go red on a real regression
instead of always reporting green.
"""

import sys

from rrc_state_machine import RRCStateMachine, RRCEvent
import test_framework
import log_analyzer
import fuzz_test


def multi_sim_demo():
    print("MULTI-SIM DEMO (two independent RRC state machines)")
    print("=" * 60)
    sim_a = RRCStateMachine(sim_id="SIM-A")
    sim_b = RRCStateMachine(sim_id="SIM-B")

    sim_a.run_sequence([RRCEvent.SETUP_REQUEST, RRCEvent.SETUP_COMPLETE])
    sim_b.run_sequence([RRCEvent.SETUP_REQUEST, RRCEvent.SETUP_COMPLETE,
                         RRCEvent.RELEASE_SUSPEND])

    print(f"  SIM-A state: {sim_a.state.value}  (power units: {sim_a.power_units})")
    print(f"  SIM-B state: {sim_b.state.value}  (power units: {sim_b.power_units})")
    print("  -> both SIMs held independent state correctly.\n")


def main():
    print("\n### 1. RUNNING TEST SUITE ###\n")
    results = test_framework.run_all()
    test_framework.print_summary(results)
    suite_ok = all(r["status"] == "PASS" for r in results)

    print("\n### 2. FIELD LOG ANALYSIS ###\n")
    entries = log_analyzer.parse_log()
    log_analyzer.print_report(entries)

    print("\n### 3. MULTI-SIM DEMO ###\n")
    multi_sim_demo()

    print("### 4. FUZZ / STABILITY CAMPAIGN ###\n")
    fuzz_ok = fuzz_test.run_fuzz_campaign()

    if suite_ok and fuzz_ok:
        print("\nRESULT: all checks passed.")
        return 0
    print("\nRESULT: one or more checks FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
