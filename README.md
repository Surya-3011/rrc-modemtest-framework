# RRC Protocol Test Automation Framework

A lightweight test automation framework built around a simulated RRC
(Radio Resource Control) connection state machine — the kind of state
machine a cellular modem runs to manage its connection to a network
(idle, connecting, connected, and suspended/inactive states, with
event-driven transitions between them).

The project isn't a real modem stack. It's a small, self-contained
demonstration of how you'd structure test automation *around* a
protocol state machine: declarative test cases, an execution engine,
structured logging, log analysis/triage, a stability/fuzz harness, and
a CI pipeline that actually fails on regressions.

## Architecture

| File | Purpose |
|---|---|
| `rrc_state_machine.py` | Core finite state machine: `RRC_IDLE` / `RRC_CONNECTING` / `RRC_CONNECTED` / `RRC_INACTIVE` states, event-driven transitions, a relative power-cost model per state |
| `test_cases.json` | Declarative test cases — normal call-flow scenarios and fault-injection scenarios |
| `test_framework.py` | Test runner — executes cases, writes a timestamped field log, persists results to SQLite |
| `log_analyzer.py` | Parses the field log, flags protocol violations and unexpected state transitions |
| `fuzz_test.py` | Randomized stress test — fires hundreds of random event sequences at the state machine and checks it never crashes or lands in an undefined state |
| `main.py` | Runs the full pipeline end-to-end and returns a non-zero exit code on any failure |

## Design notes

- **Transition table as a hash map.** `TRANSITION_TABLE` is a
  dict-of-dicts (`{state: {event: next_state}}`), giving O(1) lookup
  instead of an `if/elif` chain, and making it trivial to add a new
  state or event without touching the state machine's control flow.
- **Invalid transitions are rejected, not thrown.** An out-of-sequence
  or malformed event leaves the state machine in its current state and
  logs a `REJECTED` entry, rather than raising an exception — this
  mirrors how a real protocol stack has to stay stable in the face of
  malformed or out-of-order signalling.
- **Test data is decoupled from test code.** Adding a new scenario
  means adding an entry to `test_cases.json`; the runner never changes.
- **Structured, queryable results.** Test outcomes are written to
  SQLite (`results.db`) rather than only printed, so results could be
  trended across multiple runs.

## Running it

```bash
python3 main.py
```

No external dependencies — standard library only (`json`, `sqlite3`,
`enum`, `re`, `random`).

Running it executes, in order: the declarative test suite, the field
log analyzer, a two-SIM independent-state demo, and a 500-iteration
fuzz/stability campaign.

## Continuous integration

`.github/workflows/tests.yml` runs `main.py` on every push and pull
request. `main.py` exits with status 1 if any test case fails or the
fuzz campaign finds a crash or undefined state, so the workflow goes
red on a real regression rather than always reporting green.

## Background: what RRC is

RRC sits in the radio protocol stack between NAS (session/mobility
management) and the lower layers (PDCP/RLC/MAC/PHY). It's responsible
for whether a device has an active radio connection at all, and for
managing the handshake to establish, suspend, resume, or release that
connection. Real RRC implementations (3GPP TS 38.331 for 5G NR) define
this in far more detail — this project models a simplified version of
the same idea: `RRC_IDLE`, `RRC_INACTIVE`, and `RRC_CONNECTED` are real
state names from the 5G NR specification.

## Possible extensions

- Replace the in-process state machine with calls into an actual
  network simulator or test set.
- Replace SQLite with a dedicated results store and add trending
  across builds.
- Add coverage tracking — which state/event pairs have actually been
  exercised by the test suite.

## License

MIT — see `LICENSE`.
