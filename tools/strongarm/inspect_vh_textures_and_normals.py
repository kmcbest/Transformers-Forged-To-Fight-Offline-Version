import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from pathlib import Path
from PIL import Image
import UnityPy

SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

# 1. List RID_game/strongarm_extracted files
ext_dir = Path(r"E:\Agent\RID_game\strongarm_extracted")
print("=== strongarm_extracted files ===")
for p in sorted(ext_dir.rglob("*")):
    if p.is_file():
        print(" ", p, p.stat().st_size)

# 2. Check RAOE bottom-right quadrant and NM channels in bundle
raoe = np.array(Image.open(SCRATCH / "bundle_tform_misc_RAOE.png").convert("RGBA"))
# Bottom-right in Unity UV (u in [0.75, 1.0], v in [0.0, 0.25]) -> PIL y in [0.75*H, H], x in [0.75*W, W]!
H, W, _ = raoe.shape
q_br = raoe[int(H*0.75):H, int(W*0.75):W]
Image.fromarray(q_br).save(SCRATCH / "bundle_vh_RAOE_quad.png")
print("\n=== Bundle Vehicle RAOE Quadrant [x:0.75..1, y(PIL):0.75..1] ===")
for i, ch in enumerate(["R(Rough)", "G(AO)", "B(Emissive)", "A"]):
    print(f"  {ch}: min={q_br[:,:,i].min()}, max={q_br[:,:,i].max()}, mean={q_br[:,:,i].mean():.2f}")

# Check NM in bundle (tform_misc_NM -> 2048x2048)
nm = np.array(Image.open(SCRATCH / "bundle_tform_misc_NM_check.png").convert("RGBA"))
print("\n=== Bundle Vehicle NM (tform_misc_NM) ===")
for i, ch in enumerate(["R(Nx)", "G(Ny)", "B(Metallic)", "A(Unity_AG_or_1)"]):
    print(f"  {ch}: min={nm[:,:,i].min()}, max={nm[:,:,i].max()}, mean={nm[:,:,i].mean():.2f}")

# Check Prowl's official RAOE and NM for comparison
prowl_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"
env_p = UnityPy.load(prowl_path)
print("\n=== Official Prowl RAOE & NM stats ===")
for o in env_p.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        if any(k in t.m_Name.lower() for k in ("raoe", "_nm", "tform_misc")):
            arr = np.array(t.image.convert("RGBA"))
            stats = [(ch, int(arr[:,:,i].min()), int(arr[:,:,i].max()), round(float(arr[:,:,i].mean()),1)) for i, ch in enumerate(["R","G","B","A"])]
            print(f"  Tex {o.path_id} {t.m_Name} ({t.m_Width}x{t.m_Height}) fmt={t.m_TextureFormat}: {stats}")

# 3. Inspect Strongarm's m_MuscleClip structure inside AnimationClip
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        if ct.get("m_Name") == "frontend_Prowl_levelup_vehicle_idle_transformed":
            print("\n=== Clip structure keys ===")
            mc = ct["m_MuscleClip"]
            print("m_MuscleClip keys:", list(mc.keys()))
            clip = mc["m_Clip"]
            print("m_Clip keys:", list(clip.keys()))
            if "data" in clip:
                print("m_Clip['data'] keys:", list(clip["data"].keys()))
                d = clip["data"]
                print("  streamed:", d.get("m_StreamedClip", {}).get("curveCount"),
                      "dense:", d.get("m_DenseClip", {}).get("m_CurveCount"),
                      "const len:", len(d.get("m_ConstantClip", {}).get("data", [])))
            break

# 4. Also check vehicle mesh normals / tangents / degenerate triangles
env_s = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")
for o in env_s.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        mt = o.read_typetree()
        vc = mt["m_VertexData"]["m_VertexCount"]
        data = bytes(mt["m_VertexData"]["m_DataSize"])
        # stream 0 stride 40: pos(0..12), norm(12..24), tan(24..40)
        v_raw = np.frombuffer(data[:vc*40], dtype="<f4").reshape(vc, 10)
        pos = v_raw[:, 0:3]
        nrm = v_raw[:, 3:6]
        tan = v_raw[:, 6:10]
        nrm_len = np.linalg.norm(nrm, axis=1)
        tan_len = np.linalg.norm(tan[:, :3], axis=1)
        print(f"\n=== Strongarm Vehicle Mesh Normals & Tangents ===")
        print(f"  Normal len: min={nrm_len.min():.4f}, max={nrm_len.max():.4f}")
        print(f"  Tangent xyz len: min={tan_len.min():.4f}, max={tan_len.max():.4f}, w unique={np.unique(tan[:,3])}")
        # Check roof vertices (top height in Unity is Y): where is Y > 2.2?
        top = pos[:, 1] > 2.2
        print(f"  Roof verts Y>2.2 count={top.sum()}, Y range=[{pos[top,1].min():.3f}, {pos[top,1].max():.3f}]")
        very_top = pos[:, 1] > 2.45
        print(f"  Very top (lightbar) verts Y>2.45 count={very_top.sum()}, X=[{pos[very_top,0].min():.3f}, {pos[very_top,0].max():.3f}], Z=[{pos[very_top,2].min():.3f}, {pos[very_top,2].max():.3f}]")
        break
