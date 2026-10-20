from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\.gitignore")
content = p.read_text(encoding='utf-8')
if "!assets_redeco/*toxitron*" not in content:
    target = "!assets_redeco/*elita*"
    content = content.replace(target, target + "\n!assets_redeco/*toxitron*")
    p.write_text(content, encoding='utf-8')
    print("Updated .gitignore with toxitron whitelist")
else:
    print(".gitignore already contains toxitron")
