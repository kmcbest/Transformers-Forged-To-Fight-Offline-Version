import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("Arcee_Armature")
b_l = arm.data.bones.get("LeftArm")
b_r = arm.data.bones.get("RightArm")
b_fa = arm.data.bones.get("LeftForeArm")

print("Arcee Rest Armature:")
print(f"  LeftArm head: {b_l.head_local}, tail: {b_l.tail_local}")
print(f"  LeftForeArm head: {b_fa.head_local}, tail: {b_fa.tail_local}")
dir_l = (b_fa.head_local - b_l.head_local).normalized()
print(f"  Left Upper Arm direction vector in rest: {dir_l}")

# Check Elita FBX raw mesh arm direction
mesh = bpy.data.objects.get("Elita_One_Mesh")
# Find average of LeftArm vs LeftForeArm vertices in rest mesh
vg_la = mesh.vertex_groups.get("LeftArm")
vg_lfa = mesh.vertex_groups.get("LeftForeArm")
la_verts = [v.co for v in mesh.data.vertices if any(g.group == vg_la.index for g in v.groups)]
lfa_verts = [v.co for v in mesh.data.vertices if any(g.group == vg_lfa.index for g in v.groups)]
la_avg = sum(la_verts, mathutils.Vector()) / len(la_verts)
lfa_avg = sum(lfa_verts, mathutils.Vector()) / len(lfa_verts)
dir_elita = (lfa_avg - la_avg).normalized()
print(f"  Elita Mesh Left Upper Arm direction in rest mesh: {dir_elita}")
