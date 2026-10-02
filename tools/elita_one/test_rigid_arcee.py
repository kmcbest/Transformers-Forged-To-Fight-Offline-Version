import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arcee_mesh = bpy.data.objects.get("Arcee_Mesh")
arcee_arm = bpy.data.objects.get("Arcee_Armature")

# Reset arm and mesh to origin in rest pose to calculate bone segments
arcee_arm.location = (0, 0, 0)
arcee_mesh.location = (0, 0, 0)
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

# Clear animation temporarily for rest binding
act = arcee_arm.animation_data.action if arcee_arm.animation_data else None
arcee_arm.animation_data_clear()
bpy.context.view_layer.update()

bone_segments = {}
for b in arcee_arm.pose.bones:
    h = arcee_arm.matrix_world @ b.head
    t = arcee_arm.matrix_world @ b.tail
    bone_segments[b.name] = (h, t)

def point_to_segment_dist(p, a, b):
    ab = b - a
    ab_len_sq = ab.length_squared
    if ab_len_sq < 1e-6:
        return (p - a).length
    proj_t = max(0.0, min(1.0, (p - a).dot(ab) / ab_len_sq))
    proj = a + proj_t * ab
    return (p - proj).length

bpy.ops.object.select_all(action='DESELECT')
arcee_mesh.select_set(True)
bpy.context.view_layer.objects.active = arcee_mesh
bpy.ops.mesh.separate(type='LOOSE')
parts = [o for o in bpy.context.selected_objects if o.type == 'MESH']
print(f"Arcee has {len(parts)} mechanical parts.")

for p in parts:
    coords = [p.matrix_world @ v.co for v in p.data.vertices]
    centroid = sum(coords, mathutils.Vector()) / len(coords)
    cx = centroid.x
    best_bone = "Hips"
    min_dist = float('inf')
    for bname, (h, t) in bone_segments.items():
        if "Left" in bname and cx > 0.1: continue
        if "Right" in bname and cx < -0.1: continue
        d = point_to_segment_dist(centroid, h, t)
        if d < min_dist:
            min_dist = d
            best_bone = bname
    p.vertex_groups.clear()
    vg = p.vertex_groups.new(name=best_bone)
    vg.add(list(range(len(p.data.vertices))), 1.0, 'REPLACE')

bpy.ops.object.select_all(action='DESELECT')
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
arcee_mesh = bpy.context.active_object
arcee_mesh.name = "Arcee_Mesh"
arcee_mesh.parent = arcee_arm

# Re-enable animation
if act:
    arcee_arm.animation_data_create()
    arcee_arm.animation_data.action = act

arcee_arm.location = (2.6, 0, 0)
bpy.context.view_layer.update()

# Render frame 0 test
out_path = r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce\preview_rigid_arcee_frame00.png"
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
bpy.context.scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print(f"Rendered test to {out_path}")
