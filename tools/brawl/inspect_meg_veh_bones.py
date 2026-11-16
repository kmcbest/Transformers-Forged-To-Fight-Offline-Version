import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Brawl\brawl_robot.fbx")
# We can inspect the FBX or check using Unity or Python
# Let's inspect using Blender or check how build_rigged_brawl_fbx.py exported it!
