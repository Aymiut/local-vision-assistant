"""Checks the NetworkPolicies from inside the sampler pod: the sampler reaches what it needs, and nothing else.

Run it from the repo root, with the API running (the sampler image has Python but no curl):

    kubectl exec -i deploy/sampler -- python - < scripts/netcheck.py

Exits with 1 if any check gives the wrong result.
"""

import socket
import sys


# (what, host, port, should it connect?). Names go through the cluster's DNS, so the first two also
# check the DNS exception. 1.1.1.1 is an IP so that the last check doesn't depend on DNS.
# From the pod, a blocked port and a closed one look the same (refused), so the API must be up.
CHECKS = [
    ("MediaMTX", "mediamtx", 8554, True),
    ("the API on the Mac", "host.docker.internal", 8000, True),
    ("the Internet, by name", "google.com", 443, False),
    ("the Internet, by IP", "1.1.1.1", 443, False),
]


def connects(host, port):
    """Open a TCP connection and close it. k3s rejects blocked traffic, so this fails fast."""
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except OSError:
        return False


failures = 0
for what, host, port, expected in CHECKS:
    ok = connects(host, port) == expected
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {'reachable' if expected else 'blocked  '}  {what} ({host}:{port})")

print("All checks passed." if not failures else f"{failures} check(s) failed.")
sys.exit(1 if failures else 0)
