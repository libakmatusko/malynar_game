from flask import Flask, request, jsonify

app = Flask(__name__)

names = []
starting_positions = [[30, 0], [0, 30], [30, -30], [-30, 0], [0, -30], [-30, 30]]

@app.route('/conect/<name>', methods=['POST'])
def new_player(name):
    if name in names:
        return 'duplicate username', 400
    names.append(name)
    return jsonify({'name': name, 'starting_pos': starting_positions[len(names)-1]})

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)