import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
env_d = UnityPy.load(str(donor_path))
sf = list(env_d.files.values())[0] if not hasattr(list(env_d.files.values())[0], 'files') else list(list(env_d.files.values())[0].files.values())[0]

mat = sf.objects[2758279787216392959].read_typetree()
print("Robot Mat Shader:", mat.get("m_Shader"))
envs = mat.get("m_SavedProperties", {}).get("m_TexEnvs", [])
print("Robot Mat TexEnvs:")
for k, v in envs:
    print(f"  {k} -> {v.get('m_Texture', {})}")

mat_v = sf.objects[-8143696719442631496].read_typetree()
print("\nVehicle Mat TexEnvs:")
for k, v in mat_v.get("m_SavedProperties", {}).get("m_TexEnvs", []):
    print(f"  {k} -> {v.get('m_Texture', {})}")
