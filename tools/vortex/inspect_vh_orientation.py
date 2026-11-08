import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_grindor = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\Grindor\cha_grindor_official_01.asset")
p_vortex = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\cha_vortex_vh_grafted.asset")

print("--- Grindor 01 Mesh ---")
if p_grindor.exists():
    env = UnityPy.load(str(p_grindor))
    for obj in env.objects:
        if obj.type.name == "Mesh":
            m = obj.read()
            print(f"Name: {m.m_Name}")
            print(f"Vertex count: {len(m.m_Vertices)}")
            xs = [v[0] for v in m.m_Vertices]
            ys = [v[1] for v in m.m_Vertices]
            zs = [v[2] for v in m.m_Vertices]
            print(f"X: [{min(xs):.3f}, {max(xs):.3f}] span={max(xs)-min(xs):.3f}")
            print(f"Y: [{min(ys):.3f}, {max(ys):.3f}] span={max(ys)-min(ys):.3f}")
            print(f"Z: [{min(zs):.3f}, {max(zs):.3f}] span={max(zs)-min(zs):.3f}")
            print(f"Bindposes count: {len(m.m_BindPose)}")

print("\n--- Vortex Vh Grafted Mesh ---")
if p_vortex.exists():
    env = UnityPy.load(str(p_vortex))
    for obj in env.objects:
        if obj.type.name == "Mesh":
            m = obj.read()
            print(f"Name: {m.m_Name}")
            print(f"Vertex count: {len(m.m_Vertices)}")
            xs = [v[0] for v in m.m_Vertices]
            ys = [v[1] for v in m.m_Vertices]
            zs = [v[2] for v in m.m_Vertices]
            print(f"X: [{min(xs):.3f}, {max(xs):.3f}] span={max(xs)-min(xs):.3f}")
            print(f"Y: [{min(ys):.3f}, {max(ys):.3f}] span={max(ys)-min(ys):.3f}")
            print(f"Z: [{min(zs):.3f}, {max(zs):.3f}] span={max(zs)-min(zs):.3f}")
            print(f"Bindposes count: {len(m.m_BindPose)}")
            if len(m.m_Skin) > 0:
                print(f"Skin sample (first 3): {m.m_Skin[:3]}")
