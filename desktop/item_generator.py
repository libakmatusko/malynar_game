from json import loads, dump

with open("desktop/buildings.json", "r", encoding="UTF-8") as file:
    data = loads(file.read())

items = set()
for i in data.keys():
    if data[i]["generating"]:
        for j in range(len(data[i]["output"])):
            for k in data[i]["output"][j].keys():
                items.add(k)

print(items)

[]


['ľudia', 'peniaze', 'jedlo', 'drevo', 'mahagón', 'doska', 'mahagónová doska', 'hlina', 'tehla', 'kameň', 'mramor', 'otesaný kameň',
'otesaný mramor', 'divina', 'koža', 'pšenica', 'múka', 'uhlie', 'piesok', 'prach', 'drahokam', 'porcelán', 'kôň', 'sedlo', 'budzogáň',
'kopija', 'meč', 'katapult', 'delo', 'mušketa', 'železná ruda', 'železo', 'zlato', 'oceľ', 'železný nástroj', 'oceľový nástroj',
'klinec', 'oceľový plát', 'sklo', 'mozajka', 'pušný prach', 'hodváb']

