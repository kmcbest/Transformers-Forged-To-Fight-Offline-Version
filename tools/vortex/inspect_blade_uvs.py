import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

blade = bpy.data.objects.get("WEP_IonBlade_SKEL.mo_L.dmx")
if blade and blade.data.uv_layers.active:
    uv_layer = blade.data.uv_layers.active.data
    uvs = [d.uv for d in uv_layer]
    min_u = min(u[0] for u in uvs)
    max_u = max(u[0] for u in uvs)
    min_v = min(u[1] for u in uvs)
    max_v = max(u[1] for u in uvs)
    print(f"Blade UV bounding range: U=[{min_u:.3f}, {max_u:.3f}], V=[{min_v:.3f}, {max_v:.3f}]")
