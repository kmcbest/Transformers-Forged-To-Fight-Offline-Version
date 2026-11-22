import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

veh_mesh_names = [
    "VH_Blastoff_SKEL.mo.dmx",
    "VH_BlastoffWing_STAT.mo.001.dmx",
    "VH_BlastoffWing_STAT.mo.dmx",
]
veh_objs = [bpy.data.objects.get(n) for n in veh_mesh_names]

keep_set = set(veh_objs)
for o in list(bpy.data.objects):
    if o not in keep_set:
        bpy.data.objects.remove(o, do_unlink=True)

for obj in veh_objs:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.ops.object.select_all(action="DESELECT")
for obj in veh_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = veh_objs[0]
bpy.ops.object.join()
veh = bpy.context.active_object

xs_raw = [v.co.x for v in veh.data.vertices]
ys_raw = [v.co.y for v in veh.data.vertices]
zs_raw = [v.co.z for v in veh.data.vertices]

x_tail = min(xs_raw)
x_nose = max(xs_raw)
raw_length = x_nose - x_tail
y_center = 0.5 * (min(ys_raw) + max(ys_raw))
z_bottom = min(zs_raw)

TARGET_LENGTH = 10.277
SCALE_VEH = TARGET_LENGTH / raw_length

for v in veh.data.vertices:
    ox = v.co.x
    oy = v.co.y
    oz = v.co.z
    v.co.x = (oy - y_center) * SCALE_VEH
    v.co.y = - (ox - x_tail) * SCALE_VEH + 4.239
    v.co.z = (oz - z_bottom) * SCALE_VEH

veh.data.update()

xs_b = [v.co.x for v in veh.data.vertices]
ys_b = [v.co.y for v in veh.data.vertices]
zs_b = [v.co.z for v in veh.data.vertices]

print(f"CORRECTED Vehicle Bounds:")
print(f"  X: [{min(xs_b):.3f}, {max(xs_b):.3f}] (wingspan={max(xs_b)-min(xs_b):.2f})")
print(f"  Y: [{min(ys_b):.3f}, {max(ys_b):.3f}] (length={max(ys_b)-min(ys_b):.2f})")
print(f"  Z: [{min(zs_b):.3f}, {max(zs_b):.3f}] (height={max(zs_b)-min(zs_b):.2f})")

min_y_v = min(veh.data.vertices, key=lambda v: v.co.y)
max_y_v = max(veh.data.vertices, key=lambda v: v.co.y)
print(f"  Min Y vertex (Nose): {min_y_v.co}")
print(f"  Max Y vertex (Tail): {max_y_v.co}")
