import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
OUT_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "Megatron"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== Extracting Megatron textures to {OUT_DIR} ===")
env = UnityPy.load(str(MEG_BUNDLE))

for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        nm = getattr(data, "m_Name", getattr(data, "name", f"tex_{obj.path_id}"))
        try:
            img = data.image
            out_p = OUT_DIR / f"{nm}.png"
            img.save(out_p)
            print(f"  [✓] Saved Texture2D '{nm}' ({img.size[0]}x{img.size[1]}) -> {out_p.name}")
        except Exception as e:
            print(f"  [!] Failed to save Texture2D '{nm}': {e}")
