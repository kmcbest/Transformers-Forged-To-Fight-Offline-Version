import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

# Check all redeco bundles and inspect their GameObjects and Transforms
for p in (ROOT / "assets_redeco").glob("*.assetbundle"):
    try:
        env = UnityPy.load(str(p))
        root_gos = []
        for o in env.objects:
            if o.type.name == "GameObject":
                tt = o.read_typetree()
                # If root (no parent)
                root_gos.append((o.path_id, tt.get("m_Name")))
        
        # Check Transform scale of root and children
        transforms_with_scale = []
        for o in env.objects:
            if o.type.name == "Transform":
                tt = o.read_typetree()
                ls = tt.get("m_LocalScale")
                if ls and (abs(ls["x"] - 1.0) > 0.01 or abs(ls["y"] - 1.0) > 0.01 or abs(ls["z"] - 1.0) > 0.01):
                    transforms_with_scale.append((o.path_id, ls))
                    
        mesh_h = []
        for o in env.objects:
            if o.type.name == "Mesh":
                tt = o.read_typetree()
                aabb = tt.get("m_LocalAABB", {})
                c = aabb.get("m_Center", {})
                e = aabb.get("m_Extent", {})
                if c and e:
                    mesh_h.append((tt.get("m_Name"), round(2*e["y"], 3)))

        print(f"Bundle {p.name:30s}: meshes={mesh_h}, scaled_transforms={len(transforms_with_scale)}")
        if transforms_with_scale:
            print(f"   Scaled transforms: {transforms_with_scale[:3]}")
    except Exception as e:
        pass
