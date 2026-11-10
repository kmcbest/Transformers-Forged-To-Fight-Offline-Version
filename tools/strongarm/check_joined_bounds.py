import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for m in mesh_objs:
    bpy.ops.object.select_all(action='DESELECT')
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    for mod in list(m.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bpy.data.objects.remove(arm, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
for m in mesh_objs:
    m.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]
bpy.ops.object.join()
joined = bpy.context.view_layer.objects.active

xs = [v.co.x for v in joined.data.vertices]
ys = [v.co.y for v in joined.data.vertices]
zs = [v.co.z for v in joined.data.vertices]

print(f"Joined raw mesh bounds:")
print(f"  X: [{min(xs):.4f}, {max(xs):.4f}], span={max(xs)-min(xs):.4f}")
print(f"  Y: [{min(ys):.4f}, {max(ys):.4f}], span={max(ys)-min(ys):.4f}")
print(f"  Z: [{min(zs):.4f}, {max(zs):.4f}], span={max(zs)-min(zs):.4f}")
