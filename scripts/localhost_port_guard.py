#!/usr/bin/env python3
"""
Run a localhost command on a fixed port with retry + port-clear behavior.

Example:
  python3 scripts/localhost_port_guard.py --port 4173 --retries 2 -- bm ui --config brand-config.yaml
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from typing import List


def _listening_pids(port: int) -> List[int]:
    try:
        out = subprocess.check_output(
            ["lsof", "-tiTCP:%d" % port, "-sTCP:LISTEN"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    if not out:
        return []
    return [int(line.strip()) for line in out.splitlines() if line.strip().isdigit()]


def _kill_pids(pids: List[int], sig: signal.Signals) -> None:
    for pid in pids:
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass


def clear_port(port: int, grace_seconds: float = 1.5) -> bool:
    pids = _listening_pids(port)
    if not pids:
        return True
    print(f"[port-guard] clearing port {port} (pids={pids})")
    _kill_pids(pids, signal.SIGTERM)
    time.sleep(grace_seconds)
    remaining = _listening_pids(port)
    if remaining:
        print(f"[port-guard] force killing remaining pids on {port}: {remaining}")
        _kill_pids(remaining, signal.SIGKILL)
        time.sleep(0.5)
    return len(_listening_pids(port)) == 0


def run_fixed_port(
    port: int,
    cmd: List[str],
    retries: int,
    startup_seconds: float,
) -> int:
    env = os.environ.copy()
    env["PORT"] = str(port)

    for attempt in range(1, retries + 2):
        print(f"[port-guard] attempt {attempt}/{retries + 1} on port {port}")
        if not clear_port(port):
            print(f"[port-guard] failed to clear port {port}")
            if attempt <= retries:
                continue
            return 1

        proc = subprocess.Popen(cmd, env=env)
        start = time.time()
        while time.time() - start < startup_seconds:
            rc = proc.poll()
            if rc is not None:
                print(f"[port-guard] process exited early with code {rc}")
                break
            time.sleep(0.2)
        else:
            print(f"[port-guard] server running on fixed port {port}")
            return proc.wait()

        if attempt <= retries:
            print("[port-guard] retrying after early exit...")
            continue
        return proc.returncode if proc.returncode is not None else 1
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixed-port launcher with clear-and-retry.")
    parser.add_argument("--port", type=int, required=True, help="Fixed localhost port.")
    parser.add_argument("--retries", type=int, default=2, help="Retry attempts after first failure.")
    parser.add_argument(
        "--startup-seconds",
        type=float,
        default=3.0,
        help="How long process must stay alive to be considered started.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to execute after --")
    args = parser.parse_args()

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("error: provide a command after --", file=sys.stderr)
        return 2

    return run_fixed_port(
        port=args.port,
        cmd=cmd,
        retries=max(args.retries, 0),
        startup_seconds=max(args.startup_seconds, 0.5),
    )


if __name__ == "__main__":
    raise SystemExit(main())
