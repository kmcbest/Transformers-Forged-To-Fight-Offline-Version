import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

# Check exact Z/X distribution of bot:palm_geo_L vertices weighted to jt_elbow_L vs jt_wrist_L vs jt_thumb1_L
palm = bpy.data.objects["bot:palm_geo_L"]
bpy.ops.object.select_all(action='DESELECT')
palm.select_set(True)
bpy.context.view_layer.objects.active = palm
for m in list(palm.modifiers):
    if m.type == 'ARMATURE':
        bpy.ops.object.modifier_apply(modifier=m.name)
palm.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

for vgn in ["bot:jt_elbow_L", "bot:jt_wrist_L", "bot:jt_thumb1_L"]:
    vg = palm.vertex_groups.get(vgn)
    if not vg:
        continue
    pts = [(v.index, v.co, g.weight) for v in palm.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.01]
    pts.sort(key=lambda x: -x[1].x)
    print(f"\n{vgn} ({len(pts)} verts):")
    for idx, co, w in pts[:8]:
        print(f"  v[{idx:4d}] w={w:.2f} raw=({co.x:+.4f}, {co.y:+.4f}, {co.z:+.4f})")

# Also inspect bot:arm_geo_L bounds near wrist
arm_g = bpy.data.objects["bot:arm_geo_L"]
bpy.ops.object.select_all(action='DESELECT')
arm_g.select_set(True)
bpy.context.view_layer.objects.active = arm_g
for m in list(arm_g.modifiers):
    if m.type == 'ARMATURE':
        bpy.ops.object.modifier_apply(modifier=m.name)
vs = [v.co for v in arm_g.data.vertices]
# Wrist end is highest X in raw A-pose
vs.sort(key=lambda p: -p.x)
print("\nRaw bot:arm_geo_L top wrist-end 8 verts (highest X):")
for p in vs[:8]:
    print(f"  ({p.x:+.4f}, {p.y:+.4f}, {p.z:+.4f})")
