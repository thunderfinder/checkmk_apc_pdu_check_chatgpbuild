#!/usr/bin/env python3
from cmk.agent_based.v2 import (
    AgentCheckPlugin,
    CheckPlugin,
    SNMPTree,
    SimpleSNMPSection,
    Service,
    Result,
    State,
)

# --- Sección General de la PDU ---
apc_pdu_section = SimpleSNMPSection(
    name="apc_pdu",
    detect=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26",
        oids=[".2.1.1.0"]  # Model OID para detección
    ),
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26",
        oids=[
            ".2.1.1.0",  # Model
            ".2.1.2.0",  # Firmware
            ".6.1.1.0",  # Load State
            ".6.3.1.1.3.1",  # Current Phase 1
            ".6.3.1.1.4.1",  # Voltage Phase 1
            ".6.3.1.1.5.1",  # Power Phase 1
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

# --- Sección por Fase (multi-fase) ---
apc_pdu_phases_section = SimpleSNMPSection(
    name="apc_pdu_phases",
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26.6.3.1.1",
        oids=[".3", ".4"]  # Current, Voltage
    ),
    parse_function=lambda entries: {
        i + 1: {
            "current": float(current[0]),
            "voltage": float(voltage[0])
        }
        for i, (current, voltage) in enumerate(zip(entries[0], entries[1]))
    },
)

# --- Sección para sensores ambientales ---
apc_pdu_env_section = SimpleSNMPSection(
    name="apc_pdu_environment",
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26.4.4.4.1",
        oids=[".2", ".3"]  # Temp, Humidity
    ),
    parse_function=lambda entries: {
        idx: {
            "temperature": int(t[0]),
            "humidity": int(h[0])
        }
        for idx, (t, h) in enumerate(zip(entries[0], entries[1]), start=1)
    },
)

# --- Sección de Alarmas Activas (Traps) ---
apc_pdu_alarms_section = SimpleSNMPSection(
    name="apc_pdu_alarms",
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.318.1.1.26.3.1.1.1",
        oids=[".4"]
    ),
    parse_function=lambda entries: [alarm[0] for alarm in entries[0]]
)

# --- Descubrimiento y Checks ---
def discover_apc_pdu(section):
    yield Service(name="PDU Global Status")

def check_apc_pdu(section):
    status_map = {1: State.OK, 2: State.WARN, 3: State.CRIT, 4: State.CRIT}
    state = status_map.get(section["load_state"], State.UNKNOWN)
    yield Result(
        state=state,
        summary=f"{section['model']} | FW: {section['firmware']} | Power: {section['power']}W ({section['current']}A, {section['voltage']}V)"
    )

def discover_apc_pdu_phases(section):
    for idx in section:
        yield Service(name=f"Phase {idx}")

def check_apc_pdu_phases(item, section):
    phase = section.get(int(item.split()[-1]))
    if phase:
        yield Result(
            state=State.OK,
            summary=f"Phase Voltage: {phase['voltage']}V | Current: {phase['current']}A"
        )

def discover_apc_pdu_environment(section):
    for idx in section:
        yield Service(name=f"Env Sensor {idx}")

def check_apc_pdu_environment(item, section):
    sensor = section.get(int(item.split()[-1]))
    if sensor:
        state = State.OK
        if sensor["temperature"] > 40:
            state = State.WARN
        if sensor["temperature"] > 50:
            state = State.CRIT
        yield Result(
            state=state,
            summary=f"Temp: {sensor['temperature']}°C | Humidity: {sensor['humidity']}%"
        )

def discover_apc_pdu_alarms(section):
    if section:
        yield Service(name="PDU Alarms")

def check_apc_pdu_alarms(section):
    if section:
        yield Result(
            state=State.CRIT,
            summary=f"{len(section)} active alarm(s) detected"
        )
    else:
        yield Result(state=State.OK, summary="No active alarms")

# --- Registro del Plugin ---
plugins = [
    CheckPlugin(
        name="apc_pdu",
        service_name="APC PDU",
        sections=["apc_pdu"],
        discovery_function=discover_apc_pdu,
        check_function=check_apc_pdu,
    ),
    CheckPlugin(
        name="apc_pdu_phases",
        service_name="%s",
        sections=["apc_pdu_phases"],
        discovery_function=discover_apc_pdu_phases,
        check_function=check_apc_pdu_phases,
    ),
    CheckPlugin(
        name="apc_pdu_environment",
        service_name="%s",
        sections=["apc_pdu_environment"],
        discovery_function=discover_apc_pdu_environment,
        check_function=check_apc_pdu_environment,
    ),
    CheckPlugin(
        name="apc_pdu_alarms",
        service_name="PDU Alarms",
        sections=["apc_pdu_alarms"],
        discovery_function=discover_apc_pdu_alarms,
        check_function=check_apc_pdu_alarms,
    ),
]

agent_check_plugin = AgentCheckPlugin(
    name="apc_pdu_advanced",
    snmp_sections=[
        apc_pdu_section,
        apc_pdu_phases_section,
        apc_pdu_env_section,
        apc_pdu_alarms_section,
    ],
    check_plugins=plugins,
)
