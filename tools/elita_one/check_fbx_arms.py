import bpy
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("SK_CH_11.001")
vg_map = {vg.index: vg.name for vg in mesh.vertex_groups}

l_arm_verts = [v.co for v in mesh.data.vertices if any("l_upperarm" in vg_map[g.group] for g in v.groups)]
r_arm_verts = [v.co for v in mesh.data.vertices if any("r_upperarm" in vg_map[g.group] for g in v.groups)]

l_avg = sum(l_arm_verts, mathutils.Vector()) / len(l_arm_verts)
r_avg = sum(r_arm_verts, mathutils.Vector()) / len(r_arm_verts)

print(f"Left Arm avg in FBX:  {l_avg}")
print(f"Right Arm avg in FBX: {r_avg}")
