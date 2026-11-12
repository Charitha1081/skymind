"""Run every SkyMind test suite: python tests/run_all.py (needs: pip install -r requirements-dev.txt)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
failed = []
for name in ("test_platform.py", "test_auth.py", "test_llm.py", "test_improve.py", "test_ingest.py", "test_embed.py", "test_jobs.py", "test_fix.py", "test_stream.py"):
    print(f"=== {name}")
    if subprocess.run([sys.executable, os.path.join(HERE, name)]).returncode:
        failed.append(name)
print("\nALL SUITES PASSED" if not failed else f"\nFAILED: {', '.join(failed)}")
sys.exit(1 if failed else 0)
