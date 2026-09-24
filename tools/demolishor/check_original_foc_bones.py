import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx")

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Demolishor_ARM")

print("Demolishor FBX mesh location:", mesh.location, mesh.matrix_world.to_translation())
print("Demolishor FBX arm location:", arm.location, arm.matrix_world.to_translation())

# Check bone positions in Demolishor_ARM
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for bname in ["C_Root_Reference_XR", "C_Spine00_Hips_XB", "C_Head02_Head_XB", "L_Arm02_Shoulder_XB", "R_Arm02_Shoulder_XB", "L_Leg01_Thigh_XB", "R_Leg01_Thigh_XB"]:
    eb = arm.data.edit_bones.get(bname)
    if eb:
        print(f"  Bone {bname:25s}: head = {eb.head}")
