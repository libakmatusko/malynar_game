from time import time, localtime, strftime, sleep
import requests
import front
import json
import os
SERVER_IP = 'http://127.0.0.1:5000'# pre ucely debugovania, myslim ze tato je defaultna adresa

class actions:
    def __init__(self, name, starting_pos, debug=False):
        self.debug = debug
        self.playing = False
        self.name = name
        self.tick_counter = -1
        self.inventory = {
            'people': 0,
            'stone': 10,
            'wood': 10,
            'money': 0
        }
        self.army = {}
        self.trades = {}                # id : trade_info
        self.placed_trades = {}         # id : trade_info
        self.my_lands = [
            {
                'name': 'base',
                'position': starting_pos,
                'ticks per item': 10,
                'time to generation': 10,
                'generating': False,
                'input': {},
                'output': {'people': 1},
                'points': 0
            }
        ]# toto sa zmeni o poziciu zakladne pri prvom napojenie na server
        self.all_lands = {}
        for x in range(-40, 41):
            for y in range(-40, 41):
                if -x-40<y<-x+40:
                    self.all_lands[self.to_pos_string(x, y)] = {
                        'name': 'land',
                        'level': 0
                    }
        self.available_lands = [starting_pos]
        self.add_available_lands(starting_pos)
        self.front = front.Front(self)
        self.front.update()
        with open(f'desktop/buildings.json', 'r') as buildings_file:
            self.buildings = json.load(buildings_file)
        


    def tick(self):
        self.tick_counter += 1
        if self.tick_counter % 5 == 0:
            if not self.update_from_server():
                print('You are now ofline.')
            else:
                print('Game updated')
        if self.tick_counter % 60 == 0:
            self.save()
    
        for land in self.my_lands:
            if land['name'] != 'road':
                if land['generating']:
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

    
    def server_build(self, pos: list[int], building: str):
        response = requests.post(
            f'{SERVER_IP}/build/{self.name}',
            json={  
                self.to_pos_string(*pos): {
                    'name': building,
                    'player': name,
                    'level': 1
                }
            }
        )
        if response.status_code == 200:
            return True
    

    def server_upgrade(self, pos: list[int]):
        response = requests.post(
            f'{SERVER_IP}/upgrade/{self.name}',
            json=self.to_pos_string(*pos)
        )
    

    def build_new(self, build: str, pos: list[int]):
        building = self.buildings[build]
        cost = building['cost'][0]
        requrement = building['requriment']
        if requrement != '':
            if not requrement in self.find_resources(pos=pos):
                return False
        if not pos in self.available_lands:
            return False
        # moze byt postavene
        if not self.take_from_inventory(cost):
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
                    'points': 1
                }
            )
        else:
            self.my_lands.append(
                {
                    'name': build,
                    'position': pos,
                    'generating': building['generating'],
                    'points': 1
                }
            )
        self.all_lands[self.to_pos_string(*pos)] = {
            'name': build,
            'player': self.name,
            'level': 1
        }
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
        level = self.all_lands[self.to_pos_string(*pos)]['level']
        self.all_lands[self.to_pos_string(*pos)]['level'] += 1
        for my_land in self.my_lands:
            if my_land['position'] == pos:
                my_land.update({
                    'ticks per item': building['ticks per item'][level],
                    'time to generation': building['ticks per item'][level],
                    'generating': building['generating'][level],
                    'input': building['input'][level],
                    'output': building['output'][level],
                })
                break

        if not self.server_upgrade(pos=pos):
            pass# daco ked sa neupdatuje server
        return True
    
    def place_trade(self, type, item, count, cost):
        # type - 0 if you offer money for item, 1 if you offer item for money
        assert type == 0 or type == 1
        if type == 0:
            self.inventory['money'] -= cost
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
            self.placed_trades[response[0]] = {
                'owner': self.name,
                'type': type,
                'item': item,
                'count': count,
                'cost': cost
            }
            return response[0]      # id of placed trade
    
    def take_trade(self, id):
        response = requests.post(f'{SERVER_IP}/take_trade/{id}')
        if response.status_code == 200 and response[0]:
            if self.trades[id]["type"] == 0:
                self.inventory['money'] += self.trades[id]['cost']
                self.inventory[self.trades[id]['item']] -= self.trades[id]['count']
            else:
                self.inventory['money'] -= self.trades[id]['cost']
                self.inventory[self.trades[id]['item']] += self.trades[id]['count']
            return True
    
    def check_my_trades(self):
        for id in self.placed_trades.keys():
            response = requests.post(f'{SERVER_IP}/was_trade_taken/{id}')
            if response[0]:
                if self.placed_trades[id]['type'] == 0:
                    self.inventory[self.placed_trades[id]['item']] += self.placed_trades[id]['count']
                else:
                    self.inventory['money'] += self.placed_trades[id]['cost']
                self.placed_trades.pop(id)


    def sleep(self, pos: list[int]):
        for my_land in self.my_lands:
            if my_land['position'] == pos:
                my_land.update(
                    {'input': dict(zip(my_land['input'].keys(), [key+1000000 for key in my_land['input'].keys()]))}
                )
                break


    def wake_up(self, pos: list[int]):
        for my_land in self.my_lands:
            if my_land['position'] == pos:
                my_land.update(
                    {'input': dict(zip(my_land['input'].keys(), [key-1000000 for key in my_land['input'].keys()]))}
                )
                break


    # ak je v inventari dostatok veci, tak ich zobere a vrati True, inak vrati False
    # moze sa potencialne pouzit na davanie veci do inventara
    def take_from_inventory(self, taking) -> bool:
        for item in taking.keys():
            if taking[item] > self.inventory[item]:
                return False

        for item in taking.keys():
            self.inventory[item] -= taking[item]

        return True
    
    # prida veci do inventara alebo armady
    def generate(self, generated):
        for item in generated.keys():
            if item in self.army.keys():
                self.army[item] += generated[item]
            else:
                self.inventory[item] += generated[item]


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
            if (not land in self.available_lands) and self.all_lands[self.to_pos_string(*land)]['name'] == 'land':
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
            for resource in self.all_lands[to_pos_string(*land)]['resources']:
                if not resource in resources:
                    resources.append(resource)
        return resources


    def possible_actions(self, pos):# bude vracat zoznam staus{info{coho: kolko/ako}, actions[co, za kolko]}
        actions = []
        info = {}
        status = {'actions': actions, 'info': info}

        if pos in self.available_lands:
            resources = self.find_resources(pos)
            for key in self.buildings.keys():
                if self.buildings[key]['requrement'] == "" or self.buildings[key]['requrement'] in resources:
                    actions.append([lambda: self.build_new(key, pos), self.buildings[key]['cost'][0]])

        elif self.all_lands[self.to_pos_string(*pos)]['player'] == self.name:
            for my_land in self.my_lands:
                if my_land['position'] == pos:
                    info.update(my_land)
                    if len(my_land['input']) != 0:
                        if my_land['input'][my_land['input'].keys()[0]] > 10**6:
                            actions.append([lambda: self.wake_up(pos), {}])
                        else:
                            actions.append([lambda: self.sleep(pos), {}])
                    recepy = self.buildings[my_land['name']]
                    if len(recepy['cost']) < my_land['level']:
                        actions.append([lambda: self.upgrade(pos), self.cost_to_upgrade(pos)])

        info.update(self.all_lands[self.to_pos_string(pos)])
        return status


    # vrati co je na policku inak vrati more
    def read_pos(self, x: int, y: int):
        self.all_lands.get(
            f'{x}x{y}',
            {
                'name': 'sea',  # if non-valid
                'level': 0
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
        with open(f'save_{t}.json', 'w') as save_file:
            to_save = dict(self.__dict__)
            to_save.pop('front')
            json.dump(to_save, save_file)
    

    def load(self, save_name: str):# v tvare reload:save_03-May-21h20m30s 
        with open(f'desktop/{save_name}.json', 'r') as save_file:
            self.__dict__ = json.load(save_file)


def conect():
    name_input = input().strip()
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
        player = actions('Skuska', [30, -30], debug=True)
        player.all_lands[player.to_pos_string(30, -30)] = {
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
    sleep(1)

last_time: float = 0
while True:
    if last_time < time() - 1:
        last_time = time()
        player.tick()
    player.front.update()
