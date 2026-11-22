import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

bundle_path = r'extracted_apk\assets\assetpack\wheeljack_gs_mp20_odr\wheeljack_gs_mp20.assetbundle'
env = UnityPy.load(bundle_path)

print("=== Wheeljack Bundle PIDs ===")

for obj in env.objects:
    t = obj.type.name
    pid = obj.path_id
    try:
        d = obj.read()
        name = getattr(d, 'name', '') or getattr(d, 'm_Name', '')
    except:
        name = 'unreadable'

    if t in ('Mesh', 'Texture2D', 'Material'):
        print(f"[{t}] {name} -> PathID: {pid}")
    elif t == 'GameObject' and ('wheeljack' in name.lower() or 'cha_' in name.lower()):
        print(f"[{t}] {name} -> PathID: {pid}")

print("\n=== Container ===")
for k, v in env.container.items():
    print(f"  {k} -> PathID: {v.path_id}")
