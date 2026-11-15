import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r'E:\Agent\TFTF-blender\toolchain\megatron_anims_registered.assetbundle'
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == 'AnimationClip':
        data = obj.read()
        name = getattr(data, 'm_Name', 'clip')
        if name == 'brawler_normal_idle':
            print(f"Clip: {name}")
            # Look at constant clip data or muscle clip data
            mc = data.m_MuscleClip
            print(f"MuscleClip: curveCount={mc.m_Clip.data.m_DenseClip.m_CurveCount}, frameCount={mc.m_Clip.data.m_DenseClip.m_FrameCount}")
            if hasattr(mc, 'm_ClipBindingConstant'):
                cbc = mc.m_ClipBindingConstant
                print(f"GenericBindings count: {len(cbc.genericBindings)}")
                for i, b in enumerate(cbc.genericBindings):
                    print(f"  [{i}] path={b.path}, attribute={b.attribute}, typeID={b.typeID}")
