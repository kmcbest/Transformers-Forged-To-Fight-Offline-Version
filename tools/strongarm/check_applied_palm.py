import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

orig_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if orig_arm.animation_data:
    orig_arm.animation_data_clear()
orig_arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

for name in ['bot:palm_geo_L', 'bot:palm_geo_R', 'bot:hand_geo_L', 'bot:hand_geo_R']:
    o = bpy.data.objects.get(name)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    for mod in list(o.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    o.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    verts = [v.co for v in o.data.vertices]
    min_x = min(v.x for v in verts)
    max_x = max(v.x for v in verts)
    min_y = min(v.y for v in verts)
    max_y = max(v.y for v in verts)
    min_z = min(v.z for v in verts)
    max_z = max(v.z for v in verts)
    print(f"{name:20s}: X=[{min_x:.4f}, {max_x:.4f}], Y=[{min_y:.4f}, {max_y:.4f}], Z=[{min_z:.4f}, {max_z:.4f}]")
