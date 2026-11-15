import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector

# Inspect the thumb vertices in current blitzwing_robot.fbx
FBX_PATH = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

m = [o for o in bpy.data.objects if o.type == 'MESH'][0]

for bname in ["LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb3", "RightHandThumb1", "RightHandThumb2", "RightHandThumb3"]:
    vg = m.vertex_groups.get(bname)
    if vg:
        verts = [v for v in m.data.vertices if any(g.group == vg.index and g.weight > 0.3 for g in v.groups)]
        if verts:
            c = sum((v.co for v in verts), Vector()) / len(verts)
            print(f"Group '{bname:18s}': {len(verts):3d} verts, center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f})")
            min_x, max_x = min(v.co.x for v in verts), max(v.co.x for v in verts)
            min_y, max_y = min(v.co.y for v in verts), max(v.co.y for v in verts)
            min_z, max_z = min(v.co.z for v in verts), max(v.co.z for v in verts)
            print(f"   X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")
