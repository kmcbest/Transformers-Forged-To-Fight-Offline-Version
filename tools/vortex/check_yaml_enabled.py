import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

scene_file = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Vortex_Inspection.unity"
with open(scene_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(8250, 8275):
    print(f"{i}: {lines[i].strip()}")
print("---")
for i in range(9780, 9805):
    print(f"{i}: {lines[i].strip()}")
