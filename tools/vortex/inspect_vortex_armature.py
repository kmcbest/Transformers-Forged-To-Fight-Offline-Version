import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Vortex_ARM")
if arm:
    print(f"Vortex_ARM found! Location: {arm.location}, Scale: {arm.scale}")
    print(f"Bones count: {len(arm.data.bones)}")
    # Print root bones and key bone names
    for b in arm.data.bones:
        if not b.parent:
            print(f"  Root bone: {b.name}")
    print("\nSample bones:")
    key_bones = ["pelvis", "spine", "head", "clavicle", "upperarm", "forearm", "hand", "thigh", "calf", "foot", "blade", "rotor"]
    for b in arm.data.bones:
        for k in key_bones:
            if k in b.name.lower():
                print(f"    {b.name:30s} (head: {b.head.x:.2f}, {b.head.y:.2f}, {b.head.z:.2f})")
                break

vh_arm = bpy.data.objects.get("Vortex_VH_ARM")
if vh_arm:
    print(f"\nVortex_VH_ARM found! Bones: {len(vh_arm.data.bones)}")
    for b in vh_arm.data.bones[:15]:
        print(f"    {b.name:30s} (head: {b.head.x:.2f}, {b.head.y:.2f}, {b.head.z:.2f})")
