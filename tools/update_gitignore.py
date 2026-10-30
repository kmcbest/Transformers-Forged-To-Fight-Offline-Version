with open(r"E:\Agent\TFTF-blender\.gitignore", "r", encoding="utf-8") as f:
    text = f.read()

target = "!assets_redeco/*elita*\n"
replacement = "!assets_redeco/*elita*\n!assets_redeco/*bumblebee*\n"

if "\r\n" in text:
    target = target.replace("\n", "\r\n")
    replacement = replacement.replace("\n", "\r\n")

if target in text:
    text = text.replace(target, replacement)
    with open(r"E:\Agent\TFTF-blender\.gitignore", "w", encoding="utf-8") as f:
        f.write(text)
    print("Successfully added !assets_redeco/*bumblebee* to .gitignore")
else:
    print("Target not found in .gitignore")
