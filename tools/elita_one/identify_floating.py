import bpy
import json
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")
FBX_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx")

# 1. Get original FBX vertex groups for each vertex
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))
raw_obj = bpy.data.objects.get("SK_CH_11.001")
raw_vgs = {}
for i, v in enumerate(raw_obj.data.vertices):
    raw_vgs[i] = [(raw_obj.vertex_groups[g.group].name, g.weight) for g in v.groups]

# 2. Open side by side blend
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(0)
bpy.context.view_layer.update()

elita = bpy.data.objects.get("Elita_One_Mesh")
depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita.evaluated_get(depsgraph)
mesh_eval = elita_eval.to_mesh()

floating = []
for i, v in enumerate(mesh_eval.vertices):
    w_co = elita.matrix_world @ v.co
    # The cubes are in the upper left of Elita: X in [-2.0, -0.5], Z in [6.5, 9.0]
    if -2.0 < w_co.x < -0.5 and 6.5 < w_co.z < 9.0:
        floating.append((i, w_co, raw_vgs[i]))

print(f"Total floating verts in this box: {len(floating)}")

# Group by original vertex group name
from collections import Counter
vg_counter = Counter()
for i, w_co, groups in floating:
    for gname, w in groups:
        if w > 0.5:
            vg_counter[gname] += 1

print("\nOriginal Vertex Groups contributing to floating vertices:")
for gname, count in vg_counter.most_common(20):
    print(f"  {gname}: {count} verts")

elita_eval.to_mesh_clear()
