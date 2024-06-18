import json
with open(f'desktop/buildings.json', 'r', encoding='utf-8') as buildings_file:
    buildings = json.load(buildings_file)
    #print(buildings.keys(), len(buildings.keys()))
    for key in buildings.keys():
        #print(f'{key}{' '*(18-len(key))}levels: {len(buildings[key]['cost'])}')
        print(f'{key}{' '*(18-len(key))}{"\t".join([buildings[key]["design"][x] for x in buildings[key]["design"].keys()])}')

def d(a):
    return [f'"{i[0]}x{i[1]}"'for i in [(a, 0), (a, -a), (0, -a), (-a, 0), (-a, a), (0, a)]]

#print(*d(20), sep='\n')

