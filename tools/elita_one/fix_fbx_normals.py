import bpy
from pathlib import Path
import mathutils

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
out_fbx = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

print(f"=== Fixing Normals and Face Orientations for Elita One ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not mesh_objs:
    print("Error: No mesh found!")
    exit(1)

mesh_obj = mesh_objs[0]
bpy.context.view_layer.objects.active = mesh_obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')

# 1. Recalculate normals outside
print("[*] Recalculating normals outside...")
bpy.ops.mesh.normals_make_consistent(inside=False)

# 2. Back to object mode to check
bpy.ops.object.mode_set(mode='OBJECT')
mesh = mesh_obj.data
mesh.calc_normals()

# Validate
inward_count = 0
center = sum((v.co for v in mesh.vertices), mathutils.Vector()) / len(mesh.vertices)
for p in mesh.polygons:
    v_out = (p.center - center).normalized()
    if p.normal.dot(v_out) < -0.3:
        inward_count += 1

print(f"[+] After fix: likely inward-facing polygons: {inward_count} / {len(mesh.polygons)} ({inward_count/len(mesh.polygons)*100:.2f}%)")

# Export back to FBX
arm_objs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
if arm_objs:
    bpy.ops.export_scene.fbx(
        filepath=out_fbx,
        check_existing=False,
        use_selection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE',
        bake_space_transform=False,
        object_types={'ARMATURE', 'MESH'},
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        use_subsurf=False,
        use_armature_deform_only=True,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        axis_forward='-Z',
        axis_up='Y'
    )
    print(f"[✓] Successfully re-exported fixed FBX to {out_fbx}")
