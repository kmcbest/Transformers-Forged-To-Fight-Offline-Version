import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")

env = UnityPy.load(str(BUNDLE_PATH))
sf = list(env.assets)[0]

for obj in sf.objects.values():
    if obj.type.name == "MonoBehaviour":
        try:
            tt = obj.read_typetree()
        except Exception as e:
            print(f"Failed MB PID: {obj.path_id}, type_id: {obj.type_id}, error: {e}")
            # print serialized type info
            st = sf.types[obj.type_id]
            print(f"  class_id={st.class_id}, script_type_index={st.script_type_index}")
            if st.script_type_index >= 0:
                ls = sf.script_types[st.script_type_index]
                print(f"  script_types[{st.script_type_index}] = ({ls.local_serialized_file_index}, {ls.local_identifier_in_file})")
