import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

MEG_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(MEG_BUNDLE))

for o in env.objects:
    if o.type.name == "Avatar":
        tt = o.read_typetree()
        print(f"Avatar: {tt.get('m_Name')}")
        tos = tt.get('m_TOS', {})
        print(f"  TOS count: {len(tos)}")
        avatar = tt.get('m_Avatar', {})
        avatar_bones = avatar.get('m_Bones', [])
        print(f"  m_Bones count: {len(avatar_bones)}")
        human = tt.get('m_Human', {})
        human_bones = human.get('m_Bones', [])
        print(f"  m_Human bones count: {len(human_bones)}")
        if human_bones:
            print("  This is a HUMANOID avatar!")
        else:
            print("  This is a GENERIC avatar!")
