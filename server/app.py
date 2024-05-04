from flask import Flask, request, jsonify
import json

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
        self.trades = []

game = game_state('idk')


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
    return jsonify([game.all_lands, game.trades])


@app.route('/start/admin', methods=['POST', 'GET'])
def admin_start():
    game.playing = True
    return 'Started!', 200


def to_pos_string(x: int, y: int):
    return f'{x}x{y}'

def from_pos_string(pos: str):
    return list(map(int, pos.split('x')))

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)