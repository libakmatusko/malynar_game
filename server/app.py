from flask import Flask, request, jsonify

app = Flask(__name__)

class game_state():
    def __init__(self, game_description):
        self.game_description = game_description
        self.playing = False
        self.names = []
        self.starting_positions = [[30, 0], [0, 30], [30, -30], [-30, 0], [0, -30], [-30, 30]]

game = game_state('idk')


@app.route('/conect/<name>', methods=['POST'])
def new_player(name):
    if name in game.names:
        return 'duplicate username', 400
    if len(game.names) == 6:
        return 'game is full', 403
    game.names.append(name)
    if len(names) == 6:
        game.playing = True# nie som si isty ci nebude lepsie pouzit global
    return jsonify({'name': name, 'starting_pos': starting_positions[len(game.names)-1]})

@app.route('/update/<name>', methods=['GET'])
def update(name):
    if game.playing:
        pass #posielas update
    else:
        return 'Waiting for players', 403


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)