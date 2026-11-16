import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "GameObject":
        d = obj.read()
        name = getattr(d, 'm_Name', '')
        if "01" in name or "trans" in name.lower():
            # Check transform
            for c in d.m_Components:
                comp = c.read()
                if "Transform" in type(comp).__name__:
                    rot = comp.m_LocalRotation
                    pos = comp.m_LocalPosition
                    scale = comp.m_LocalScale
                    pname = comp.m_Father.read().m_GameObject.read().m_Name if comp.m_Father else "None"
                    print(f"GO: {name:25s} Parent={pname:20s} LocalPos=({pos.x:.2f},{pos.y:.2f},{pos.z:.2f}) LocalRot=({rot.x:.3f},{rot.y:.3f},{rot.z:.3f},{rot.w:.3f})")
