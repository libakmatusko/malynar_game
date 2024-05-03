from flask import Flask, request, jsonify
import json

app = Flask(__name__)

class game_state():
    def __init__(self, game_description):
        self.game_description = game_description
        self.playing = False
        self.names = []
        self.starting_positions = [(30, 0), (0, 30), (30, -30), (-30, 0), (0, -30), (-30, 30)]

game = game_state('idk')


@app.route('/conect/<name>', methods=['POST'])
def new_player(name):
    if name[:6] == 'reload':
        return jsonify({'save_name': name[7:]}, status=204)
    if name in game.names:
        return 'This username already exist', 400
    if len(game.names) == 6:
        return 'The game is full', 403
    game.names.append(name)
    if len(game.names) == 6:
        game.playing = True
    return jsonify({'name': name, 'starting_pos': game.starting_positions[len(game.names)-1]})


@app.route('/start/<name>', methods=['POST'])
def start(name):
    if game.playing == True:
        return "Play!", 200
    return 'Waiting', 403


@app.route('/update/<name>', methods=['POST'])
def update(name):
    if game.playing:
        return jsonify({})
    else:
        return 'Waiting for players', 403


@app.route('/start/admin', methods=['POST', 'GET'])
def admin_start():
    game.playing = True
    return 'Started!', 200

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)