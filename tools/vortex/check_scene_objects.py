import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

scene_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Vortex_Inspection.unity"
env = UnityPy.load(scene_path)

print("=== Objects in Vortex_Inspection.unity ===")
for obj in env.objects:
    if obj.type.name in ["GameObject", "Transform"]:
        data = obj.read()
        name = getattr(data, 'm_Name', getattr(data, 'name', 'unnamed'))
        if any(k in name.lower() for k in ["grindor", "vortex", "camera"]):
            print(f"[{obj.type.name}] {name}")
    elif obj.type.name == "SkinnedMeshRenderer":
        data = obj.read()
        go_name = "unknown"
        if hasattr(data, 'm_GameObject') and data.m_GameObject:
            try:
                go = data.m_GameObject.read()
                go_name = go.m_Name
            except:
                pass
        print(f"[SkinnedMeshRenderer] on GameObject '{go_name}', m_Enabled={getattr(data, 'm_Enabled', 'unknown')}")
