import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(p))
ab = [o for o in env.objects if o.type.name == "AssetBundle"][0]
tt = ab.read_typetree()
print("Original m_Name:", tt["m_Name"])
print("Original container:", tt["m_Container"][0][0])
tt["m_Name"] = "data/swoop_gs_deluxe2008_odr/swoop_gs_deluxe2008.assetbundle"
new_c = []
for k, v in tt["m_Container"]:
    new_c.append([k.replace("ramjet", "swoop"), v])
tt["m_Container"] = new_c
ab.save_typetree(tt)

# Now read again
tt2 = ab.read_typetree()
print("Read again m_Name:", tt2["m_Name"])
print("Read again container:", tt2["m_Container"][0][0])
