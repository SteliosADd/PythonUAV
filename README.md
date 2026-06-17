# PythonUAV - Network & Bluetooth Radar

A military-styled radar interface built with Pygame that scans your local network and nearby Bluetooth (BLE) devices in real time. Designed as a cybersecurity educational tool.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

### Network Scanning
- ARP/ping sweep across the local subnet (x.x.x.0/24)
- Hostname resolution and MAC vendor identification
- Device type detection (Router, Phone, Laptop, Printer, IoT, Camera)
- Port scanning on selected devices (21 common ports including SSH, HTTP, SMB, RDP)

### Bluetooth / AirDrop Detection
- BLE device discovery via `bleak`
- Apple Continuity Protocol parsing (AirDrop, AirPods, Find My, Handoff, Hey Siri, etc.)
- Signal strength (RSSI) display with visual bars
- Identifies Apple devices from manufacturer advertisement data (Company ID 0x004C)

### Radar UI
- Animated sweep with glowing cone effect
- CRT scanline overlay and vignette for retro military aesthetic
- Devices displayed as blips with glow effects that pulse when the sweep passes
- Network devices shown as green triangles, BT devices as cyan diamonds
- AirDrop-enabled devices highlighted in blue

### Device Management
- **Click** to select a device and view detailed info
- **Tag** devices as KNOWN, SUSPECT, or TARGET
- **Hide/Unhide** devices from the radar
- **Right-click** to quick-tag
- **Hover tooltips** with device summary
- Animated connection line from center to selected device

### Tools
- **Port Scanner** - scan common ports on any network device
- **MAC Vendor Lookup** - identify manufacturer from MAC address OUI
- **Export** - save full device report to text file
- **Screenshot** - capture radar as PNG
- **Event Log** - scrolling log of all discoveries and actions
- **Alert System** - animated popups when new devices appear

## Requirements

- Python 3.10+
- Windows (uses Windows-specific ping flags and `CREATE_NO_WINDOW`)

## Installation

```bash
pip install pygame bleak
```

## Usage

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `R` | Rescan network & Bluetooth |
| `B` | Toggle Bluetooth overlay |
| `M` | Mute/unmute sounds |
| `T` | Cycle tag on selected device (KNOWN/SUSPECT/TARGET) |
| `X` / `DEL` | Hide selected device |
| `U` | Unhide all hidden devices |
| `P` | Port scan selected device |
| `S` | Export device report to file |
| `C` | Clear selection |
| `F12` | Save screenshot |
| `ESC` | Quit |
| **Left Click** | Select device |
| **Right Click** | Select + Tag device |

## Disclaimer

This tool is intended for **educational purposes** and **authorized security testing only**. Only use on networks and devices you own or have explicit permission to test. Unauthorized network scanning may violate local laws.
