import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import subprocess

# find Megatron clips or override controller
res = subprocess.check_output(['es.exe', '-n', '10', 'override_megatron'], text=True)
print("Found override controller files:")
for line in res.strip().splitlines():
    print(" ", line)
