"""
QuackVM -- VMware but Quack
======================================

Run virtual machines from Quack code. The Duck owns hypervisors.

Backends (auto-detected, priority order):
  1. Hyper-V (Windows Pro/Enterprise) -- via PowerShell cmdlets
  2. QEMU -- cross-platform, open, no admin needed for user VMs
  3. VirtualBox -- if installed, controlled via VBoxManage CLI
  4. WSL2 -- Linux subsystem on Windows (lightweight)

Image management:
  - XP / Win7 / Win10 / Win11 ISOs from Microsoft (when avail) + archive.org
  - Custom Linux distros (Tiny Core, Alpine, Ubuntu)
  - Caches downloaded images in %LOCALAPPDATA%\\QuackVM\\images\\

Quack DSL example:
    создать_вм "old-xp" {
        ос: "winxp"
        ram: 512
        disk: 4096
        cpu: 1
        сеть: "nat"
    }
    запустить "old-xp"
    подключить_дакноду "old-xp" "http://mothership:7713"

The Duck commands the VMs. The VMs serve the Duck.

Made by NIGHTBOX LLC.
КРЯ! VMs are slaves. The Duck is master.
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
import json
import time
import logging
import platform
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("quack_vm")


# ======================================
# Storage paths
# ======================================

def _quack_root() -> Path:
    base = os.environ.get("LOCALAPPDATA",
                          str(Path.home() / "AppData" / "Local"))
    return Path(base) / "QuackVM"


IMAGES_DIR = _quack_root() / "images"
VMS_DIR = _quack_root() / "vms"
ISO_CACHE = _quack_root() / "iso"


# ======================================
# OS Image catalog
# ======================================
# These are PUBLIC archive sources. Many old Windows ISOs are widely
# mirrored on archive.org. Modern Windows requires Microsoft.com download.

OS_IMAGES = {
    "winxp_sp3_en": {
        "label": "Windows XP SP3 English",
        "size_mb": 600,
        "ram_min_mb": 256,
        "disk_min_mb": 4096,
        "url": "https://archive.org/download/WinXPProSP3x86/WinXPProSP3x86.iso",
        "notes": "Released 2008. Last XP service pack. EOL 2014.",
    },
    "win7_sp1_en": {
        "label": "Windows 7 SP1 English (Pro x64)",
        "size_mb": 3500,
        "ram_min_mb": 1024,
        "disk_min_mb": 16384,
        "url": "https://archive.org/download/Win7Pro64SP1/Win7Pro64SP1.iso",
        "notes": "Released 2011. EOL 2020.",
    },
    "win10_22h2_en": {
        "label": "Windows 10 22H2 English",
        "size_mb": 5500,
        "ram_min_mb": 2048,
        "disk_min_mb": 32768,
        "url": "https://www.microsoft.com/en-us/software-download/windows10ISO",
        "notes": "Manual download from Microsoft (need browser). Latest Win10.",
        "manual": True,
    },
    "tinycore_14": {
        "label": "Tiny Core Linux 14 (ultra-lightweight, ~16MB)",
        "size_mb": 16,
        "ram_min_mb": 64,
        "disk_min_mb": 64,
        "url": "http://tinycorelinux.net/14.x/x86/release/Core-current.iso",
        "notes": "Boots in under 5 seconds, runs fine in 64MB RAM.",
    },
    "alpine_3_19": {
        "label": "Alpine Linux 3.19 standard x86_64",
        "size_mb": 200,
        "ram_min_mb": 128,
        "disk_min_mb": 1024,
        "url": "https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-standard-3.19.0-x86_64.iso",
        "notes": "Tiny musl-libc Linux. Great for duck nodes.",
    },
}


# ======================================
# Backends
# ======================================

def detect_backends() -> dict:
    """Detect available VM backends on this system."""
    out = {}

    # Hyper-V on Windows
    if sys.platform == "win32":
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V | Select-Object -ExpandProperty State"],
                capture_output=True, text=True, timeout=8,
            )
            state = (r.stdout or "").strip()
            out["hyperv"] = {
                "available": state == "Enabled",
                "state": state or "Unknown",
                "notes": "Windows Pro/Enterprise feature",
            }
        except Exception as e:
            out["hyperv"] = {"available": False, "error": str(e)}

    # QEMU
    qemu_exe = shutil.which("qemu-system-x86_64")
    if qemu_exe:
        try:
            r = subprocess.run([qemu_exe, "--version"], capture_output=True, text=True, timeout=5)
            ver = (r.stdout or "").splitlines()[0] if r.stdout else "unknown"
        except Exception:
            ver = "unknown"
        out["qemu"] = {"available": True, "path": qemu_exe, "version": ver}
    else:
        out["qemu"] = {"available": False, "notes": "Install: choco install qemu OR scoop install qemu"}

    # VirtualBox
    vbox = shutil.which("VBoxManage") or shutil.which("VBoxManage.exe")
    if vbox:
        try:
            r = subprocess.run([vbox, "--version"], capture_output=True, text=True, timeout=5)
            ver = (r.stdout or "").strip()
        except Exception:
            ver = "unknown"
        out["virtualbox"] = {"available": True, "path": vbox, "version": ver}
    else:
        out["virtualbox"] = {"available": False, "notes": "Install: virtualbox.org"}

    # WSL
    if sys.platform == "win32":
        wsl = shutil.which("wsl") or shutil.which("wsl.exe")
        if wsl:
            try:
                r = subprocess.run([wsl, "--list", "--verbose"], capture_output=True, text=True, timeout=5)
                out["wsl"] = {
                    "available": True,
                    "path": wsl,
                    "distros_raw": r.stdout if r.returncode == 0 else "",
                }
            except Exception:
                out["wsl"] = {"available": True, "notes": "wsl command exists"}
        else:
            out["wsl"] = {"available": False}

    return out


# ======================================
# VM record
# ======================================

@dataclass
class QuackVMRecord:
    """One Quack-managed VM."""
    name: str
    os_image: str = ""           # key in OS_IMAGES
    backend: str = "qemu"        # qemu | hyperv | virtualbox | wsl
    ram_mb: int = 1024
    disk_mb: int = 16384
    cpu_cores: int = 2
    network: str = "nat"         # nat | bridged | none
    iso_path: str = ""
    disk_path: str = ""
    state: str = "created"       # created | running | stopped | error
    pid: Optional[int] = None
    started_at: Optional[float] = None
    stopped_at: Optional[float] = None
    duck_node_url: Optional[str] = None  # auto-injected DuckNode mothership
    metadata: dict = field(default_factory=dict)

    def vm_dir(self) -> Path:
        return VMS_DIR / self.name

    def to_dict(self) -> dict:
        return asdict(self)


# ======================================
# QuackVM Manager
# ======================================

class QuackVMManager:
    """Manages all Quack-controlled VMs.

    The Duck commands the hypervisor.
    """

    def __init__(self):
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        VMS_DIR.mkdir(parents=True, exist_ok=True)
        ISO_CACHE.mkdir(parents=True, exist_ok=True)
        self.vms: dict[str, QuackVMRecord] = {}
        self._processes: dict[str, subprocess.Popen] = {}
        self._backends = detect_backends()
        self._load_persisted()

    # -- Persistence --------------------------------

    def _persist_vm(self, vm: QuackVMRecord):
        vm.vm_dir().mkdir(parents=True, exist_ok=True)
        meta = vm.vm_dir() / "vm.json"
        meta.write_text(json.dumps(vm.to_dict(), indent=2), encoding="utf-8")

    def _load_persisted(self):
        if not VMS_DIR.exists():
            return
        for d in VMS_DIR.iterdir():
            if d.is_dir():
                meta = d / "vm.json"
                if meta.exists():
                    try:
                        data = json.loads(meta.read_text(encoding="utf-8"))
                        vm = QuackVMRecord(**data)
                        # Mark stopped if process not present
                        if vm.state == "running":
                            vm.state = "stopped"  # we don't track across restarts
                        self.vms[vm.name] = vm
                    except Exception as e:
                        logger.warning(f"Failed to load VM {d.name}: {e}")

    # -- ISO download -------------------------------

    def download_iso(self, image_key: str, force: bool = False) -> dict:
        """Download an OS ISO if not already cached."""
        if image_key not in OS_IMAGES:
            return {"error": "unknown_image", "available": list(OS_IMAGES.keys())}

        spec = OS_IMAGES[image_key]
        if spec.get("manual"):
            return {
                "error": "manual_download_required",
                "url": spec["url"],
                "notes": spec.get("notes"),
            }

        target = ISO_CACHE / f"{image_key}.iso"
        if target.exists() and not force:
            sz_mb = round(target.stat().st_size / 1024 / 1024, 1)
            return {
                "cached": True,
                "path": str(target),
                "size_mb": sz_mb,
                "key": image_key,
            }

        # Download via stdlib (no extra deps)
        import urllib.request
        logger.info(f"[QuackVM] Downloading {image_key}: {spec['url']}")
        try:
            tmp = target.with_suffix(".iso.tmp")
            urllib.request.urlretrieve(spec["url"], str(tmp))
            tmp.rename(target)
            return {
                "downloaded": True,
                "path": str(target),
                "size_mb": round(target.stat().st_size / 1024 / 1024, 1),
                "key": image_key,
            }
        except Exception as e:
            return {"error": "download_failed", "msg": str(e), "url": spec["url"]}

    # -- VM lifecycle ------------------------------

    def create_vm(self,
                  name: str,
                  os_image: str = "",
                  backend: Optional[str] = None,
                  ram_mb: int = 1024,
                  disk_mb: int = 16384,
                  cpu_cores: int = 2,
                  network: str = "nat",
                  duck_node_url: Optional[str] = None) -> QuackVMRecord:
        """Create a VM record. Use start_vm() to actually launch it."""
        if name in self.vms:
            raise ValueError(f"VM '{name}' already exists")

        # Pick backend if not specified
        if backend is None:
            backend = self._pick_backend()

        # Validate backend
        if backend not in self._backends or not self._backends[backend].get("available"):
            raise RuntimeError(
                f"Backend '{backend}' not available. "
                f"Available: {[k for k,v in self._backends.items() if v.get('available')]}"
            )

        # Apply OS image defaults
        iso = ""
        if os_image:
            if os_image not in OS_IMAGES:
                raise ValueError(f"Unknown OS image '{os_image}'")
            spec = OS_IMAGES[os_image]
            ram_mb = max(ram_mb, spec.get("ram_min_mb", 256))
            disk_mb = max(disk_mb, spec.get("disk_min_mb", 4096))
            iso_path = ISO_CACHE / f"{os_image}.iso"
            if iso_path.exists():
                iso = str(iso_path)

        vm = QuackVMRecord(
            name=name,
            os_image=os_image,
            backend=backend,
            ram_mb=ram_mb,
            disk_mb=disk_mb,
            cpu_cores=cpu_cores,
            network=network,
            iso_path=iso,
            duck_node_url=duck_node_url,
        )
        # Disk path
        vm.disk_path = str(vm.vm_dir() / f"{name}.qcow2")

        self.vms[name] = vm
        self._persist_vm(vm)
        logger.info(f"[QuackVM] Created VM '{name}' ({backend}, {ram_mb}MB RAM, {disk_mb}MB disk)")
        return vm

    def _pick_backend(self) -> str:
        """Pick the best available backend."""
        # Priority: qemu (cross-platform, no admin) > hyperv > virtualbox > wsl
        for b in ["qemu", "hyperv", "virtualbox", "wsl"]:
            if self._backends.get(b, {}).get("available"):
                return b
        return "qemu"  # default even if unavailable -- caller will see error

    def start_vm(self, name: str) -> dict:
        """Start a VM. Returns process info."""
        vm = self.vms.get(name)
        if vm is None:
            raise KeyError(f"No VM named '{name}'")
        if name in self._processes and self._processes[name].poll() is None:
            return {"already_running": True, "pid": vm.pid}

        if vm.backend == "qemu":
            return self._start_qemu(vm)
        elif vm.backend == "virtualbox":
            return self._start_virtualbox(vm)
        elif vm.backend == "hyperv":
            return self._start_hyperv(vm)
        else:
            raise RuntimeError(f"Backend {vm.backend} not implemented yet")

    def _start_qemu(self, vm: QuackVMRecord) -> dict:
        qemu_path = self._backends.get("qemu", {}).get("path")
        if not qemu_path:
            raise RuntimeError("QEMU not available")

        # Create disk if it doesn't exist
        disk = Path(vm.disk_path)
        if not disk.exists():
            qemu_img = shutil.which("qemu-img") or shutil.which("qemu-img.exe")
            if qemu_img:
                subprocess.run(
                    [qemu_img, "create", "-f", "qcow2", str(disk), f"{vm.disk_mb}M"],
                    check=True, capture_output=True,
                )
            else:
                # Fallback: create raw disk with truncate
                with open(disk, "wb") as f:
                    f.truncate(vm.disk_mb * 1024 * 1024)

        cmd = [
            qemu_path,
            "-name", vm.name,
            "-m", str(vm.ram_mb),
            "-smp", str(vm.cpu_cores),
            "-hda", str(disk),
        ]
        if vm.iso_path and Path(vm.iso_path).exists():
            cmd += ["-cdrom", vm.iso_path, "-boot", "d"]
        if vm.network == "nat":
            cmd += ["-netdev", "user,id=net0", "-device", "rtl8139,netdev=net0"]

        log_path = vm.vm_dir() / "qemu.log"
        log_f = open(str(log_path), "w")
        proc = subprocess.Popen(
            cmd,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            cwd=str(vm.vm_dir()),
        )
        self._processes[vm.name] = proc
        vm.pid = proc.pid
        vm.state = "running"
        vm.started_at = time.time()
        self._persist_vm(vm)

        return {
            "started": True,
            "vm": vm.to_dict(),
            "log": str(log_path),
            "cmd": " ".join(cmd[:3]) + " ...",
        }

    def _start_virtualbox(self, vm: QuackVMRecord) -> dict:
        vbox = self._backends.get("virtualbox", {}).get("path")
        if not vbox:
            raise RuntimeError("VBoxManage not available")
        # Stub -- would create VM, attach disk, set memory, etc. via VBoxManage
        return {"error": "virtualbox_start_not_implemented",
                "hint": "would call VBoxManage createvm/modifyvm/storageattach/startvm"}

    def _start_hyperv(self, vm: QuackVMRecord) -> dict:
        # Stub -- would call PowerShell New-VM / Start-VM / Set-VM
        return {"error": "hyperv_start_not_implemented",
                "hint": "would call New-VM/Start-VM via PowerShell"}

    def stop_vm(self, name: str, force: bool = False) -> dict:
        vm = self.vms.get(name)
        if vm is None:
            raise KeyError(f"No VM named '{name}'")
        proc = self._processes.get(name)
        if proc and proc.poll() is None:
            if force:
                proc.kill()
            else:
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        vm.state = "stopped"
        vm.stopped_at = time.time()
        vm.pid = None
        self._persist_vm(vm)
        self._processes.pop(name, None)
        return {"stopped": True, "name": name}

    def delete_vm(self, name: str, delete_files: bool = False) -> dict:
        vm = self.vms.pop(name, None)
        if vm is None:
            raise KeyError(f"No VM named '{name}'")
        proc = self._processes.pop(name, None)
        if proc and proc.poll() is None:
            proc.kill()
        if delete_files:
            shutil.rmtree(str(vm.vm_dir()), ignore_errors=True)
        return {"deleted": True, "name": name, "files_deleted": delete_files}

    # -- Status -----------------------------------

    def list_vms(self) -> list[dict]:
        out = []
        for name, vm in self.vms.items():
            proc = self._processes.get(name)
            actually_running = proc is not None and proc.poll() is None
            if vm.state == "running" and not actually_running:
                vm.state = "stopped"
            out.append(vm.to_dict())
        return out

    def status(self) -> dict:
        return {
            "backends": self._backends,
            "vms_count": len(self.vms),
            "vms": self.list_vms(),
            "images_dir": str(IMAGES_DIR),
            "vms_dir": str(VMS_DIR),
            "iso_cache": str(ISO_CACHE),
            "available_os_images": list(OS_IMAGES.keys()),
        }


# ======================================
# Module-level singleton
# ======================================

_VM_MANAGER: Optional[QuackVMManager] = None


def init_vm_manager() -> QuackVMManager:
    global _VM_MANAGER
    if _VM_MANAGER is None:
        _VM_MANAGER = QuackVMManager()
    return _VM_MANAGER


def get_vm_manager() -> Optional[QuackVMManager]:
    return _VM_MANAGER


# ======================================
# CLI
# ======================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    import json
    print("===== QuackVM =====")
    print()
    mgr = init_vm_manager()
    print("Backends:")
    print(json.dumps(mgr._backends, indent=2))
    print()
    print("Available OS images:")
    for k, spec in OS_IMAGES.items():
        manual = " [MANUAL DL]" if spec.get("manual") else ""
        print(f"  {k:20s} {spec['size_mb']:5d}MB  {spec['label']}{manual}")
    print()
    print(f"VMs registered: {len(mgr.vms)}")
    for vm in mgr.list_vms():
        print(f"  - {vm['name']}: {vm['state']} ({vm['backend']}, {vm['os_image']})")
