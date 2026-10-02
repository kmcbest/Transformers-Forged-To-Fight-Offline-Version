import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_setup.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

mesh = bpy.data.objects.get("Elita_One_Mesh")
# Find vertices with weight in LeftArm or LeftShoulder
vg_ls = mesh.vertex_groups.get("LeftShoulder")
vg_la = mesh.vertex_groups.get("LeftArm")
la_verts = [v.co for v in mesh.data.vertices if any(g.group == vg_la.index for g in v.groups)]
ls_verts = [v.co for v in mesh.data.vertices if any(g.group == vg_ls.index for g in v.groups)]

print(f"Elita Mesh LeftShoulder avg: {sum(ls_verts, mathutils.Vector())/len(ls_verts)}")
print(f"Elita Mesh LeftArm avg:      {sum(la_verts, mathutils.Vector())/len(la_verts)}")

arm = bpy.data.objects.get("Arcee_Armature")
b_ls = arm.data.bones.get("LeftShoulder")
b_la = arm.data.bones.get("LeftArm")
print(f"Arcee LeftShoulder head:     {b_ls.head_local}")
print(f"Arcee LeftArm head:          {b_la.head_local}")
