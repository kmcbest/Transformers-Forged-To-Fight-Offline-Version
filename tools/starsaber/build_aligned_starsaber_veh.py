import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
import json
import math
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [StarSaber] Stage 2 Master Vehicle Pipeline (Vehicle Pose -> Jetfire Tank Mesh) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models" / "StarSaber" / "source" / "StarSaber.fbx"
DONOR_REF_DIR = ROOT / "3rd-party-models" / "StarSaber" / "00_donor_reference"
OUT_FBX_DIR = ROOT / "3rd-party-models" / "StarSaber" / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "StarSaber"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

JETFIRE_29_VEH_BONES = [
    "chop1_torso_backpack_outer_center",
    "chop1_torso_back_center",
    "chop1_torso_backpack_inner_center",
    "chop1_main_center_hidden",
    "chop1_wing_right",
    "chop1_wpns_arm_right",
    "chop1_wpns_leg_right",
    "chop1_wings_rear_right",
    "chop1_wings_upper_right",
    "chop1_wpns_cannon_left",
    "chop1_wing_left",
    "chop1_wpns_arm_left",
    "chop1_wpns_leg_left",
    "chop1_wings_rear_left",
    "chop1_wings_upper_left",
    "chop1_wpns_cannon_right",
    "chop2_arm_upper_left",
    "chop2_forearm_left",
    "chop2_arm_upper_right",
    "chop2_forearm_right",
    "chop2_hip_center",
    "chop2_torso_center",
    "chop2_head_center",
    "chop2_leg_upper_left",
    "chop2_leg_lower_left",
    "chop2_foot_left",
    "chop2_leg_upper_right",
    "chop2_leg_lower_right",
    "chop2_foot_right",
]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    print("[*] Importing StarSaber.fbx for vehicle extraction...")
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
    
    arm = bpy.data.objects.get("Bip001")
    mesh = bpy.data.objects.get("StarSaber.001")
    assert arm and mesh, "Missing Bip001 or StarSaber.001!"
    
    veh_act = bpy.data.actions.get("Bip001|vehicle_idle01_Garage|Base Layer")
    if not veh_act:
        for act in bpy.data.actions:
            if "vehicle" in act.name and "Bip001" in act.name:
                veh_act = act
                break
                
    print(f"[*] Applying vehicle action: {veh_act.name if veh_act else 'None'}")
    if veh_act and arm.animation_data:
        arm.animation_data.action = veh_act
        bpy.context.scene.frame_set(1)
        bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_mesh_obj = mesh.evaluated_get(depsgraph)
    baked_mesh_data = eval_mesh_obj.to_mesh()
    
    veh_obj = bpy.data.objects.new("cha_starsaber_veh", baked_mesh_data.copy())
    bpy.context.scene.collection.objects.link(veh_obj)
    
    for o in list(bpy.data.objects):
        if o != veh_obj:
            bpy.data.objects.remove(o, do_unlink=True)
            
    print(f"[✓] Extracted standalone vehicle mesh: {veh_obj.name}")
    
    vs = [v.co for v in veh_obj.data.vertices]
    xs = [v.x for v in vs]
    ys = [v.y for v in vs]
    zs = [v.z for v in vs]
    raw_len = max(zs) - min(zs)
    raw_span = max(xs) - min(xs)
    raw_h = max(ys) - min(ys)
    print(f"[*] Raw vehicle bounds:")
    print(f"    X (wingspan): [{min(xs):.3f}, {max(xs):.3f}] (span: {raw_span:.3f})")
    print(f"    Y (height):   [{min(ys):.3f}, {max(ys):.3f}] (span: {raw_h:.3f})")
    print(f"    Z (length):   [{min(zs):.3f}, {max(zs):.3f}] (span: {raw_len:.3f})")
    
    # Target length ~11.33m matching Jetfire vehicle
    SCALE_VEH = 11.33 / raw_len
    print(f"[*] Applying vehicle scale factor: {SCALE_VEH:.4f}")
    scale_mat = Matrix.Scale(SCALE_VEH, 4)
    veh_obj.data.transform(scale_mat)
    veh_obj.data.update()
    
    # Ground at Z=0 and center X
    new_vs = [v.co for v in veh_obj.data.vertices]
    min_x, max_x = min(v.x for v in new_vs), max(v.x for v in new_vs)
    min_y, max_y = min(v.y for v in new_vs), max(v.y for v in new_vs)
    min_z, max_z = min(v.z for v in new_vs), max(v.z for v in new_vs)
    
    center_x = (max_x + min_x) / 2
    ground_mat = Matrix.Translation(Vector((-center_x, 0.0, -min_z)))
    veh_obj.data.transform(ground_mat)
    veh_obj.data.update()
    
    fin_vs = [v.co for v in veh_obj.data.vertices]
    print(f"[✓] Final vehicle bounds:")
    print(f"    X (wingspan): [{min(v.x for v in fin_vs):.3f}, {max(v.x for v in fin_vs):.3f}] (span: {max(v.x for v in fin_vs)-min(v.x for v in fin_vs):.3f})")
    print(f"    Y (height):   [{min(v.y for v in fin_vs):.3f}, {max(v.y for v in fin_vs):.3f}] (span: {max(v.y for v in fin_vs)-min(v.y for v in fin_vs):.3f})")
    print(f"    Z (length):   [{min(v.z for v in fin_vs):.3f}, {max(v.z for v in fin_vs):.3f}] (span: {max(v.z for v in fin_vs)-min(v.z for v in fin_vs):.3f})")
    
    # Create Jetfire 29 Vehicle Armature
    print("[*] Creating 29-bone Jetfire Vehicle Armature...")
    arm_data = bpy.data.armatures.new("cha_jetfire_gs_leader2014_01_arm")
    arm_obj = bpy.data.objects.new("cha_jetfire_gs_leader2014_01_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    root_bone = arm_data.edit_bones.new(JETFIRE_29_VEH_BONES[0])
    root_bone.head = Vector((0.0, 0.0, 1.0))
    root_bone.tail = Vector((0.0, 0.0, 2.0))
    
    for bn in JETFIRE_29_VEH_BONES[1:]:
        b = arm_data.edit_bones.new(bn)
        b.head = Vector((0.0, 0.0, 1.0))
        b.tail = Vector((0.0, 0.0, 1.5))
        b.parent = root_bone
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Assign all vertices to root vehicle bone
    veh_obj.vertex_groups.clear()
    for bn in JETFIRE_29_VEH_BONES:
        vg = veh_obj.vertex_groups.new(name=bn)
        if bn == JETFIRE_29_VEH_BONES[0]:
            vg.add(list(range(len(veh_obj.data.vertices))), 1.0, 'REPLACE')
            
    # Explicit material setup
    veh_obj.data.materials.clear()
    mat_main = bpy.data.materials.new(name="cha_starsaber_main")
    veh_obj.data.materials.append(mat_main)

    veh_obj.parent = arm_obj
    mod = veh_obj.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj
    
    # Export tank/vehicle FBX
    for out_fbx in (OUT_FBX_DIR / "starsaber_veh_prepared.fbx", UNITY_DIR / "starsaber_veh_prepared.fbx"):
        print(f"[*] Exporting prepared vehicle FBX to {out_fbx}...")
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        veh_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        
        bpy.ops.export_scene.fbx(
            filepath=str(out_fbx),
            use_selection=True,
            use_active_collection=False,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=False,
            object_types={'ARMATURE', 'MESH'},
            use_mesh_modifiers=True,
            mesh_smooth_type='FACE',
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            axis_forward='-Z',
            axis_up='Y',
            armature_nodetype='NULL',
            bake_anim=False
        )
    print(f"[✓] Exported {out_fbx} successfully!")


if __name__ == "__main__":
    main()
