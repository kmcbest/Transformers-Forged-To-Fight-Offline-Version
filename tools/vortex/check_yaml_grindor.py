import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

scene_file = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Vortex_Inspection.unity"
with open(scene_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines):
    if "cha_grindor_cin_rotf_00" in line:
        print(f"Line {i}: {line.strip()}")
        # print next 25 lines
        for j in range(i, min(i + 25, len(lines))):
            print(f"  {lines[j].strip()}")
        print("---")
