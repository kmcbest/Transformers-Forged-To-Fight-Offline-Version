import UnityPy

env = UnityPy.load(r"d:\Agent\tftf\toolchain\unity_build_project\AssetBundles\demolishor_mesh.assetbundle")

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        vertices = mesh.m_Vertices
        print(f"Total vertices: {len(vertices)}")
        if vertices:
            xs = [v.x for v in vertices]
            ys = [v.y for v in vertices]
            zs = [v.z for v in vertices]
            print(f"X range: {min(xs):.4f} to {max(xs):.4f}")
            print(f"Y range: {min(ys):.4f} to {max(ys):.4f}")
            print(f"Z range: {min(zs):.4f} to {max(zs):.4f}")
