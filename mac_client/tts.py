from __future__ import annotations

import shutil
import subprocess


def speak(text: str) -> None:
    if not text:
        return

    if shutil.which("say") is None:
        print("[TTS] 'say' command not available; skipping audio output.")
        return

    subprocess.run(["say", text], check=False)
