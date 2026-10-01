import sys
sys.path.insert(0, '.')
from Server import gamedata

ld = gamedata.build_login_data()
heroes = ld.get('heroes', {})
print("Total keys in login_data['heroes']:", len(heroes))
print("Is demolishor_gs in login_data['heroes']?", 'demolishor_gs' in heroes)
print("Keys in login_data['heroes']:")
for k in sorted(heroes.keys()):
    print(" ", k)
