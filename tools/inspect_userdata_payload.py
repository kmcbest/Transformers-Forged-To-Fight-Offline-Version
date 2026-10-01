import json
import struct

with open("build/payload_test.bin", "rb") as f:
    data = f.read()

# Parse the binary payload
# First 16 bytes: magic, version, port, count...
magic = data[:8]
print("Magic:", magic)

# Let's search for @userdata:template
idx = data.find(b"@userdata:template")
print("Found @userdata:template at:", idx)

# Or search for "bid":"demolishor_gs" in the payload
demo_pos = data.find(b'"bid":"demolishor_gs"')
print("Found demolishor_gs bid at:", demo_pos)

# In @userdata:template, let's see how many "bid":" are there
user_start = data.find(b'{"userData":', idx)
user_end = data.find(b'"deletes":{}}', user_start)
if user_start != -1 and user_end != -1:
    user_chunk = data[user_start:user_end + 13]
    print("userData chunk size:", len(user_chunk))
    bids = [b.split(b'"')[0].decode() for b in user_chunk.split(b'"bid":"')[1:]]
    print(f"Total bids in @userdata:template: {len(bids)}")
    print("First 15 bids:", bids[:15])
    print("Is demolishor_gs in @userdata:template bids?", "demolishor_gs" in bids)
