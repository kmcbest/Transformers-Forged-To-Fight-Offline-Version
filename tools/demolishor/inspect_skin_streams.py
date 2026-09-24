# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

def inspect_skin_channel(bundle_path, mesh_name):
    env = UnityPy.load(bundle_path)
    for obj in env.objects:
        if obj.type.name == 'Mesh':
            tree = obj.read_typetree()
            if mesh_name in tree.get('m_Name', ''):
                print(f"\n--- {mesh_name} in {bundle_path} ---")
                vdata = tree.get('m_VertexData', {})
                channels = vdata.get('m_Channels', [])
                for i, ch in enumerate(channels):
                    if ch.get('dimension') > 0:
                        print(f"  Channel {i}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dim={ch.get('dimension')}")
                
                raw = bytes(vdata.get('m_DataSize', []))
                # Check stream offsets
                streams = vdata.get('m_Streams', [])
                print("Streams count:", len(streams))
                for s_idx, st in enumerate(streams):
                    print(f"  Stream {s_idx}: channelMask={st.get('channelMask')}, offset={st.get('offset')}, stride={st.get('stride')}, dividerOp={st.get('dividerOp')}, freq={st.get('frequency')}")
                return tree

t1 = inspect_skin_channel('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle', 'cha_ironhide_cin_rotf_00')
t2 = inspect_skin_channel('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle', 'cha_demolishor_gs_00')
