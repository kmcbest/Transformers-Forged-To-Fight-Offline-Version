import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")

arm = bpy.data.objects.get("Ironhide_Reference_Armature")
for bname in ["Hips", "Spine", "Spine1", "Neck", "Head", "Jaw"]:
    b = arm.data.bones.get(bname)
    if b:
        print(f"{bname}: Y={b.head_local.y:.3f}, Z={b.head_local.z:.3f}")

# Check facial bones if any
for b in arm.data.bones:
    if "Eye" in b.name or "Nose" in b.name or "Lip" in b.name:
        print(f"Face feature {b.name}: Y={b.head_local.y:.3f}, Z={b.head_local.z:.3f}")
