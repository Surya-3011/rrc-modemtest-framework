# Mini RRC Protocol Test Automation Framework

![tests](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/actions/workflows/tests.yml/badge.svg)

### Built for: Qualcomm — Modem System Test (MST) Engineer, On-Campus

A small but complete test bed that simulates a modem's RRC connection
state machine and puts a real automation/logging/analysis harness around
it — the same *shape* of work as the JD, scaled to something you can
build and defend in 1–2 days with just OOPS + DSA + COA + DBMS.

## Files

| File | What it does |
|---|---|
| `rrc_state_machine.py` | Core FSM: RRC_IDLE / CONNECTING / CONNECTED / INACTIVE states, event-driven transitions, power-cost model |
| `test_cases.json` | Declarative test cases — normal call flows + fault-injection cases |
| `test_framework.py` | Test runner: executes cases, writes field logs, stores results in SQLite |
| `log_analyzer.py` | Parses field logs, flags protocol violations and "unexpected drop" bugs |
| `fuzz_test.py` | Randomized stress test — 500 random event sequences, checks for crashes/undefined states |
| `main.py` | Runs everything end-to-end (this is your demo script) |

## Run it

```bash
python3 main.py
```

That's it — no external dependencies (stdlib only: `json`, `sqlite3`, `enum`, `re`, `random`).

## Continuous integration

`.github/workflows/tests.yml` runs `main.py` on every push and pull
request. `main.py` exits with status 1 if any test case fails or the
fuzz campaign finds a crash/undefined state, so the workflow actually
goes red on a real regression instead of always reporting green. The
badge at the top of this file reflects the current status.

## How this maps to the JD, bullet by bullet

- **"System level feature testing, developing/executing test strategies and test plans"**
  → `test_cases.json` + `test_framework.py`. Each test case is a declared
  scenario (initial state, event sequence, expected outcome) — exactly
  how a real test plan is structured, decoupled from the framework code.

- **"Field log analysis, troubleshooting/analyzing problems"**
  → `log_analyzer.py`. Every state transition is written to a timestamped
  log; the analyzer parses it back out and root-causes failures (which
  test, which message, why rejected) without needing to re-run code —
  this is literally what "read the field log to find the bug" looks like.

- **"Automation framework development and maintenance along with new
  feature integration"**
  → The whole `test_framework.py` design: add a new test case by editing
  JSON, no code change. Add a new protocol state/event by editing one
  dict (`TRANSITION_TABLE`) in `rrc_state_machine.py`.

- **"Testing and optimizing power consumption"**
  → `POWER_COST` per state + `power_units` accumulated per test run,
  reported per test case. Rough, but gives you a legitimate design
  conversation about how you'd extend it into a real power-state model.

- **"Improving the stability of the product"**
  → `fuzz_test.py`. Randomized/invalid event injection with an assertion
  that the FSM never throws and never lands in an undefined state — the
  same idea as stability/fuzz test campaigns run on real modem firmware.

- **"Radio Access Technologies... call flows for Single SIM and
  Multi-SIM devices"**
  → `multi_sim_demo()` in `main.py`: two independent `RRCStateMachine`
  instances proving state isolation between SIMs.

- **"Physical layer, MAC procedures, RRC protocol specifications..."**
  → The state machine itself models the RRC layer specifically (setup,
  release, suspend/resume, reconfiguration). You should be ready to say
  out loud that PHY/MAC are *not* modeled here and explain in words how
  they'd sit underneath RRC in the protocol stack (see crib sheet below).

- **"Network Simulators for preparing test beds, configuration,
  scripting and debugging"**
  → The whole repo *is* a (very simplified) network simulator + test bed:
  `test_framework.py` plays the role of the simulator generating message
  sequences, and you configure it purely via JSON — same mental model as
  configuring a real network simulator/test set.

## Where your coursework shows up

- **OOPS**: `RRCStateMachine` as a class encapsulating state + behavior;
  `RRCState`/`RRCEvent` as enums instead of magic strings.
- **DSA**: transition table as a dict-of-dicts (hash map) → O(1) lookup
  instead of an if/elif chain; be ready to state that trade-off out loud.
- **DBMS**: `results.db` (SQLite) persists structured results — mention
  you'd extend the schema to trend pass rates over multiple runs/builds.
- **COA**: use this to talk about how real state machines like this are
  often implemented as literal hardware registers/interrupts in a modem
  — a bitmask register for state, interrupt-driven event handling — even
  though this Python version models it in software.

## 1–2 day prep plan

**Day 1 (build + fundamentals, ~4–5 hrs)**
1. Run `main.py`, read every file top to bottom until you can explain
   any line without looking (30–45 min).
2. Add 2 of your own test cases to `test_cases.json` (e.g. a second
   radio-link-failure-during-reconfiguration case) — having *made a
   change yourself* is what makes "I built this" credible in interview.
3. Spend 90 min on the RAN fundamentals crib sheet below — this is what
   the JD is actually testing for, the project is just your vehicle to
   demonstrate you can build test infra around it.
4. Skim 5G/LTE RRC state diagrams (search "5G NR RRC state machine
   3GPP") so your mental model lines up with the real spec, not just
   your simplified version.

**Day 2 (polish + mock interview, ~2–3 hrs)**
1. Prepare a 90-second spoken walkthrough: what it does → why you built
   it this way → how each JD bullet maps to a file (use the table above).
2. Rehearse answers to the "likely questions" below out loud, once each.
3. Re-run `main.py` once right before the interview so a live demo works
   if asked.

## Core RAN concepts to know cold (beyond the project)

- **Protocol stack, top to bottom**: NAS (mobility/session mgmt) → RRC
  (radio connection mgmt) → PDCP (ciphering/header compression) → RLC
  (segmentation, ARQ) → MAC (scheduling, HARQ) → PHY (modulation, coding).
- **RRC states in real 5G NR**: RRC_IDLE, RRC_INACTIVE, RRC_CONNECTED —
  your project mirrors this almost exactly, so lean on it.
- **Call flow basics**: initial attach/registration, RRC setup, PDU
  session establishment, handover at a conceptual level, paging.
- **Single vs Multi-SIM**: Dual SIM Dual Standby (DSDS) vs Dual SIM Dual
  Active (DSDA) — one radio timeshared vs two radios, at a high level.
- **What "system test" actually means day to day**: running test cases
  on real hardware/network simulators (e.g. Keysight/Anritsu call boxes),
  reading modem diagnostic logs (QXDM-style), writing automation scripts,
  triaging failures back to a root cause and filing/verifying bug fixes.

## Likely interview questions, and how to use this project to answer them

- **"Walk me through a project of yours."** → Use this one. Lead with
  the *why* (JD-aligned, built for this interview under time pressure),
  then the architecture, then one concrete bug/edge case you handled
  (the out-of-sequence `SETUP_COMPLETE` rejection is a good one).
- **"How would you test a new protocol feature?"** → Talk through adding
  a new state/event to `TRANSITION_TABLE` and a new declarative test
  case in JSON, without touching the runner — that separation of
  test-data from test-code is the actual answer they're listening for.
- **"How do you debug a failing test?"** → Walk through
  `log_analyzer.py`: parse the field log, find the rejected/unexpected
  transition, trace back to which event caused it.
- **"How would you scale this to something real?"** → Talk about
  replacing the in-process FSM with calls into an actual network
  simulator / test set, replacing SQLite with a real test-results DB,
  and adding coverage tracking (which state/event pairs have been
  exercised) — shows you understand this is a toy, not a claim of
  building real modem test infra.
