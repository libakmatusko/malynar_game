import json
with open("server/resources.json", 'r') as f:
    d = json.load(f)
for k in d.keys():
    if "count" in d[k].keys():
        d[k]['count'] = int(d[k]['count'])
with open("server/resources.json", 'w') as f:
    json.dump(d, f, indent=4)