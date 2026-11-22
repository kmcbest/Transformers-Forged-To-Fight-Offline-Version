import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Let's inspect swindle_robot_prepared.fbx bone names using a simple binary scan or FBX reader
fbx_path = r'3rd-party-models\Swindle\03_fbx_exports\swindle_robot_prepared.fbx'
with open(fbx_path, 'rb') as f:
    content = f.read().decode('latin1', errors='ignore')

import re
models = re.findall(r'Model::(.*?)"', content)
print(f"Total Model elements in FBX: {len(models)}")
finger_bones = [m for m in models if 'Thumb' in m or 'Index' in m or 'Middle' in m or 'Ring' in m or 'Pinky' in m]
print(f"Finger bones in FBX ({len(finger_bones)}):")
for fb in sorted(finger_bones):
    print("  ", fb)
