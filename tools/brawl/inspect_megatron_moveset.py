import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

meg_bundle = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(meg_bundle)

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tt = obj.read_typetree()
        if "m_MoveMap" in tt or "Base" in str(tt):
            print(f"Found MoveSet PID={obj.path_id}")
            # Print keys or entries in MoveSet
            for k, v in tt.items():
                if "move" in k.lower() or "attack" in k.lower() or k == "Base":
                    print(f"  {k} -> {v}")
