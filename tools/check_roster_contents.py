import sys
sys.path.insert(0, '.')
from Server import gamedata

print("Total in ROSTER:", len(gamedata.ROSTER))
print("Total in OWNED:", len(gamedata.OWNED))
print("\nIs demolishor_gs in ROSTER?", "demolishor_gs" in gamedata.ROSTER)
print("Is demolishor_gs in OWNED?", "demolishor_gs" in gamedata.OWNED)
print("Is optimusprime_cin_tf in ROSTER?", "optimusprime_cin_tf" in gamedata.ROSTER)
print("Is megatron_cin_rotf in ROSTER?", "megatron_cin_rotf" in gamedata.ROSTER)

ud = gamedata.build_user_data()
heroes = ud['updates']['heroes']
print(f"\nTotal items in updates.heroes: {len(heroes)}")
hero_bids = [h['bid'] for h in heroes if h.get('entity_type') == 'bot']
print(f"Total bots in updates.heroes: {len(hero_bids)}")
print("First 20 bots in updates.heroes:")
print(hero_bids[:20])
print("\nWhere is demolishor_gs in hero_bids?")
if "demolishor_gs" in hero_bids:
    print(f"Index of demolishor_gs: {hero_bids.index('demolishor_gs')}")
else:
    print("demolishor_gs NOT in hero_bids!")
