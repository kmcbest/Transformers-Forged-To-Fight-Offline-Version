import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

obj_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\Grindor\cha_grindor_cin_rotf_01.obj"
verts = []
with open(obj_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])

verts = np.array(verts)
print(f"=== Grindor Vehicle OBJ ({obj_path}) ===")
print(f"Total Verts: {len(verts)}")
print(f"X: [{verts[:, 0].min():.2f}, {verts[:, 0].max():.2f}]")
print(f"Y: [{verts[:, 1].min():.2f}, {verts[:, 1].max():.2f}]")
print(f"Z: [{verts[:, 2].min():.2f}, {verts[:, 2].max():.2f}]")

p_nose = verts[np.argmax(verts[:, 2])]
p_tail = verts[np.argmin(verts[:, 2])]
p_top = verts[np.argmax(verts[:, 1])]
p_bottom = verts[np.argmin(verts[:, 1])]
p_left = verts[np.argmin(verts[:, 0])]
p_right = verts[np.argmax(verts[:, 0])]

print(f"Max Z: {p_nose}")
print(f"Min Z: {p_tail}")
print(f"Max Y: {p_top}")
print(f"Min Y: {p_bottom}")
print(f"Min X: {p_left}")
print(f"Max X: {p_right}")
