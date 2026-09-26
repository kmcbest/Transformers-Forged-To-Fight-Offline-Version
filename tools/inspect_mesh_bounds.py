import UnityPy
from pathlib import Path

p = Path("extracted_apk/assets/assetpack/primordial_base_odr/primordial_base.assetbundle")
env = UnityPy.load(str(p))

for obj in env.objects:
    if obj.type.name == "Mesh":
        m = obj.read()
        if "courtyard" in m.m_Name.lower() or "metal" in m.m_Name.lower():
            aabb = getattr(m, "m_LocalAABB", None)
            if aabb:
                c = aabb.m_Center
                e = aabb.m_Extent
                print(f"Mesh {m.m_Name}: Center=({c.x:.1f}, {c.y:.1f}, {c.z:.1f}), Extent=({e.x:.1f}, {e.y:.1f}, {e.z:.1f})")
                print(f"   X: [{c.x - e.x:.1f}, {c.x + e.x:.1f}], Z: [{c.z - e.z:.1f}, {c.z + e.z:.1f}]")
