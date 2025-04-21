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

# --- SNMP Tree ---

# Base OID: rPDU2 (.1.3.6.1.4.1.318.1.1.26)
# Aquí podrías expandir con más ramas si quieres más granularidad

apc_pdu_snmp_section = SimpleSNMPSection(
    name="apc_pdu",
    detect=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26",
        oids=[
            # Identificación
            ".1.3.6.1.4.1.318.1.1.26.2.1.1.0",  # Model
            ".1.3.6.1.4.1.318.1.1.26.2.1.2.0",  # Firmware
            # Estado general
            ".1.3.6.1.4.1.318.1.1.26.6.1.1.0",  # Load state
            # Fase A
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

# --- Discovery ---
def discover_apc_pdu(section):
    yield Service(name="PDU Status")

# --- Check Logic ---
def check_apc_pdu(section):
    data = section

    status_map = {
        1: State.OK,       # normal
        2: State.WARN,     # nearOverload
        3: State.CRIT,     # overload
        4: State.CRIT,     # off
    }

    load_state = status_map.get(data["load_state"], State.UNKNOWN)

    yield Result(
        state=load_state,
        summary=f"PDU {data['model']} | Firmware {data['firmware']} | Load: {data['power']}W ({data['current']}A, {data['voltage']}V)"
    )

# --- Plugin registration ---
check_plugin = CheckPlugin(
    name="apc_pdu",
    service_name="APC PDU",
    sections=["apc_pdu"],
    discovery_function=discover_apc_pdu,
    check_function=check_apc_pdu,
)

agent_check_plugin = AgentCheckPlugin(
    name="apc_pdu",
    snmp_sections=[apc_pdu_snmp_section],
    check_plugins=[check_plugin],
)
