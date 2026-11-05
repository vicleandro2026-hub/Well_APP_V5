"""Integração com macOS sem alterar as versões existentes para Windows."""

import os
from pathlib import Path
import subprocess
import sys

IS_MAC = sys.platform == "darwin"
FONT_FAMILY = "Helvetica Neue" if IS_MAC else "Segoe UI"


def open_folder(folder):
    folder = str(Path(folder).expanduser().resolve())
    if sys.platform == "win32":
        os.startfile(folder)
    else:
        command = "open" if IS_MAC else "xdg-open"
        subprocess.run([command, folder], check=True, timeout=10,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)


def wheel_steps(delta):
    # Aqua fornece deltas pequenos e frequentes; Windows usa unidades de 120.
    steps = delta / 4 if IS_MAC else delta / 120
    return max(-4.0, min(4.0, steps))
