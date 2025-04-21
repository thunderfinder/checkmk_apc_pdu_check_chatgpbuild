# APC PDU SNMP Plugin for Checkmk 2.2

This is a custom SNMP-based plugin for Checkmk 2.2 that performs detailed monitoring of APC rPDU2 power distribution units.
It includes:

- Global PDU status (model, firmware, load state, power, voltage, current)
- Per-outlet monitoring (on/off state and current consumption)

## 🧩 Plugin Overview

This plugin uses the new `check_api.v2` API introduced in Checkmk 2.2 and is fully compatible with its structure.

### Features
- SNMP-based monitoring (no agent needed)
- One unified plugin for all relevant checks
- Dynamic discovery of PDU outlets
- Alerts for load state and outlet status (e.g., if an outlet is off)

## 📁 Project Structure

```
checkmk/
└── local/
    └── lib/
        └── check_mk/
            └── base/
                └── plugins/
                    └── agent_based/
                        └── apc_pdu_snmp.py
```

---

## 📦 Installation Steps

### 1. Copy the plugin file

Place `apc_pdu_snmp.py` in your site:

```bash
~/local/lib/check_mk/base/plugins/agent_based/apc_pdu_snmp.py
```

### 2. Reload Checkmk (if using Raw edition)
```bash
cmk -R
```

### 3. Detect and discover services
Run the following commands for a host configured with SNMP:

```bash
cmk -vI --detect-plugins=apc_pdu <host>
cmk -v --detect-plugins=apc_pdu <host>
```

This will:
- Discover the PDU global service
- Discover one service per outlet

---

## 🔍 What This Plugin Monitors

### General PDU Metrics
- **Model & Firmware**: Identification of the hardware
- **Load State**:
  - `1` = OK
  - `2` = Near overload (WARN)
  - `3` = Overload (CRIT)
  - `4` = Off (CRIT)
- **Current, Voltage, Power**: Real-time power metrics

### Outlet-Specific Checks
For each outlet:
- **Name**: Defined in the device config
- **On/Off status**:
  - `1` = ON (OK)
  - `2` = OFF (CRIT)
- **Current draw** in Amperes (A)

---

## 🛠 How It Works Internally

### SNMP Sections
- `apc_pdu`: Reads general metrics from the rPDU2 MIB tree
- `apc_pdu_outlets`: Fetches outlet state, current and names

### Plugin Components
- `discover_apc_pdu`: Discovers one global service
- `check_apc_pdu`: Evaluates the main PDU metrics
- `discover_apc_pdu_outlets`: One service per outlet
- `check_apc_pdu_outlets`: Checks outlet state and consumption

### OIDs Used
- Base: `.1.3.6.1.4.1.318.1.1.26`
- Examples:
  - `rPDU2OutletSwitchedStatusOutletState`: `.8.3.1.1.4`
  - `rPDU2OutletMeteredStatusCurrent`: `.8.2.1.1.3`
  - `rPDU2OutletStatusOutletName`: `.8.1.1.1.2`

---

## 🧪 Testing Tips

Use SNMPwalk to verify OIDs before running Checkmk:
```bash
snmpwalk -v2c -c public <host> .1.3.6.1.4.1.318.1.1.26
```

Check plugin output:
```bash
cmk -nv --detect-plugins=apc_pdu <host>
```

If needed, restart Checkmk services:
```bash
omd restart
```

---

## ✅ To Do / Improvements
- Add trap support for alarms
- Add phase-level monitoring if 3-phase
- Include temperature/humidity sensors if detected

---

## 📄 License
MIT License

---

## 🙌 Credits
Based on APC PowerNet MIB v4.5.7 for rPDU2 family.
Plugin created for Checkmk 2.2 with love ❤️

---

