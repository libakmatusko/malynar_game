from time import time, localtime, strftime, sleep
import requests
from front import Front
import json
SERVER_IP = 'http://127.0.0.1:5000'# pre ucely debugovania, myslim ze tato je defaultna adresa


class actions:
    def __init__(self, name, starting_pos):
        self.playing = False
        self.name = name
        self.tick_counter = -1
        self.inventory = {
            'people': 0
        }
        self.army = {

        }
        self.trades = [
            
        ]
        self.my_lands = [
            {
                'name': 'base',
                'position': starting_pos,
                'ticks per item': 10,
                'time to generation': 10,
                'generating': False,
                'input': {},
                'output': {'people': 1},
            }
        ]# toto sa zmeni o poziciu zakladne pri prvom napojenie na server
        self.all_lands = [
            {
                'name': 'base',
                'position': starting_pos,
            }
        ]
        self.available_lands = [starting_pos]
        self.add_available_lands(starting_pos)
        self.front = Front(self)


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
                else:
                    if self.take_from_inventory(land['input']):
                        land['generating'] = True
        
    # neviem este ako presne ma vyzerat, returne True ak sa hra
    def update_from_server(self):
        response = requests.post(
            f'{SERVER_IP}/update/{self.name}',
        )


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
        for land in [
            [pos[0], pos[1]+1],
            [pos[0]+1, pos[1]],
            [pos[0]-1, pos[1]+1],
            [pos[0], pos[1]-1],
            [pos[0]-1, pos[1]],
            [pos[0]+1, pos[1]-1],    
        ]:
            if not land in self.available_lands:
                self.available_lands.append(land)

    

    def save(self):
        t = strftime("%d-%B-%Hh%Mm%Ss", localtime())
        with open(f'save_{t}.json', 'w') as save_file:
            to_save = dict(self.__dict__)
            print(to_save)
            to_save.pop('front')
            save_file.write(json.dumps(
                to_save,
                indent=4
            ))
    

    def load(self, save_name: str):# v tvare reload:save_03-May-21h20m30s 
         with open(f'{save_name}.json', 'r') as save_file:
            self.__dict__ = json.load(save_file)


def conect():
    name_input = input().strip()
    if name_input[:6] == 'reload':
        player = actions('', [0, 0])
        player.load(name_input[7:])
        return player
        
    response = requests.post(
        f'{SERVER_IP}/conect/{name_input}',
    )
    if response.status_code == 400:
        print('Username already in use. Try a new one:', end=' ')
        conect()
    elif response.status_code == 200:
        player = actions(response.json()['name'], response.json()['starting_pos'])
    return player
    

def start():
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

last_time = 0
while True:
    if last_time < time() - 1:
        last_time = time()
        player.tick()
    player.front.update()
