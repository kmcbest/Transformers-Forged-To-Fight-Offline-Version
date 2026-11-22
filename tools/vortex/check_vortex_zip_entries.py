import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile

with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    for name in z.namelist():
        if "logo" in name.lower() or "decepticon" in name.lower() or "symbol" in name.lower() or "vortex" in name.lower():
            print("Zip entry:", name)
