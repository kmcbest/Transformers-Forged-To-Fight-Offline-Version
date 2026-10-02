import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if name == "TeamSelect_Agile_idle":
            print(f"=== Clip: {name} ===")
            cbc = data.m_ClipBindingConstant
            print(f"GenericBindings count: {len(cbc.genericBindings)}")
            for b in cbc.genericBindings[:15]:
                print(f"  path={b.path}, attribute={b.attribute}, typeID={b.typeID}, isPPtrCurve={b.isPPtrCurve}")
            if hasattr(data, 'm_AnimationType'):
                print(f"  AnimationType: {data.m_AnimationType}")
            break
