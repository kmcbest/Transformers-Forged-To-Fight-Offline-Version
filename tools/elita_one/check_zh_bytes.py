from pathlib import Path

data = Path("Server/bot_names_zh.json").read_bytes()
print("Total bytes:", len(data))
print("Last 200 bytes:", data[-200:])
try:
    s = data.decode("utf-8")
    print("Decodes as UTF-8 cleanly!")
except Exception as e:
    print("Failed to decode UTF-8:", e)
