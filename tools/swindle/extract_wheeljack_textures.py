import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import os
import UnityPy

bundle_path = r'extracted_apk\assets\assetpack\wheeljack_gs_mp20_odr\wheeljack_gs_mp20.assetbundle'
out_dir = r'toolchain\unity_build_project\Assets\Swindle\Wheeljack'
os.makedirs(out_dir, exist_ok=True)

env = UnityPy.load(bundle_path)

extracted = []
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        d = obj.read()
        name = getattr(d, 'name', '') or getattr(d, 'm_Name', '')
        try:
            img = d.image
            out_path = os.path.join(out_dir, f"{name}.png")
            img.save(out_path)
            extracted.append((name, img.size, img.mode))
        except Exception as e:
            print(f"Failed to export {name}: {e}")

print(f"Extracted {len(extracted)} textures to {out_dir}:")
for name, sz, mode in extracted:
    print(f"  {name} ({sz[0]}x{sz[1]}, {mode})")
