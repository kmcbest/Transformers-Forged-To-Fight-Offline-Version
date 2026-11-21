import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]

def centroid_of(bone_name):
    vg = mesh.vertex_groups.get(bone_name)
    if not vg:
        return None
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    if not pts:
        return None
    return sum(pts, Vector((0,0,0))) / len(pts)

c_lh = centroid_of("LeftHand")
c_rh = centroid_of("RightHand")
c_toe = centroid_of("LeftToeBase") or centroid_of("LeftFoot")

print(f"NEW FBX CENTROIDS in Blender:")
print(f"  LeftHand:  {c_lh}")
print(f"  RightHand: {c_rh}")
print(f"  LeftFoot:  {c_toe}")
