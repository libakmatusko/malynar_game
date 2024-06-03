from flask import Flask, request, jsonify
import json
import functools

app = Flask(__name__)

class All_trades():
    def __init__(self):
        self.actual_trades = {}        # int id : Trade_offer
        self.sold_trades = {}          # player name : Trade_offer
        self.current_id = 0
    
    def place_trade(self, owner, type, item, count, cost):
        self.current_id += 1
        self.actual_trades[self.current_id] = Trade_offer(owner, item, count, cost, type)
        return self.current_id

    def take_trade(self, id):
        if id in self.actual_trades:
            self.sold_trades[id] = self.actual_trades.pop(id)
            return True
        return False
        

    def is_sold(self, id):
        if id in self.sold_trades.keys():
            self.sold_trades.pop(id)
            return True
        return False
    
    def get_availible_trades(self):
        return self.actual_trades
        

class Trade_offer():
    def __init__(self, owner, item, count, cost, type):
        self.owner = owner  # player who placed trade
        self.item = item
        self.count = count
        self.cost = cost    # amounth of money
        self.type = type    # 0 if you offer money for item, 1 if you offer item for money
        

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
    return jsonify({'all_lands': game.all_lands, 'trades': game.trades})


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
    game.trades.place_trade() # to do
    return 'Placed', 200

@app.route('/take_trade/<id>', methods=['POST'])
def take_trade(id):
    return game.trades.take_trade(id), 200

@app.route('/was_trade_taken/<id>', methods=['POST'])
def was_trade_taken(id):
    return game.trades.is_sold(id), 200

@app.route('/get_all_trades/', methods=['POST', 'GET'])
def get_all_trades():
    return jsonify(game.trades.get_availible_trades())

def to_pos_string(x: int, y: int):
    return f'{x}x{y}'

def from_pos_string(pos: str):
    return list(map(int, pos.split('x')))


game = game_state('idk')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)