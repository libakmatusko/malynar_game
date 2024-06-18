import json

with open("desktop/buildings.json", "r", encoding='utf-8') as f:
    buildings = json.load(f)

with open("admin/builds_txt.txt", "w", encoding="utf-8") as f:
    for build in buildings.keys():
        print(build)
        if build == 'cesta':
            continue
        f.write('\n' + build.upper() + '\n')
        for i in range(len(buildings[build]['cost'])):
            f.write(f'{buildings[build]["input"][i]}    ---({buildings[build]["ticks per item"][i]} ⌛)--->    {buildings[build]["output"][i]}\n')
