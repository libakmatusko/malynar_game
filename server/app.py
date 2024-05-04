from flask import Flask, request, jsonify
import json
import functools

app = Flask(__name__)

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
        self.trades = []


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

def to_pos_string(x: int, y: int):
    return f'{x}x{y}'

def from_pos_string(pos: str):
    return list(map(int, pos.split('x')))


game = game_state('idk')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)