import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

# 1. Check blitzwing_mesh.assetbundle actual m_LocalAABB & m_BindPose
mb = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
e = UnityPy.load(str(mb))
print("=== blitzwing_mesh.assetbundle contents ===")
for o in e.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        c = tt["m_LocalAABB"]["m_Center"]
        ex = tt["m_LocalAABB"]["m_Extent"]
        bp0 = tt["m_BindPose"][0] if tt["m_BindPose"] else {}
        print(f"  {tt['m_Name']}: verts={tt['m_VertexData']['m_VertexCount']} center=({c['x']:.4f},{c['y']:.4f},{c['z']:.4f}) ext=({ex['x']:.4f},{ex['y']:.4f},{ex['z']:.4f}) bp0={[round(bp0[k],3) for k in ('e00','e01','e02','e03','e10','e11','e12','e13','e20','e21','e22','e23')] if bp0 else None}")

# 2. Inspect Mixmaster projectile_special_bullet & Sideswipe projectile_sideswipe_missile MoveSet + PrefabList
ROOT_GM = Path(r"E:\Agent\TFTF")
for nm, rel, proj_name in [
    ("MIXMASTER", "extracted_apk/assets/assetpack/mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle", "projectile_special_bullet"),
    ("SIDESWIPE", "extracted_apk/assets/assetpack/sideswipe_gs_deluxe2014_odr/sideswipe_gs_deluxe2014.assetbundle", "projectile_sideswipe_missile"),
]:
    p = ROOT_GM / rel
    if not p.exists():
        p = next((ROOT_GM / "extracted_apk/assets/assetpack").glob(f"*{nm.lower()}*/*.assetbundle"))
    env = UnityPy.load(str(p))
    objs = {o.path_id: o for o in env.objects}
    print(f"\n=== {nm} -> {proj_name} ===")
    for o in env.objects:
        if o.type.name == "GameObject":
            go = o.read_typetree()
            if go["m_Name"] == proj_name:
                for c in go["m_Component"]:
                    cp = c["component"]["m_PathID"]
                    if objs[cp].type.name == "MonoBehaviour":
                        tt = objs[cp].read_typetree()
                        print("  Comp keys:", [k for k in tt.keys() if not k.startswith("m_")])
                        if "_moves" in tt:
                            print("   _moves:", tt["_moves"])
                        if "_prefabs" in tt:
                            print("   _prefabs:", tt["_prefabs"])
                        if "Speed" in tt or "Radius" in tt or "CollisionPointOffset" in tt:
                            print("   cfg:", {k: v for k, v in tt.items() if k in ("Speed", "Radius", "CollisionPointOffset", "Gravity", "MaxLifeTime", "ImpactPrefabName")})
