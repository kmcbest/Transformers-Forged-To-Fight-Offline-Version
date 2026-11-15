import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(bundle))
obj_map = {o.path_id: o for o in env.objects}

clip = obj_map[-1178808270879590806].read_typetree()
print("Clip name:", clip.get("m_Name"))
print("Clip m_MuscleClip:")
mc = clip.get("m_MuscleClip", {})
print("  m_StartTime:", mc.get("m_StartTime"))
print("  m_StopTime:", mc.get("m_StopTime"))
print("  m_ClipBindingConstant:")
bind = clip.get("m_ClipBindingConstant", {})
for b in bind.get("genericBindings", []):
    print("    binding: pathHash=", b.get("path"), "attribute=", b.get("attribute"), "typeID=", b.get("typeID"), "classID=", b.get("classID"))
