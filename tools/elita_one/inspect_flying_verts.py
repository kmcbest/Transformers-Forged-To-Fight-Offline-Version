import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arcee_mesh = bpy.data.objects.get("Arcee_Mesh")
arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

# Find which bones have vertices that are flying far from the armature center
print("Inspecting Arcee Mesh deformed vertices:")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_a = arcee_mesh.evaluated_get(depsgraph)
eval_mesh_a = eval_a.to_mesh()

flying_bones = {}
for i, v in enumerate(eval_mesh_a.vertices):
    w_co = eval_a.matrix_world @ v.co
    # If Z > 6.0 and abs(w_co.x - 2.6) > 1.2, or floating in air
    # Let's check distance to closest bone in armature
    vgroups = [(arcee_mesh.vertex_groups[g.group].name, g.weight) for g in arcee_mesh.data.vertices[i].groups]
    main_b = max(vgroups, key=lambda x: x[1])[0] if vgroups else "None"
    
    # Check if this vertex is one of the floating pink cylinders
    # (e.g. between X=0 and X=2.0, or X > 3.5, or Y < -0.5)
    if (w_co.x < 1.8 and w_co.x > -1.8) or w_co.z > 7.0:
        flying_bones[main_b] = flying_bones.get(main_b, 0) + 1

print(f"Flying vertices by bone group in Arcee: {flying_bones}")

print("\nInspecting Elita One Mesh deformed vertices:")
eval_e = elita_mesh.evaluated_get(depsgraph)
eval_mesh_e = eval_e.to_mesh()
flying_bones_e = {}
for i, v in enumerate(eval_mesh_e.vertices):
    w_co = eval_e.matrix_world @ v.co
    vgroups = [(elita_mesh.vertex_groups[g.group].name, g.weight) for g in elita_mesh.data.vertices[i].groups]
    main_b = max(vgroups, key=lambda x: x[1])[0] if vgroups else "None"
    if (w_co.x < 1.8 and w_co.x > -1.8) or w_co.z > 8.0:
        flying_bones_e[main_b] = flying_bones_e.get(main_b, 0) + 1

print(f"Flying vertices by bone group in Elita One: {flying_bones_e}")
