import json

with open("tools/font_base64.txt", "r", encoding="ascii") as f:
    font_base64 = f.read().strip()

with open("tools/pua_data.json", "r", encoding="utf-8") as f:
    pua_data = json.load(f)

pua_json_str = json.dumps(pua_data, ensure_ascii=False)

with open("tools/html_template.txt", "r", encoding="utf-8") as f:
    template = f.read()

result = template.replace("__FONT_BASE64__", font_base64).replace("__PUA_JSON__", pua_json_str)

output_path = r"E:\Agent\TFTF\tools\pua_icons_viewer.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(result)

print("Generated HTML successfully at:", output_path)
