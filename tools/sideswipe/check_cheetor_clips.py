import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
env_ch = UnityPy.load(str(ROOT / "extracted_apk" / "assets" / "assetpack" / "cheetor_bw_transmetal_odr" / "cheetor_bw_transmetal.assetbundle"))
sf_ch = list(env_ch.assets)[0]

for pid in (-1929738649458782990, 868105726138923071):
    obj = sf_ch.objects[pid]
    tt = obj.read_typetree()
    print(f"Clip {pid}: name={tt.get('m_Name')}, class={obj.class_id}")
