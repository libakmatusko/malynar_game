from time import time
import requests
SERVER_IP = '0.0.0.0'


class actions:
    def __init__(self, name, starting_pos: list[int]):
        self.name = name
        self.tick_counter = -1
        self.inventory = {
            'people': 0
        }
        self.army = {

        }
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
        self.available_lands = {
            starting_pos,
            [starting_pos[0], starting_pos[1]+1],
            [starting_pos[0]+1, starting_pos[1]],
            [starting_pos[0]-1, starting_pos[1]+1],
            [starting_pos[0], starting_pos[1]-1],
            [starting_pos[0]-1, starting_pos[1]],
            [starting_pos[0]+1, starting_pos[1]-1],
            
        }


    def tick(self):

        self.tick_counter += 1
        if self.tick_counter % 5 == 0:
            if not self.update_from_server():
                self.tick_counter = -1
                return
    
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
                    if take_from_inventory(land['input']):
                        land['generating'] = True
        
    # neviem este ako presne ma vyzerat, returne True ak sa hra
    def update_from_server(self):
        pass


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


def start():
    response = requuests.post(
        f'{SERVER_IP}/conect/{input()}',
    )
    if response.status_code == 400:
        print('Username already in use. Try a new one:', end=' ')
        start()
    elif response.status_code == 200:
        player = actions(response.json()['name'], response.json()['starting_pos'])

print('Enter username:', end=' ')
start()

last_time = 0
while True:
    if last_time < time() - 1:
        last_time = time()
        player.tick()
