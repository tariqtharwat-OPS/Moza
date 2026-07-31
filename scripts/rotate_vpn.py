#!/usr/bin/env python3
"""
VPN Rotation Script with Multiple Methods
Primary: Cloudflare WARP CLI
Fallback: ProtonVPN Windows App (UI Automation), OpenVPN CLI, System Proxy, Manual
"""

import subprocess
import time
import sys
import json
import logging
import requests
import os
import random
import threading
from pathlib import Path
from typing import Optional, Tuple, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

IP_CHECK_URL = "https://api.ipify.org?format=json"
IP_CHECK_TIMEOUT = 10
VPN_CONNECT_TIMEOUT = 30
VPN_DISCONNECT_TIMEOUT = 15
MAX_RETRIES = 3

WARP_CLI_PATH = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"

PROTONVPN_PATHS = [
    r"C:\Program Files\Proton\VPN\v5.1.5\ProtonVPN.Client.exe",
    r"C:\Program Files\Proton\VPN\v4.4.1\ProtonVPN.Client.exe",
    r"C:\Program Files\Proton\VPN\ProtonVPN.Launcher.exe",
]

OPENVPN_PATH = r"C:\Program Files\Proton\VPN\v5.1.5\Resources\openvpn.exe"
OPENVPN_CONFIG_DIR = Path(os.environ.get("USERPROFILE", "")) / "OpenVPN" / "config"


def get_current_ip() -> Optional[str]:
    try:
        response = requests.get(IP_CHECK_URL, timeout=IP_CHECK_TIMEOUT)
        if response.status_code == 200:
            return response.json().get("ip")
    except Exception as e:
        logger.error(f"Failed to get IP: {e}")
    return None


def wait_for_ip_change(old_ip: str, timeout: int = VPN_CONNECT_TIMEOUT) -> Tuple[bool, Optional[str]]:
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(3)
        new_ip = get_current_ip()
        if new_ip and new_ip != old_ip:
            logger.info(f"IP changed: {old_ip} -> {new_ip}")
            return True, new_ip
        logger.debug(f"Waiting for IP change... current: {new_ip}")
    logger.warning(f"IP did not change after {timeout}s (still: {old_ip})")
    return False, old_ip


def check_protonvpn_installed() -> Optional[str]:
    for path in PROTONVPN_PATHS:
        if Path(path).exists():
            logger.info(f"Found ProtonVPN at: {path}")
            return path
    return None


def check_service_running(service_name: str) -> bool:
    try:
        result = subprocess.run(
            ["sc", "query", service_name],
            capture_output=True, text=True, timeout=5
        )
        return "RUNNING" in result.stdout
    except Exception:
        return False


SCRIPT_DIR = Path(__file__).parent
UI_SCRIPT = SCRIPT_DIR / "protonvpn_ui.ps1"


class ProtonVPNUIAutomation:
    def __init__(self):
        self.script_path = UI_SCRIPT

    def _run(self, action: str) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File",
                 str(self.script_path), "-Action", action],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout.strip()
            if result.returncode == 0:
                return True, output
            else:
                logger.warning(f"UI action '{action}' failed: {result.stderr.strip()}")
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"UI action '{action}' timed out")
            return False, "timeout"
        except Exception as e:
            logger.error(f"UI action '{action}' error: {e}")
            return False, str(e)

    def disconnect(self) -> bool:
        ok, _ = self._run("disconnect")
        return ok

    def connect(self) -> bool:
        ok, _ = self._run("connect")
        return ok

    def change_server(self) -> bool:
        ok, _ = self._run("change_server")
        return ok

    def reconnect(self) -> bool:
        ok, _ = self._run("reconnect")
        return ok

    def is_connected(self) -> bool:
        ok, output = self._run("status")
        if ok:
            return "Connected to:" in output or "Connected" in output
        return False

    def get_status(self) -> Optional[str]:
        ok, output = self._run("status")
        if ok:
            return output.strip()
        return None


class ProtonVPNOpenVPN:
    def __init__(self):
        self.openvpn_path = OPENVPN_PATH
        self.config_dir = OPENVPN_CONFIG_DIR
        self.process = None

    def check_configs(self) -> List[Path]:
        if not self.config_dir.exists():
            logger.warning(f"Config dir not found: {self.config_dir}")
            return []
        return list(self.config_dir.glob("*.ovpn"))

    def disconnect(self) -> bool:
        try:
            subprocess.run(["taskkill", "/F", "/IM", "openvpn.exe"],
                          capture_output=True, timeout=10)
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
            return True
        except Exception as e:
            logger.error(f"OpenVPN disconnect error: {e}")
            return False

    def connect(self, config_file: Path) -> bool:
        if not self.openvpn_path.exists():
            logger.error(f"OpenVPN not found at {self.openvpn_path}")
            return False
        self.disconnect()
        try:
            self.process = subprocess.Popen(
                [str(self.openvpn_path), "--config", str(config_file)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            logger.info(f"Started OpenVPN with {config_file.name}")
            return True
        except Exception as e:
            logger.error(f"OpenVPN connect error: {e}")
            return False

    def rotate(self) -> bool:
        configs = self.check_configs()
        if not configs:
            logger.error("No OpenVPN configs found")
            return False
        config = random.choice(configs)
        return self.connect(config)


class SystemProxyRotator:
    PROXY_LIST = []

    def __init__(self):
        self.proxy_list = self.PROXY_LIST

    def get_current_proxy(self) -> Optional[str]:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_READ
            )
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if proxy_enable:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                winreg.CloseKey(key)
                return proxy_server
            winreg.CloseKey(key)
        except Exception:
            pass
        return None

    def set_proxy(self, proxy: str) -> bool:
        try:
            import winreg
            import ctypes
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy)
            winreg.CloseKey(key)
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
            logger.info(f"Set system proxy to: {proxy}")
            return True
        except Exception as e:
            logger.error(f"Failed to set proxy: {e}")
            return False

    def disable_proxy(self) -> bool:
        try:
            import winreg
            import ctypes
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
            logger.info("Disabled system proxy")
            return True
        except Exception as e:
            logger.error(f"Failed to disable proxy: {e}")
            return False

    def rotate(self) -> bool:
        if not self.proxy_list:
            logger.warning("No proxy list configured")
            return False
        proxy = random.choice(self.proxy_list)
        return self.set_proxy(proxy)


class ManualFallback:
    @staticmethod
    def notify_and_wait(message: str, timeout: int = 300) -> bool:
        logger.warning("=" * 60)
        logger.warning("MANUAL INTERVENTION REQUIRED")
        logger.warning(message)
        logger.warning(f"Waiting {timeout}s for user to change VPN...")
        logger.warning("=" * 60)

        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast("VPN Rotation Required", message, duration=10)
        except ImportError:
            pass

        print(f"\n>>> {message}")
        print("Press ENTER after changing VPN server, or wait for timeout...")

        result = [False]

        def wait_input():
            try:
                input()
                result[0] = True
            except Exception:
                pass

        t = threading.Thread(target=wait_input)
        t.daemon = True
        t.start()
        t.join(timeout=timeout)

        if result[0]:
            logger.info("User confirmed VPN change")
            return True
        else:
            logger.warning("Timeout waiting for user")
            return False


def check_openvpn_configs() -> bool:
    if OPENVPN_CONFIG_DIR.exists():
        configs = list(OPENVPN_CONFIG_DIR.glob("*.ovpn"))
        if configs:
            logger.info(f"Found {len(configs)} OpenVPN configs in {OPENVPN_CONFIG_DIR}")
            return True
    return False


class WARPCLI:
    def __init__(self):
        self.cli_path = WARP_CLI_PATH

    def _run(self, *args: str) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                [self.cli_path] + list(args),
                capture_output=True, text=True, timeout=10
            )
            output = (result.stdout + result.stderr).strip()
            ok = result.returncode == 0 and "error" not in result.stderr.lower()
            return ok, output
        except Exception as e:
            return False, str(e)

    def is_installed(self) -> bool:
        return Path(self.cli_path).exists()

    def status(self) -> Optional[str]:
        ok, output = self._run("status")
        if ok:
            return output
        return None

    def is_connected(self) -> bool:
        status = self.status()
        return status and "Connected" in status

    def connect(self) -> bool:
        ok, _ = self._run("connect")
        return ok

    def disconnect(self) -> bool:
        ok, _ = self._run("disconnect")
        return ok

    def reconnect(self) -> bool:
        self.disconnect()
        time.sleep(2)
        return self.connect()


def run_warp_rotation() -> Tuple[bool, Optional[str]]:
    logger.info("Method A: Cloudflare WARP Rotation")
    warp = WARPCLI()
    if not warp.is_installed():
        logger.error(f"WARP CLI not found at {WARP_CLI_PATH}")
        return False, None
    old_ip = get_current_ip()
    logger.info(f"Current IP: {old_ip}")
    if not warp.reconnect():
        logger.error("Failed to reconnect WARP")
        return False, None
    return wait_for_ip_change(old_ip)


def run_protonvpn_ui_rotation() -> Tuple[bool, Optional[str]]:
    logger.info("Method A: ProtonVPN UI Automation")
    try:
        vpn = ProtonVPNUIAutomation()

        status = vpn.get_status()
        logger.info(f"VPN Status: {status}")

        old_ip = get_current_ip()
        logger.info(f"Current IP: {old_ip}")

        # Use reconnect action: disconnect, wait, connect to new server
        if not vpn.reconnect():
            logger.error("Failed to reconnect VPN")
            return False, None

        return wait_for_ip_change(old_ip)
    except Exception as e:
        logger.error(f"UI Automation failed: {e}")
        return False, None


def run_openvpn_rotation() -> Tuple[bool, Optional[str]]:
    logger.info("Method B: OpenVPN CLI")
    if not check_openvpn_configs():
        logger.warning("No OpenVPN configs found")
        return False, None
    vpn = ProtonVPNOpenVPN()
    old_ip = get_current_ip()
    logger.info(f"Current IP: {old_ip}")
    if vpn.rotate():
        return wait_for_ip_change(old_ip)
    return False, None


def run_proxy_rotation() -> Tuple[bool, Optional[str]]:
    logger.info("Method C: System Proxy Rotation")
    proxy = SystemProxyRotator()
    old_ip = get_current_ip()
    logger.info(f"Current IP: {old_ip}")
    if proxy.rotate():
        time.sleep(5)
        return wait_for_ip_change(old_ip)
    return False, None


def run_manual_fallback() -> Tuple[bool, Optional[str]]:
    logger.info("Method D: Manual Fallback")
    old_ip = get_current_ip()
    logger.info(f"Current IP: {old_ip}")
    manual = ManualFallback()
    if manual.notify_and_wait(
        "Please change your VPN server manually in the ProtonVPN app",
        timeout=300
    ):
        return wait_for_ip_change(old_ip)
    return False, None


def install_protonvpn_guide() -> bool:
    logger.info("=" * 60)
    logger.info("ProtonVPN not found!")
    logger.info("Please install ProtonVPN from: https://protonvpn.com/download-windows")
    logger.info("=" * 60)
    print("\nProtonVPN is not installed.")
    print("Download from: https://protonvpn.com/download-windows")
    print("Or use winget: winget install ProtonTechnologies.ProtonVPN")
    print()
    response = input("Is ProtonVPN now installed? (y/n): ").strip().lower()
    return response == 'y'


def rotate_vpn(skip_methods: List[str] = None) -> Tuple[bool, Optional[str]]:
    skip_methods = skip_methods or []

    protonvpn_path = check_protonvpn_installed()
    if not protonvpn_path and 'ui' not in skip_methods:
        logger.warning("ProtonVPN not installed, skipping UI method")
        skip_methods.append('ui')

    initial_ip = get_current_ip()
    logger.info(f"Initial IP: {initial_ip}")

    methods = [
        ('warp', 'Cloudflare WARP CLI', run_warp_rotation),
        ('ui', 'ProtonVPN UI Automation', run_protonvpn_ui_rotation),
        ('openvpn', 'OpenVPN CLI', run_openvpn_rotation),
        ('proxy', 'System Proxy', run_proxy_rotation),
        ('manual', 'Manual Fallback', run_manual_fallback),
    ]

    for method_id, method_name, method_func in methods:
        if method_id in skip_methods:
            logger.info(f"Skipping {method_name}")
            continue
        logger.info(f"\n--- Trying {method_name} ---")
        success, new_ip = method_func()
        if success and new_ip and new_ip != initial_ip:
            logger.info(f"SUCCESS: {method_name} - IP changed to {new_ip}")
            return True, new_ip
        else:
            logger.warning(f"FAILED: {method_name}")

    logger.error("All VPN rotation methods failed!")
    return False, None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="VPN Rotation Script")
    parser.add_argument("--skip", nargs="+", choices=['warp', 'ui', 'openvpn', 'proxy', 'manual'],
                        help="Methods to skip")
    parser.add_argument("--check-ip", action="store_true", help="Just check current IP")
    parser.add_argument("--install-check", action="store_true", help="Check ProtonVPN installation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.check_ip:
        ip = get_current_ip()
        print(f"Current IP: {ip}")
        return 0 if ip else 1

    if args.install_check:
        warp = WARPCLI()
        found = []
        if warp.is_installed():
            found.append(f"Cloudflare WARP: {WARP_CLI_PATH}")
        path = check_protonvpn_installed()
        if path:
            found.append(f"ProtonVPN: {path}")
        if found:
            print("Installed VPN tools:\n  " + "\n  ".join(found))
            return 0
        else:
            print("No VPN tools found (neither WARP nor ProtonVPN)")
            return 1

    success, new_ip = rotate_vpn(skip_methods=args.skip)

    if success:
        print(f"\nOK: VPN rotated successfully! New IP: {new_ip}")
        return 0
    else:
        print(f"\nFAILED: VPN rotation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())