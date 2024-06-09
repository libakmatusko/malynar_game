from flask import Flask, request, jsonify
import json
import functools
from time import strftime, localtime

app = Flask(__name__)

class All_trades():
    def __init__(self):
        self.all_trades = {}           # int id : trade
        self.sold_trades = {}          # player id : trade
        self.current_id = 0
    
    def place_trade(self, owner, type, item, count, cost):
        new_trade = {}
        new_trade['owner'] = owner      # player who placed trade
        new_trade['type'] = type        # 0 if you offer money for item, 1 if you offer item for money 
        new_trade['item'] = item        # specific item
        new_trade['count'] = count      # amount of item
        new_trade['cost'] = cost        # amount of money

        self.current_id += 1
        self.all_trades[self.current_id] = new_trade

        return self.current_id

    def take_trade(self, id):
        if id in self.all_trades:
            self.sold_trades[id] = self.all_trades.pop(id)
            return True
        return False

    def is_sold(self, id):
        if id in self.sold_trades.keys():
            self.sold_trades.pop(id)
            return True
        return False
    
    def get_availible_trades(self):
        return self.all_trades


class game_state():
    def __init__(self, game_description):
        self.game_description = game_description
        self.starting_positions = [
            (30, 0),
            (0, 30),
            (30, -30),
            (-30, 0),
            (0, -30),
            (-30, 30),
        ]
        self.playing = False
        self.names = []
        self.all_lands = {}
        for x in range(-40, 41):
            for y in range(-40, 41):
                if -x-40<y<-x+40:
                    self.all_lands[to_pos_string(x, y)] = {
                        'name': 'land',
                        'level': 0
                    }
        with open('server/resources.json', 'r') as resources_file:
            resources = json.load(resources_file)
            for pos in resources.keys():
                self.all_lands[pos] = resources[pos]
        self.trades = All_trades()
    
    def make_save(self) -> None:
        time = strftime("%d-%B-%Hh%Mm%Ss", localtime())
        with open(f'saves/lands_{time}.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_lands, f)
        with open(f'saves/trades_{time}.json', 'w', encoding='utf-8') as f:
            json.dump(dict(self.trades.__dict__), f)

    def restore_save(self, time: str) -> None: # to do v tvare
        with open(f'saves/lands_{time}.json', 'r', encoding='utf-8') as f:
            self.all_lands = json.load(f)
        with open(f'saves/trades_{time}.json', "r", encoding='utf-8') as f:
            self.trades.__dict__ = json.load(f)


@app.route('/conect/<name>', methods=['POST'])
def new_player(name):
    if name in game.names:
        return 'This username already exist', 400
    if len(game.names) == 6:
        return 'The game is full', 403
    game.names.append(name)
    if len(game.names) == 6:
        game.playing = True
    cords = game.starting_positions[len(game.names)-1]
    game.all_lands[to_pos_string(*cords)] = {
        'name': 'base',
        'player': name,
        'level': 1
    }
    return jsonify({'name': name, 'starting_pos': cords})


@app.route('/start/<name>', methods=['POST'])
def start(name):
    if game.playing == True:
        return "Play!", 200
    return 'Waiting', 403


@app.route('/update/<name>', methods=['POST'])
def update(name):
    return jsonify({'all_lands': game.all_lands, 'trades': game.trades.get_availible_trades()})


@app.route('/start/admin', methods=['POST', 'GET'])
def admin_start():
    game.playing = True
    return 'Started!', 200


@app.route('/build/<name>', methods=['POST'])
def build(name):
    content = request.json.keys()
    for pos in content:
        game.all_lands[pos] = content[pos]
    return 'Built', 200


@app.route('/upgrade/<name>', methods=['POST'])
def upgrade(name):
    pos = request.json
    game.all_lands[pos]['level'] += 1
    return 'Upgraded', 200

@app.route('/place_trade/<name>', methods=['POST'])
def place_trade(name):
    pos = request.json
    id = game.trades.place_trade(name, pos['type'], pos['item'], pos['count'], pos['cost'])
    return id, 200

@app.route('/take_trade/<id>', methods=['POST'])
def take_trade(id):
    return game.trades.take_trade(int(id)), 200

@app.route('/was_trade_taken/<id>', methods=['POST'])
def was_trade_taken(id):
    return game.trades.is_sold(int(id)), 200

@app.route('/quicksave/admin', methods=['POST'])
def quicksave():
    game.make_save()
    return 'Saved', 200

@app.route('/load_from_save/<time>', methods=['POST'])
def load_from_save(time):
    if not game.playing:
        return 'Not started!', 400
    game.restore_save(time)
    return 'Loaded', 200

@app.route('/hello/', methods=['POST'])
def hello(time):
    return 'hello'

def to_pos_string(x: int, y: int):
    return f'{x}x{y}'

def from_pos_string(pos: str):
    return list(map(int, pos.split('x')))



game = game_state('idk')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)