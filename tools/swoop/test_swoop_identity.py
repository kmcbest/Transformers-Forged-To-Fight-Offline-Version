import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

# Apply parent transform to keep world positions
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

swoop_mesh = bpy.data.objects.get("Swoop.001")
bb = [swoop_mesh.matrix_world @ Vector(c) for c in swoop_mesh.bound_box]
curr_h = max(c.z for c in bb) - min(c.z for c in bb)
scale_factor = 11.40 / curr_h
print(f"curr_h={curr_h:.4f}, scale_factor={scale_factor:.4f}")

S_mat = Matrix.Scale(scale_factor, 4)
swoop_mesh.matrix_world = S_mat @ swoop_mesh.matrix_world

pts = [swoop_mesh.matrix_world @ v.co for v in swoop_mesh.data.vertices]
min_z = min(p.z for p in pts)
print(f"min_z={min_z:.4f}, max_z={max(p.z for p in pts):.4f}")

# Check Left Hand and Right Hand
for vg in swoop_mesh.vertex_groups:
    if vg.name in ["Bone_L_Hand", "Bone_R_Hand"]:
        v_in_g = [pts[v.index] for v in swoop_mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
        if v_in_g:
            mean_p = sum(v_in_g, Vector((0,0,0))) / len(v_in_g)
            print(f"  VG {vg.name} ({len(v_in_g)} verts) pos after scale: X={mean_p.x:+.3f}, Y={mean_p.y:+.3f}, Z={mean_p.z - min_z:+.3f}")

wpn_mesh = bpy.data.objects.get("Swoop_Weapon")
if wpn_mesh:
    wpn_mesh.matrix_world = S_mat @ wpn_mesh.matrix_world
    wpts = [wpn_mesh.matrix_world @ v.co for v in wpn_mesh.data.vertices]
    mean_w = sum(wpts, Vector((0,0,0))) / len(wpts)
    print(f"  Swoop_Weapon pos: X={mean_w.x:+.3f}, Y={mean_w.y:+.3f}, Z={mean_w.z - min_z:+.3f}")
