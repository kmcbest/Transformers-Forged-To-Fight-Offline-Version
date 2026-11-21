import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

robot = bpy.data.objects.get("cha_sideswipe_main")

slot1_polys = [p for p in robot.data.polygons if p.material_index == 1]
slot1_verts = set(vi for p in slot1_polys for vi in p.vertices)

print(f"Slot 1 has {len(slot1_verts)} vertices.")
# Test offsetting vertices forward along -Y by 0.025
orig_ys = [robot.data.vertices[vi].co.y for vi in slot1_verts]
print(f"Original Y range: [{min(orig_ys):.4f}, {max(orig_ys):.4f}]")

# Pocket front rim Y (Slot 0)
rim_ys = [-1.15, -1.18, -1.14]
print(f"Rim Y is ~ -1.15. If we offset Mesh 20 by -0.025, Y will be [{min(orig_ys)-0.025:.4f}, {max(orig_ys)-0.025:.4f}]")
