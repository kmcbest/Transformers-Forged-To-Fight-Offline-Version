import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_arm = bpy.data.objects.get("Elita_One_Armature")
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")

print("Arcee Action:", arcee_arm.animation_data.action.name if arcee_arm.animation_data else "None")
print("Elita Action:", elita_arm.animation_data.action.name if elita_arm.animation_data else "None")

bpy.context.scene.frame_set(0)
print("\nArcee RightArm pose rot:", arcee_arm.pose.bones.get("RightArm").rotation_quaternion)
print("Elita RightArm pose rot:", elita_arm.pose.bones.get("RightArm").rotation_quaternion)

print("\nElita Mesh Modifiers:")
for m in elita_mesh.modifiers:
    print(f"  Name: {m.name}, Type: {m.type}, Object: {getattr(m, 'object', None)}")

# Find any vertices on Elita Mesh that are outside the normal character envelope (X between -4.5 and -0.5, Z between 0 and 9)
bad_verts = []
for i, v in enumerate(elita_mesh.data.vertices):
    w_co = elita_mesh.matrix_world @ v.co
    # If X > -0.5 (stretching towards center) or Y far from 0
    if w_co.x > -0.5 or abs(w_co.y) > 2.0:
        bad_verts.append((i, w_co))

print(f"\nFound {len(bad_verts)} outlier vertices stretching out of envelope!")
if bad_verts:
    for i, co in bad_verts[:10]:
        vgroups = [(elita_mesh.vertex_groups[g.group].name, g.weight) for g in elita_mesh.data.vertices[i].groups]
        print(f"  Vert {i} at {co}: {vgroups}")
