import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

meg_bundle = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(meg_bundle)

for name, f in env.file.files.items():
    print(f"Subfile: {name}, type={type(f)}")
    if hasattr(f, "externals"):
        print(f"  externals ({len(f.externals)}):")
        for idx, ext in enumerate(f.externals):
            print(f"    [{idx+1}] {dir(ext)} name={getattr(ext, 'name', '')} path={getattr(ext, 'path', '')}")
