"""
rrc_state_machine.py
---------------------
A simplified model of a modem's RRC (Radio Resource Control) connection
state machine — the same category of state machine a real UE (device)
modem runs to manage its connection to the network (5G/LTE call flow).

States (simplified from 3GPP TS 38.331):
    RRC_IDLE       -> no dedicated connection, low power
    RRC_CONNECTING -> transient, setup/resume procedure in progress
    RRC_CONNECTED  -> active data connection, high power
    RRC_INACTIVE   -> suspended connection, context kept, medium power

Design notes (things to be ready to explain in interview):
- Transition table is a dict-of-dicts -> O(1) event lookup instead of a
  long if/elif chain (DSA: hash map beats linear scan).
- Illegal / out-of-sequence events are REJECTED, not crashed on — mirrors
  how a real modem stack must stay stable under malformed or attacker-
  injected signalling (ties to "improving the stability of the product"
  in the JD).
- Each state carries a relative power cost, so a test session can report
  an approximate energy profile (ties to "power consumption testing").
- One state machine instance = one SIM. Instantiating two objects models
  a Multi-SIM device, each with independent state.
"""

from enum import Enum
import time


class RRCState(Enum):
    IDLE = "RRC_IDLE"
    CONNECTING = "RRC_CONNECTING"
    CONNECTED = "RRC_CONNECTED"
    INACTIVE = "RRC_INACTIVE"


class RRCEvent(Enum):
    SETUP_REQUEST = "RRCSetupRequest"
    SETUP_COMPLETE = "RRCSetupComplete"
    RELEASE = "RRCRelease"
    RELEASE_SUSPEND = "RRCRelease(suspend)"
    RESUME_REQUEST = "RRCResumeRequest"
    RESUME = "RRCResume"
    RECONFIGURATION = "RRCReconfiguration"
    RADIO_LINK_FAILURE = "RadioLinkFailure"
    PAGING = "Paging"


# Relative power cost per state, arbitrary units (CONNECTED costs the most
# radio/PA power, IDLE the least). Used only for the demo power metric.
POWER_COST = {
    RRCState.IDLE: 1,
    RRCState.INACTIVE: 2,
    RRCState.CONNECTING: 3,
    RRCState.CONNECTED: 5,
}

# (current_state) -> {event: next_state}
TRANSITION_TABLE = {
    RRCState.IDLE: {
        RRCEvent.SETUP_REQUEST: RRCState.CONNECTING,
        RRCEvent.PAGING: RRCState.CONNECTING,
    },
    RRCState.CONNECTING: {
        RRCEvent.SETUP_COMPLETE: RRCState.CONNECTED,
        RRCEvent.RESUME: RRCState.CONNECTED,
        RRCEvent.RADIO_LINK_FAILURE: RRCState.IDLE,
    },
    RRCState.CONNECTED: {
        RRCEvent.RECONFIGURATION: RRCState.CONNECTED,  # self-loop: applies new config
        RRCEvent.RELEASE: RRCState.IDLE,
        RRCEvent.RELEASE_SUSPEND: RRCState.INACTIVE,
        RRCEvent.RADIO_LINK_FAILURE: RRCState.IDLE,
    },
    RRCState.INACTIVE: {
        RRCEvent.RESUME_REQUEST: RRCState.CONNECTING,
        RRCEvent.RELEASE: RRCState.IDLE,
        RRCEvent.RADIO_LINK_FAILURE: RRCState.IDLE,
    },
}


class RRCStateMachine:
    def __init__(self, sim_id="UE-1"):
        self.sim_id = sim_id
        self.state = RRCState.IDLE
        self.power_units = 0
        # history entries: (timestamp, sim_id, event, from_state, to_state, status)
        self.history = []

    def handle_event(self, event: RRCEvent):
        ts = time.time()
        from_state = self.state
        valid = TRANSITION_TABLE.get(self.state, {})

        if event in valid:
            next_state = valid[event]
            status = "OK"
        else:
            # Out-of-sequence / malformed message: stay put, flag it.
            next_state = self.state
            status = "REJECTED"

        self.power_units += POWER_COST[self.state]
        self.history.append((ts, self.sim_id, event.value, from_state.value,
                              next_state.value, status))
        self.state = next_state
        return status

    def run_sequence(self, events):
        for e in events:
            self.handle_event(e)
        return self.state
