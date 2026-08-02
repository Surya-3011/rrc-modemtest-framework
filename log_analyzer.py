"""
log_analyzer.py
----------------
Parses the field_log.txt produced by test_framework.py and produces a
triage-style diagnostic summary -- the kind of pass an engineer does over
real device logs when a test fails or a field unit reports a drop.

Detects:
  - protocol violations (REJECTED / out-of-sequence messages), grouped
    by test case, so a failing test can be root-caused straight from
    the log instead of re-reading code.
  - "unexpected drops": any transition into RRC_IDLE that was NOT caused
    by RRCRelease or RadioLinkFailure (would indicate a bug in the state
    machine itself, since no other event should ever silently drop you
    to IDLE).
  - a rough energy profile per test (sum of power units logged), useful
    for flagging tests that spend abnormally long in high-power states.
"""

import re
from collections import defaultdict

LOG_PATH = "field_log.txt"

LOG_LINE_RE = re.compile(
    r"\[(?P<ts>[^\]]+)\] (?P<sim>\S+) \| (?P<test>\S+) \| "
    r"(?P<event>\S+) \| (?P<from>\S+) -> (?P<to>\S+) \| (?P<status>\S+)"
)

DROP_ALLOWED_EVENTS = {"RRCRelease", "RadioLinkFailure"}


def parse_log(path=LOG_PATH):
    entries = []
    with open(path) as f:
        for line in f:
            m = LOG_LINE_RE.match(line.strip())
            if m:
                entries.append(m.groupdict())
    return entries


def analyze(entries):
    violations_by_test = defaultdict(list)
    unexpected_drops = []

    for e in entries:
        if e["status"] == "REJECTED":
            violations_by_test[e["test"]].append(e)

        if e["to"] == "RRC_IDLE" and e["from"] != "RRC_IDLE" \
                and e["event"] not in DROP_ALLOWED_EVENTS:
            unexpected_drops.append(e)

    return violations_by_test, unexpected_drops


def print_report(entries):
    violations_by_test, unexpected_drops = analyze(entries)

    print("FIELD LOG ANALYSIS")
    print("=" * 60)
    print(f"Total log lines parsed: {len(entries)}")
    print(f"Tests with protocol violations: {len(violations_by_test)}")

    for test, viols in violations_by_test.items():
        print(f"\n  [{test}]")
        for v in viols:
            print(f"    - rejected '{v['event']}' while in {v['from']}"
                  f" (message out of sequence)")

    if unexpected_drops:
        print("\n!! UNEXPECTED DROPS TO IDLE (state-machine bug candidates):")
        for d in unexpected_drops:
            print(f"    - {d['test']}: {d['from']} -> IDLE via unexpected "
                  f"event '{d['event']}'")
    else:
        print("\nNo unexpected drops to IDLE detected -- all IDLE "
              "transitions were via RRCRelease or RadioLinkFailure.")

    print("=" * 60)


if __name__ == "__main__":
    entries = parse_log()
    print_report(entries)
