import bpy
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("SK_CH_11.001")
head_verts = [v.co for v in mesh.data.vertices if "head" in mesh.vertex_groups[v.groups[0].group].name.lower()]
avg_head = sum(head_verts, mathutils.Vector()) / len(head_verts)
print("Avg head pos in raw FBX:", avg_head)
# Nose or eyes: where are they relative to head center?
nose_verts = sorted(head_verts, key=lambda v: v.y) # or x/z
print("Min X:", min(v.x for v in head_verts), "Max X:", max(v.x for v in head_verts))
print("Min Y:", min(v.y for v in head_verts), "Max Y:", max(v.y for v in head_verts))
print("Min Z:", min(v.z for v in head_verts), "Max Z:", max(v.z for v in head_verts))
