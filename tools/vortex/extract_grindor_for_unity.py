import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
GRINDOR_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
OUT_GRINDOR_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Vortex" / "Grindor"
OUT_GRINDOR_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== 1. LOADING {GRINDOR_BUNDLE} ===")
env = UnityPy.load(str(GRINDOR_BUNDLE))

id_to_obj = {o.path_id: o for o in env.objects}

def get_name(o):
    try:
        d = o.read()
        return getattr(d, "m_Name", getattr(d, "name", ""))
    except Exception:
        try:
            t = o.read_typetree()
            return t.get("m_Name", "")
        except Exception:
            return ""

print("\n=== 2. EXTRACTING GRINDOR REFERENCE TEXTURES ===")
for o in env.objects:
    if o.type.name == "Texture2D":
        data = o.read()
        nm = getattr(data, "m_Name", getattr(data, "name", f"tex_{o.path_id}"))
        try:
            img = data.image
            out_p = OUT_GRINDOR_DIR / f"{nm}.png"
            img.save(out_p)
            print(f"  [OK] Saved Texture: {nm}.png ({img.size})")
        except Exception as e:
            print(f"  [WARN] Failed to export Texture {nm}: {e}")

print("\n=== 3. EXPORTING GRINDOR REFERENCE MESHES (OBJ) ===")
for o in env.objects:
    if o.type.name == "Mesh":
        d = o.read()
        nm = getattr(d, "m_Name", getattr(d, "name", f"mesh_{o.path_id}"))
        try:
            obj_data = d.export()
            if isinstance(obj_data, str) and len(obj_data) > 0:
                out_p = OUT_GRINDOR_DIR / f"{nm}.obj"
                with open(out_p, "w", encoding="utf-8") as f:
                    f.write(obj_data)
                print(f"  [OK] Saved Mesh OBJ: {nm}.obj ({len(obj_data)} chars)")
        except Exception as e:
            print(f"  [WARN] Failed to export Mesh {nm}: {e}")

print("\n[SUCCESS] Grindor reference extraction complete!")
