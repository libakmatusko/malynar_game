import requests
import json
import os
SERVER_IP = 'http://127.0.0.1:5000'# pre ucely debugovania, myslim ze tato je defaultna adresa

all_items: list[str] = ['berries', 'iron']
should_save = False

def start_game():
    response = requests.post(
        f'{SERVER_IP}/start/admin',
    )
    if response.status_code == 200:
        print("Game started")
    else:
        print("Game start failed")

def add_trade(owner, type, item, count, cost):
    response = requests.post(
            f'{SERVER_IP}/place_trade/{owner}',
            json={  
                'type': type,
                'item': item,
                'count': count,
                'cost': cost
            }
        )
    if response.status_code == 200:
        print("trade added")
    else:
        print("adding trade failed")

def take_trade(id):
    response = requests.post(f'{SERVER_IP}/take_trade/{id}')
    if response.status_code == 200:
        print("trade taken")
    else:
        print("taking trade failed")

def write_trades_to_file():
    response = requests.post(
                f'{SERVER_IP}/update/admin',
            ).json()
    
    with open("admin/all_trades.json", "w", encoding='utf-8') as f:
        json.dump(response['trades'], f)

def save_server():
    response = requests.post(
                f'{SERVER_IP}/quicksave/admin',
            )
    if response.status_code == 200:
        print("server saved!")
    else:
        print('server save failed')

def load_server(time):
    response = requests.post(
                f'{SERVER_IP}/load_from_save/{time}',
            )
    if response.status_code == 200:
        print('server loaded')
    else:
        print('server load failed')

while True:
    task = input("Zadaj akciu (start, add_trade, take_trade, all_trades, start_saves, load_server)\n")

    if task == 'start':
        start_game()
        continue

    if task == 'add_trade':
        owner = input("Name of owner of task\n")
        type = int(input("type - 0 if you offer money for item, 1 if you offer item for money\n"))
        if type not in {0, 1}:
            print("zly typ ty puk\n")
            continue
        item = input("name of item\n")
        if item not in all_items:
            print("zly item ty puk\n")
            continue
        count = int(input("how many items\n"))
        cost = int(input("money value\n"))

        add_trade(owner, type, item, count, cost)
        continue

    if task == 'take_trade':
        id = int(input("trade id\n"))
        take_trade(id)
        continue
    
    if task == 'all_trades':
        write_trades_to_file()
        continue

    if task == 'start_saves':
        should_save = True
    
    if task == 'load_server':
        time = input("enter time-stamp of save-file\n")
        load_server(time)
    
    if should_save:
        save_server()

    