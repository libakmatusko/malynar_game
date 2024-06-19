from time import time, localtime, strftime, sleep
import requests
import front
import json
import os
from copy import copy
import random
from math import floor
SERVER_IP = 'http://127.0.0.1:5000'# pre ucely debugovania, myslim ze tato je defaultna adresa
LAN_SERVER_IP = 'http://192.168.1.20:5000'# stefi to na tomto spojazdnil
#SERVER_IP = LAN_SERVER_IP

class actions:
    def __init__(self, name, starting_pos, debug=False):
        self.debug:bool = debug
        self.playing:bool = False
        self.name:str = name
        
        self.points:int = 0
        self.army_points: int = 0

        self.tick_counter:int = -1
        self.inventory:dict[str, int] = {
            'ľudia': 1,
            'kameň': 50,
            'drevo': 50,
            'peniaze': 10,
            "jedlo": 1
        }
        with open('desktop/army.json', 'r', encoding='utf-8') as f:
            self.army:dict = json.load(f)

        self.trades:dict = {}                # id : trade_info
        self.trades:dict = {1: {"owner": "admin", "type": 0, "count": 10, "item": "železo", "cost": 20}}
        self.placed_trades:dict = {}         # id : trade_info
        self.my_lands:list = [
            {
                'name': 'base',
                'position': starting_pos,
                'ticks per item': 60,
                'time to generation': 10,
                'generating': True,
                'input': {},
                'output': {'ľudia': 1},
                'points': 0,
                'is_sleeping': False
            }
        ]# toto sa zmeni o poziciu zakladne pri prvom napojenie na server
        self.all_lands:dict = {}
        for x in range(-30, 31):
            for y in range(-30, 31):
                if -x-31<y<-x+31:
                    self.all_lands[self.to_pos_string(x, y)] = {
                        'name': 'land'
                    }

        with open(f'desktop/info.json', 'r', encoding='utf-8') as info_file:
            docasne = json.load(info_file)
            self.beast_types = docasne["monsters"]
            self.info = docasne["nature"]
        #print(len(self.all_lands))
        self.available_lands:list = [starting_pos]
        self.add_available_lands(starting_pos)

        with open(f'desktop/buildings.json', 'r', encoding='utf-8') as buildings_file:
            self.buildings = json.load(buildings_file)
        
        self.used_codes = []

        self.front = front.Front(self)
        self.front.center_hexagon_cords = {"x": starting_pos[0], "y": starting_pos[1]}
        self.front.update()
        self.front.draw_map()
    

    def __int__(self):
        return self.points * 100 + self.army_points + self.inventory['peniaze'] *10


    def tick(self):
        self.tick_counter += 1
        if self.tick_counter % 5 == 0:
            if not self.update_from_server():
                #print('You are now ofline.')
                pass
            else:
                pass
                #print('Game updated')
            self.create_color_codes()
            self.frontend_update()
        if self.tick_counter % 60 == 0:
            self.generate_ľudia()
            self.save()
    
        for land in self.my_lands:
            '''
            if land['name'] != 'road':
                if land['generating']:
                    if not land["is_sleeping"]:
                        if land['time to generation'] == 1:
                            land['time to generation'] = land['ticks per item']
                            land['generating'] = False
                            self.generate(land['output'])
                        else:
                            land['time to generation'] -= 1
                elif land.get('input') == None or len(land.get('input')):
                    pass
                else:
                    if self.take_from_inventory(land['input']):
                        land['generating'] = True
            '''

            # original je zakomentovany, nefungoval pri budovach berucich input a nevedel som ho opravit

            if land["generating"]:
                if not land["is_sleeping"]:
                    if land["time to generation"] == 0:
                        if self.take_from_inventory(land["input"]):
                            self.generate(land["output"])
                            land["time to generation"] = land["ticks per item"]
                    else:
                        land["time to generation"] -= 1


    def create_color_codes(self):
         
        # smiliho front end calculation
        colors = ["#ffabab", "#e7ffac", "#6eb5ff", "#f6a6ff", "#a79aff", "#fff5ba"]
        counter = 0
        self.color_code = {}
        for land in self.all_lands.keys():  
            if self.all_lands[land]['name'] == "base":
                self.color_code[self.all_lands[land]["player"]] = colors[counter]
                counter += 1


    # return True ak sa updatlo
    def update_from_server(self):
        if self.debug:
            return False
        try:
            response = requests.post(
                f'{SERVER_IP}/update/{self.name}',
            ).json()
            for key in response.keys():
                self.__dict__[key] = response[key]
        except:
            return False
        return True
    

    def frontend_update(self):
        self.front.update_inventory_window()
        self.front.show_trades()
        self.check_my_trades()
        self.front.fill_build_window()
    
    def generate_ľudia(self):
        new_count = self.inventory['jedlo'] // 30
        self.inventory['ľudia'] += min(new_count, self.inventory['ľudia'] // 10)
        self.inventory['jedlo'] -= new_count * 30

    def server_build(self, pos: list[int], building: str):
        if self.debug:
            print('Neupdatujem')
            return True
        response = requests.post(
            f'{SERVER_IP}/build/{self.name}',
            json={  
                self.to_pos_string(*pos): {
                    'name': building,
                    'player': self.name,
                    'level': 1
                }
            }
        )
        if response.status_code == 200:
            return True
    

    def server_upgrade(self, pos: list[int]):
        if self.debug:
            print('Neupdatujem')
            return True
        response = requests.post(
            f'{SERVER_IP}/upgrade/{self.name}',
            json=self.to_pos_string(*pos)
        )
    

    def build_new(self, build: str, pos: list[int]):
        print('building', build)
        print('position', pos)
        building = self.buildings[build]
        cost = building['cost'][0]
        requrement = building['requrement']
        if requrement != '':
            print(requrement)
            if not requrement in self.find_resources(pos=pos):
                print('nie je requrement')
                return False
        if not pos in self.available_lands:
            print(pos)
            print(self.available_lands)
            print('nie je v available lands')
            return False
        # moze byt postavene
        if not self.take_from_inventory(cost):
            print('nie su materialy')
            return False
        self.add_available_lands(pos)
        if building['generating'] == True:
            self.my_lands.append(
                {
                    'name': build,
                    'position': pos,
                    'ticks per item': building['ticks per item'][0],
                    'time to generation': building['ticks per item'][0],
                    'generating': building['generating'],
                    'input': building['input'][0],
                    'output': building['output'][0],
                    'points': 1,
                    'is_sleeping': False
                }
            )
        else:
            self.my_lands.append(
                {
                    'name': build,
                    'position': pos,
                    'generating': building['generating'],
                    'points': 1,
                    'is_sleeping': False
                }
            )
        self.all_lands[self.to_pos_string(*pos)] = {
            'name': build,
            'player': self.name,
            'level': 1
        }
        self.points += building.get('points', [0])[0]
        if not self.server_build(pos=pos, building=build):
            pass# daco ked sa neupdatuje na server
        return True
    
    
    def cost_to_upgrade(self, pos: list[int]) -> dict:
        all_building = self.all_lands[self.to_pos_string(*pos)]
        return self.buildings[all_building['name']]['cost'][all_building['level']]
    
    def upgrade(self, pos: list[int]) -> bool:
        if self.all_lands[self.to_pos_string(*pos)]['player'] != self.name:
            return False
        costs = self.cost_to_upgrade(pos=pos)
        if not self.take_from_inventory(costs):
            return False
        level:int = self.all_lands[self.to_pos_string(*pos)]['level']
        self.all_lands[self.to_pos_string(*pos)]['level'] += 1
        for my_land in self.my_lands:
            if my_land['position'] == pos:
                building = self.buildings[my_land['name']]
                if building["generating"]:
                    my_land.update({
                        'ticks per item': building['ticks per item'][level],
                        'input': building['input'][level],
                        'output': building['output'][level],
                    })
                break
        self.points += building.get('points', [0 for _ in range(level+1)])[level]
        if not self.server_upgrade(pos=pos):
            pass# daco ked sa neupdatuje server
        return True
    
    def place_trade(self, type, item, count, cost):
        # type - 0 if you offer peniaze for item, 1 if you offer item for peniaze
        assert type == 0 or type == 1
        if type == 0:
            self.inventory['peniaze'] -= cost
        else:
            self.inventory[item] -= count

        response = requests.post(
            f'{SERVER_IP}/place_trade/{self.name}',
            json={  
                'type': type,
                'item': item,
                'count': count,
                'cost': cost
            }
        )
        if response.status_code == 200:
            self.placed_trades[int(response.text)] = {
                'owner': self.name,
                'type': type,
                'item': item,
                'count': count,
                'cost': cost
            }
            return int(response.text)      # id of placed trade
        print("unable to place trade on server")
    
    def take_trade(self, id):
        if self.trades[id]['type'] == 0:
            if self.inventory[self.trades[id]['item']] < self.trades[id]['count']:
                return False
        else:
            if self.inventory['peniaze'] < self.trades[id]['cost']:
                return False

        response = requests.post(f'{SERVER_IP}/take_trade/{id}')
        if response.status_code == 200 and response.text == "1":
            if self.trades[id]["type"] == 0:
                self.inventory['peniaze'] += self.trades[id]['cost']
                self.inventory[self.trades[id]['item']] -= self.trades[id]['count']
            else:
                self.inventory['peniaze'] -= self.trades[id]['cost']
                self.inventory[self.trades[id]['item']] += self.trades[id]['count']
            return True
        return False
    
    def check_my_trades(self):
        ids = copy(self.placed_trades).keys()
        for id in ids:
            response = requests.post(f'{SERVER_IP}/was_trade_taken/{id}')
            if response.text == "1":
                if self.placed_trades[id]['type'] == 0:
                    self.inventory[self.placed_trades[id]['item']] += self.placed_trades[id]['count']
                else:
                    self.inventory['peniaze'] += self.placed_trades[id]['cost']
                self.placed_trades.pop(id)

    def build_soldier(self, name: str) -> bool:
        if name not in self.army.keys():
            return False
        
        if not self.take_from_inventory(self.army[name]['recipe']):
            return False
        
        self.army[name]["count"] += 1
        return True
    
    def fight_monster(self, type: str, count: int, pos: str) -> bool:
        your_stren = 0
        soldier_count = 0
        for soldier in self.army.keys():
            your_stren += self.army[soldier]["strength"] * self.army[soldier]['count']
            soldier_count += self.army[soldier]['count']

        if your_stren == 0:
            return False

        you_receieve_dmg = int(self.beast_types[type]["strength"]) * int(count)

        monsters_killed = int(floor(your_stren / self.beast_types[type]["strength"]))
        self.army_points += monsters_killed * self.beast_types[type]["strength"]

        while you_receieve_dmg > 0 and soldier_count > 0:
            soldier = random.choice(list(self.army.keys()))
            if self.army[soldier]['count'] == 0:
                continue
            if you_receieve_dmg < self.army[soldier]["strength"] / 2:
                break
            else:
                self.army[soldier]['count'] -= 1
                soldier_count -= 1
                you_receieve_dmg -= self.army[soldier]["strength"]

        if self.all_lands[pos]["count"] <= count:
            # updatovat my_lands
            l_pos = self.from_pos_string(pos=pos)
            for land in [
                [l_pos[0], l_pos[1]+1],
                [l_pos[0]+1, l_pos[1]],
                [l_pos[0]-1, l_pos[1]+1],
                [l_pos[0], l_pos[1]-1],
                [l_pos[0]-1, l_pos[1]],
                [l_pos[0]+1, l_pos[1]-1],
            ]:
                if self.all_lands[self.to_pos_string(*land)].get("player") == self.name:
                    self.available_lands.append(l_pos)
                    break

            self.all_lands[pos] = {'name': 'land'}

            self.front.status = self.possible_actions(self.front.map_cords)
            self.front.draw_menu()
            self.front.update()
        else:
            self.all_lands[pos]["count"] -= count

        response = requests.post(f'{SERVER_IP}/kill_monsters/{pos}|{monsters_killed}')

        if response.status_code == 200 and response.text == '0':
            return True
        elif response.status_code == 200:
            return False
        else:
            print('zlyhal server')
            return False


    def is_ok_code(self, item, code):
        a = int("".join([str(ord(x)) for x in self.name[:2]]))

        with open("desktop/all_codes.json", "r", encoding="utf-8") as f:
            all_codes = json.load(f)

        if (code - a) in all_codes[item]:
            self.used_codes.append(code - a)
            return True
        
        return False

    def sleep(self, pos: list[int]):
        for my_land in self.my_lands:
            if my_land['position'] == pos:
                my_land.update(
                    {'is_sleeping': True}
                )
                self.front.draw_menu()
                break


    def wake_up(self, pos: list[int]):
        for my_land in self.my_lands:
            if my_land['position'] == pos:
                my_land.update(
                    {'is_sleeping': False}
                )
                self.front.draw_menu()
                break


    # ak je v inventari dostatok veci, tak ich zobere a vrati True, inak vrati False
    # moze sa potencialne pouzit na davanie veci do inventara
    def take_from_inventory(self, taking) -> bool:
        for item in taking.keys():
            if taking[item] > self.inventory.get(item, 0):
                return False

        for item in taking.keys():
            self.inventory[item] -= taking[item]

        return True
    
    # prida veci do inventara alebo armady
    def generate(self, generated):
        for item in generated.keys():
            if item in self.army.keys():
                self.army[item] += generated[item]
            elif item in self.inventory.keys():
                self.inventory[item] += generated[item]
            else:
                self.inventory[item] = generated[item]

    def add_available_lands(self, pos: list[int]):
        try:
            self.available_lands.remove(pos)
        except:
            pass
        for land in [
            [pos[0], pos[1]+1],
            [pos[0]+1, pos[1]],
            [pos[0]-1, pos[1]+1],
            [pos[0], pos[1]-1],
            [pos[0]-1, pos[1]],
            [pos[0]+1, pos[1]-1],
        ]:
            if (not (land in self.available_lands)) and self.read_pos(*land)['name'] == 'land':
                self.available_lands.append(land)
    

    def find_resources(self, pos: list[int]):
        resources = []
        for land in [
            [pos[0], pos[1]+1],
            [pos[0]+1, pos[1]],
            [pos[0]-1, pos[1]+1],
            [pos[0], pos[1]-1],
            [pos[0]-1, pos[1]],
            [pos[0]+1, pos[1]-1],    
        ]:
            for resource in self.info.get(self.read_pos(*land)['name'], []):
                if not resource in resources:
                    resources.append(resource)
        return resources


    def possible_actions(self, pos):# bude vracat zoznam staus{info{coho: kolko/ako}, actions[co, za kolko]}
        actions = []
        info = {}

        if pos in self.available_lands:
            resources = self.find_resources(pos)
            for key in self.buildings.keys():
                if (self.buildings[key]['requrement'] == "") or (self.buildings[key]['requrement'] in resources):
                    # print(key, pos)
                    actions.append([f'Postav {key}', (self.build_new, (key, list(tuple(pos)))), self.buildings[key]['cost'][0]])

        elif self.read_pos(*pos).get('player') == self.name:
            for my_land in self.my_lands:
                if my_land['position'] == pos:
                    info.update(my_land)
                    land_input = my_land.get('input')
                    if land_input and len(land_input) != 0:
                        if my_land['is_sleeping']:
                            actions.append(['Zobud', lambda: self.wake_up(pos), {}])
                        else:
                            actions.append(['Uspi', lambda: self.sleep(pos), {}])
                    try:
                        recepy = self.buildings[my_land['name']]
                        if len(recepy['cost']) < my_land['level']:
                            actions.append(['Vylepsi', lambda: self.upgrade(pos), self.cost_to_upgrade(pos)])
                    except:# je to base
                        pass
        info.update(self.read_pos(*pos))
        return {'actions': actions, 'info': info}


    # vrati co je na policku inak vrati more
    def read_pos(self, x: int, y: int):
         return self.all_lands.get(
            f'{x}x{y}',
            {
                'name': 'sea' # if non-valid
            }
        )

    
    def to_pos_string(self, x: int, y: int) -> str:
        return f'{x}x{y}'

    def from_pos_string(self, pos: str) -> list[int]:
        return list(map(int, pos.split('x')))
    

    def save(self):
        t = strftime("%d-%B-%Hh%Mm%Ss", localtime())
        if os.getcwd()[-7:] != 'desktop':
            os.chdir(os.getcwd() + '\\desktop')
        for file in os.listdir():
            if file[:4] == 'save':
                os.remove(file)
        with open(f'save_{t}.json', 'w', encoding="utf-8") as save_file:
            to_save = dict(self.__dict__)
            to_save.pop('front')
            to_save.pop('info')
            to_save.pop('buildings')
            json.dump(to_save, save_file, indent=4)
    

    def load(self, save_name: str):# v tvare reload:save_03-May-21h20m30s 
        with open(f'desktop/{save_name}.json', 'r', encoding='utf-8') as save_file:
            self.__dict__.update(json.load(save_file))


def conect():
    name_input = input().strip()
    player = None
    if name_input[:6] == 'reload':
        player = actions('', [0, 0])
        player.load(name_input[7:])
        return player
    try:
        response = requests.post(
            f'{SERVER_IP}/conect/{name_input}',
        )
        if response.status_code == 400:
            print('Username already in use. Try a new one:', end=' ')
            conect()
        elif response.status_code == 200:
            player = actions(response.json()['name'], response.json()['starting_pos'])
    except: #ked testujeme ofline
        player = actions('Skuska', [0, 0], debug=True)
        player.all_lands[player.to_pos_string(0, 0)] = {
            'name': 'base',
            'player': player.name,
            'level': 1
        }

    return player

def start():
    if player.debug:
        return True
    response = requests.post(
        f'{SERVER_IP}/start/{player.name}',
    )
    if response.status_code == 200:
        return True
    return False


print('Enter username:', end=' ')
player = conect()

while not start():
    sleep(3)

last_time: float = 0
while True:
    if last_time < time() - 0.1:
        last_time = time()
        player.tick()
    player.front.update()
