"""Run every SkyMind test suite: python tests/run_all.py (needs: pip install -r requirements-dev.txt)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
failed = []
for name in ("test_platform.py", "test_auth.py", "test_llm.py"):
    print(f"=== {name}")
    if subprocess.run([sys.executable, os.path.join(HERE, name)]).returncode:
        failed.append(name)
print("\nALL SUITES PASSED" if not failed else f"\nFAILED: {', '.join(failed)}")
sys.exit(1 if failed else 0)
