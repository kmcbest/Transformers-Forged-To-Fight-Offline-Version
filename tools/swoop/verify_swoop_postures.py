import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

# Strip parent transforms and apply
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

swoop_mesh = bpy.data.objects.get("Swoop.001")

# Measure bounding box in world space
bb = [swoop_mesh.matrix_world @ Vector(c) for c in swoop_mesh.bound_box]
curr_h = max(c.z for c in bb) - min(c.z for c in bb)
scale_factor = 11.40 / curr_h
print(f"curr_h={curr_h:.4f}, scale_factor={scale_factor:.4f}")

# Apply scale
swoop_mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = swoop_mesh
bpy.ops.object.select_all(action='DESELECT')
swoop_mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Ground to Z=0
min_z = min(v.co.z for v in swoop_mesh.data.vertices)
for v in swoop_mesh.data.vertices:
    v.co.z -= min_z

print(f"Lowest Z={min(v.co.z for v in swoop_mesh.data.vertices):.3f}, Highest Z={max(v.co.z for v in swoop_mesh.data.vertices):.3f}")

def vg_center(name):
    vg = swoop_mesh.vertex_groups.get(name)
    if not vg: return None
    pts = [v.co for v in swoop_mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    return sum(pts, Vector((0,0,0))) / len(pts) if pts else None

print(f"Head:       {vg_center('Bone_Head')}")
print(f"Back:       {vg_center('Back')}")
print(f"Bird Beak:  {vg_center('beak')}")
print(f"Left Hand:  {vg_center('Bone_L_Hand')}")
print(f"Right Hand: {vg_center('Bone_R_Hand')}")
print(f"Left Foot:  {vg_center('Bone_L_Foot00')}")
print(f"Right Foot: {vg_center('Bone_R_Foot00')}")
