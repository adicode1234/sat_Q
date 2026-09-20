#!/usr/bin/env python3
"""
SatQuery AI — Deployment & Health Verification Script
Checks gateway connectivity, static asset serving, auth endpoint, and protected routes.
"""

import sys
import urllib.request
import urllib.error
import os

PORT = os.environ.get("PORT", "8000")
HOST = os.environ.get("HOST", "127.0.0.1")
BASE_URL = f"http://{HOST}:{PORT}"

checks = [
    ("Root Landing Page", f"{BASE_URL}/", (200,)),
    ("Auth Session Endpoint", f"{BASE_URL}/api/auth/session", (200,)),
    ("Workspace Auth Guard", f"{BASE_URL}/api/review-queue/stats", (200, 401)),
    ("Static Logo Asset", f"{BASE_URL}/satquery_logo.png", (200,)),
    ("Favicon Vector", f"{BASE_URL}/favicon.svg", (200,)),
]

print("🛰️  Verifying SatQuery AI Service Health at:", BASE_URL)
print("-" * 60)

passed = 0
for name, url, expected_codes in checks:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SatQuery-HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            if status in expected_codes:
                print(f"  ✅ [PASS] {name:25} -> HTTP {status}")
                passed += 1
            else:
                print(f"  ⚠️ [WARN] {name:25} -> HTTP {status} (expected {expected_codes})")
    except urllib.error.HTTPError as e:
        if e.code in expected_codes:
            print(f"  ✅ [PASS] {name:25} -> HTTP {e.code} (Protected as expected)")
            passed += 1
        else:
            print(f"  ❌ [FAIL] {name:25} -> HTTP {e.code}")
    except Exception as e:
        print(f"  ❌ [FAIL] {name:25} -> {e}")

print("-" * 60)
if passed == len(checks):
    print("🎉 All deployment health checks passed successfully!")
    sys.exit(0)
else:
    print(f"⚠️  {len(checks) - passed} check(s) failed.")
    sys.exit(1)
