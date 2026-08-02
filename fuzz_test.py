"""
fuzz_test.py
------------
Lightweight stability/stress test: fires random (including invalid)
event sequences at the state machine and checks it never crashes and
never ends up in an undefined state. This is the "improving the
stability of the product" bullet in miniature -- real modem test teams
run large-scale randomized/fuzz campaigns for exactly this reason.
"""

import random
from rrc_state_machine import RRCStateMachine, RRCEvent, RRCState

N_RUNS = 500
MAX_EVENTS_PER_RUN = 12


def random_run():
    sm = RRCStateMachine(sim_id="FUZZ-UE")
    n_events = random.randint(1, MAX_EVENTS_PER_RUN)
    for _ in range(n_events):
        event = random.choice(list(RRCEvent))
        sm.handle_event(event)
    return sm


def run_fuzz_campaign():
    crashes = 0
    invalid_final_states = 0

    for _ in range(N_RUNS):
        try:
            sm = random_run()
            if sm.state not in RRCState:
                invalid_final_states += 1
        except Exception as exc:
            crashes += 1
            print(f"CRASH on random sequence: {exc}")

    ok = crashes == 0 and invalid_final_states == 0
    print(f"Fuzz campaign complete: {N_RUNS} runs")
    print(f"  Crashes:               {crashes}")
    print(f"  Invalid final states:  {invalid_final_states}")
    print("  Result:", "PASS - state machine held stable under random input" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_fuzz_campaign() else 1)
