#!/usr/bin/env python3
"""Backend Health Check Probe for Containers & Orchestrators.

Queries the local health endpoint and checks database connectivity.
Exits 0 if healthy, exits 1 on failure.
"""

import sys
import urllib.request
import json
import os

HOST = os.environ.get("BACKEND_HOST", "127.0.0.1")
PORT = os.environ.get("PORT", os.environ.get("BACKEND_PORT", "8000"))
URL = f"http://{HOST}:{PORT}/health"


def check_health() -> int:
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                print(f"Healthcheck failed with HTTP status: {response.status}", file=sys.stderr)
                return 1

            payload = json.loads(response.read().decode("utf-8"))
            if payload.get("status") not in ("healthy", "ok"):
                print(f"Healthcheck reported non-healthy payload: {payload}", file=sys.stderr)
                return 1

            print(f"Healthcheck OK: {payload}")
            return 0
    except Exception as e:
        print(f"Healthcheck exception: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(check_health())
