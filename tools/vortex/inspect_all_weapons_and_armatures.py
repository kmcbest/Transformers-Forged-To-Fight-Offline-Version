import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

print("--- All Armatures ---")
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        print(f"  Armature: {obj.name} (bones: {len(obj.data.bones)})")

print("\n--- All Weapon/Blade Meshes ---")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        nl = obj.name.lower()
        if "wep" in nl or "blade" in nl or "gun" in nl or "missile" in nl:
            print(f"  Mesh: {obj.name:35s} | Mats: {[m.name for m in obj.data.materials]}")
