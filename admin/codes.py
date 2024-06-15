import random
import json

all_codes: dict[str, list[int]] = {}
used_codes: set[int] = set()

try:
    with open("desktop/all_codes.json", "r", encoding="utf-8") as f:
        all_codes = json.load(f)
except:
    all_codes = {}

def get_random_code():
    return random.randint(10000, 99999)

def create_codes(count) -> None:
    with open("desktop/buildings.json", "r", encoding="utf-8") as f:
        buildings = json.load(f)

    new_codes: dict[str, list[int]] = {}
    for build in buildings.keys():
        new_codes[build] = []
        for _ in range(count):
            code = get_random_code()
            while code in used_codes:
                code = get_random_code()
            new_codes[build].append(code)
            used_codes.add(code)
    
    with open("desktop/all_codes.json", "w", encoding='utf-8') as f:
        json.dump(new_codes, f)

def get_code(name, item):
    a = int("".join([str(ord(x)) for x in name[:2]]))

    counter = 0
    code = all_codes[item][counter]
    while code in used_codes:
        counter += 1
        code = all_codes[item][counter]
    
    return code + a

def check_code(name, code, item):
    a = int("".join([str(ord(x)) for x in name[:2]]))

    if (code - a) in all_codes[item]:
        return True
    
    return False

while True:
    task = input("zadaj ulohu (novy, check, generate_new)\n")
    if task == 'novy':
        name = input('meno druzinky\n')
        item = input('nazov budovy\n')
        print(get_code(name, item))
        continue
    if task == 'check':
        name = input('meno druzinky\n')
        item = input('nazov budovy\n')
        code = input('code\n')
        print(check_code(name, code, item))
        continue

    if task == 'generate_new':
        count = int(input('pocet kodov na budovu\n'))
        create_codes(count)
        continue
