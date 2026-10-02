import UnityPy

bpath = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bpath)

pids = [-737396187749761411, 5182645448333425879]
for obj in env.objects:
    if obj.path_id in pids:
        tree = obj.read_typetree()
        print(f"Material {obj.path_id}: {tree.get('m_Name')}")
        for prop, val in tree.get("m_SavedProperties", {}).get("m_TexEnvs", []):
            tex_ptr = val.get("m_Texture", {})
            print(f"  {prop}: PathID {tex_ptr.get('m_PathID')}")
