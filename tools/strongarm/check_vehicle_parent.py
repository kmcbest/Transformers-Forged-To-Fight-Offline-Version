import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, 'm_Name', '')
        if name == "cha_prowl_gs_deluxe2016_01":
            print(f"Mesh GameObject: {name}")
            for comp in getattr(data, 'm_Components', []):
                c = comp.read()
                if type(c).__name__ == "Transform":
                    p_ptr = getattr(c, 'm_Father', None)
                    if p_ptr:
                        p_tr = p_ptr.read()
                        p_go = getattr(p_tr, 'm_GameObject', None).read()
                        print(f"  Parent: {p_go.m_Name}")
                        gp_ptr = getattr(p_tr, 'm_Father', None)
                        if gp_ptr:
                            gp_tr = gp_ptr.read()
                            gp_go = getattr(gp_tr, 'm_GameObject', None).read()
                            print(f"  Grandparent: {gp_go.m_Name}")
                            ggp_ptr = getattr(gp_tr, 'm_Father', None)
                            if ggp_ptr:
                                ggp_tr = ggp_ptr.read()
                                ggp_go = getattr(ggp_tr, 'm_GameObject', None).read()
                                print(f"  Great-grandparent: {ggp_go.m_Name}")
