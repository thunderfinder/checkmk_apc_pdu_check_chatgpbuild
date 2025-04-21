# ~/local/lib/check_mk/base/plugins/agent_based/apc_pdu_snmp.py

from cmk.agent_based.v2 import (
    AgentCheckPlugin,
    CheckPlugin,
    SNMPTree,
    SimpleSNMPSection,
    Service,
    Result,
    State,
)

# --- Sección general de la PDU ---
apc_pdu_snmp_section = SimpleSNMPSection(
    name="apc_pdu",
    detect=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26",
        oids=[
            ".1.3.6.1.4.1.318.1.1.26.2.1.1.0",  # Model
            ".1.3.6.1.4.1.318.1.1.26.2.1.2.0",  # Firmware
            ".1.3.6.1.4.1.318.1.1.26.6.1.1.0",  # Load state
            ".1.3.6.1.4.1.318.1.1.26.6.3.1.1.3.1",  # Current
            ".1.3.6.1.4.1.318.1.1.26.6.3.1.1.4.1",  # Voltage
            ".1.3.6.1.4.1.318.1.1.26.6.3.1.1.5.1",  # Power
        ]
    ),
    parse_function=lambda x: {
        "model": x[0][0],
        "firmware": x[1][0],
        "load_state": int(x[2][0]),
        "current": float(x[3][0]),
        "voltage": float(x[4][0]),
        "power": float(x[5][0]),
    },
)

# --- Sección para outlets ---
apc_pdu_outlets_section = SimpleSNMPSection(
    name="apc_pdu_outlets",
    detect=None,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26.8",
        oids=[
            # Outlet name, state (on/off), current
            ".1.1.1.1.2",  # Name
            ".3.1.1.4",    # State
            ".2.1.1.3",    # Current
        ],
    ),
    parse_function=lambda entries: {
        idx: {
            "name": name[0],
            "state": int(state[0]),
            "current": float(current[0]) / 10  # Deciamperios
        }
        for name, state, current, idx in zip(entries[0], entries[1], entries[2], range(1, len(entries[0]) + 1))
    },
)

# --- Discovery general ---
def discover_apc_pdu(section):
    yield Service(name="PDU Status")

# --- Discovery de outlets ---
def discover_apc_pdu_outlets(section):
    for idx, outlet in section.items():
        name = outlet.get("name", f"Outlet {idx}")
        yield Service(name=f"Outlet: {name}")

# --- Check general ---
def check_apc_pdu(section):
    data = section
    status_map = {
        1: State.OK,
        2: State.WARN,
        3: State.CRIT,
        4: State.CRIT,
    }
    load_state = status_map.get(data["load_state"], State.UNKNOWN)

    yield Result(
        state=load_state,
        summary=f"PDU {data['model']} | FW {data['firmware']} | Load: {data['power']}W ({data['current']}A, {data['voltage']}V)"
    )

# --- Check outlets ---
def check_apc_pdu_outlets(item, section):
    outlet = section.get(int(item.split()[-1]))
    if not outlet:
        return

    state_map = {
        1: State.OK,   # on
        2: State.CRIT, # off
    }

    state = state_map.get(outlet["state"], State.UNKNOWN)
    yield Result(
        state=state,
        summary=f"{outlet['name']} is {'ON' if outlet['state'] == 1 else 'OFF'}, Current: {outlet['current']} A"
    )

# --- Plugins ---
plugins = [
    CheckPlugin(
        name="apc_pdu",
        service_name="APC PDU",
        sections=["apc_pdu"],
        discovery_function=discover_apc_pdu,
        check_function=check_apc_pdu,
    ),
    CheckPlugin(
        name="apc_pdu_outlets",
        service_name="%s",
        sections=["apc_pdu_outlets"],
        discovery_function=discover_apc_pdu_outlets,
        check_function=check_apc_pdu_outlets,
    ),
]

agent_check_plugin = AgentCheckPlugin(
    name="apc_pdu",
    snmp_sections=[apc_pdu_snmp_section, apc_pdu_outlets_section],
    check_plugins=plugins,
)
