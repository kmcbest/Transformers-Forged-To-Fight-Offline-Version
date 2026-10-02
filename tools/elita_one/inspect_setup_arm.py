import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_setup.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("Arcee_Armature")
if arm:
    print(f"Arcee_Armature bones count: {len(arm.data.bones)}")
    for b in list(arm.data.bones)[:10]:
        print(f"  {b.name}: head={b.head_local}")
