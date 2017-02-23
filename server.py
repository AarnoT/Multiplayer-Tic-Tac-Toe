"""Tic-tac-toe game server."""

import random
import http.server
import http.cookies
import urllib.parse
import json


class GameMatch:
    """Store the state of a single game match."""

    def __init__(self, match_id, player_1, board_size=3):
        """Set instance variables."""
        self.match_id = match_id
        self.player_1 = player_1
        self.player_2 = None
        self.board = ['*' * board_size]  * board_size
        self.state = 'WAITING'

    def check_game_over(self):
        """Check if the match has ended."""
        for y in range(len(self.board)):
            if all(self.board[x][y] == 'o' for x in range(len(self.board))):
                return 'o'
            if all(self.board[x][y] == 'x' for x in range(len(self.board))):
                return 'x'
        for x in range(len(self.board)):
            if all(self.board[x][y] == 'o' for y in range(len(self.board))):
                return 'o'
            if all(self.board[x][y] == 'x' for y in range(len(self.board))):
                return 'x'
        if all(self.board[n][n] == 'o' for n in range(len(self.board))):
            return 'o'
        if all(self.board[n][n] == 'x' for n in range(len(self.board))):
            return 'x'
        if all(self.board[n][len(self.board) - n - 1] == 'o' for n in range(len(self.board))):
            return 'o'
        if all(self.board[n][len(self.board) - n - 1] == 'x' for n in range(len(self.board))):
            return 'x'
        return False

    def check_valid_move(self, x_tile, y_tile):
        """Check if a move is valid. (0, 0) is the top left corner."""
        move_is_on_board = 0 < x_tile < len(self.board) and 0 < y_tile < len(self.board)
        spot_is_free = self.board[y_tile][x_tile] == '*'
        return move_is_on_board and spot_is_free


class GameHandler(http.server.BaseHTTPRequestHandler):
    """Handle requests and the game state."""

    matches = dict()
    player_ids = set()

    def index_page(self):
        """Send the index page as a response."""
        self.send_response(200)
        self.end_headers()
        with open('index.html', 'r') as index_page:
            self.wfile.write(index_page.read().encode())

    def set_player_id(self):
        """Set the player_id cookie if it's not already set."""
        cookie = http.cookies.SimpleCookie(self.headers.get('Cookie', ""))
        player_id = None
        if 'player_id' not in cookie:
            player_id = random.randint(1, 10000000)
            while player_id in GameHandler.player_ids:
                player_id = random.randint(1, 10000000)
            self.send_header('Set-Cookie', 'player_id={}'.format(player_id))
            GameHandler.player_ids.add(player_id)
        return player_id or int(cookie['player_id'].value)

    def create_game(self):
        """Create a new match and set the player_id."""
        self.send_response(303)
        player_id = self.set_player_id()
        match_id = random.randint(1, 10000000)
        while match_id in GameHandler.matches:
            match_id = random.randint(1, 10000000)
        GameHandler.matches[match_id] = GameMatch(match_id, player_id)
        self.send_header('Location', '/match?id={}'.format(match_id))
        self.end_headers()
        self.wfile.write(str(match_id).encode())

    def game_state(self):
        """Send the state of a specific match as a response."""
        query = self.get_query()
        query_dict = urllib.parse.parse_qs(query)
        match_id = int(query_dict.get('id', [-1])[0])
        if match_id in GameHandler.matches:
            match = GameHandler.matches[match_id]
            self.send_response(200)
            self.end_headers()
            player_id = set_player_id()
            player_num = 1 if player_id == match.player_1 else 2
            self.wfile.write(json.dumps({'board' : match.board,
                                         'state' : match.state,
                                         'player_num' : player_num}).encode())
        else:
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

    def make_move(self):
        """Change the state of a specific match."""
        self.send_response(200)
        self.end_headers()

    def match(self):
        """Send the match page as a response."""
        query = self.get_query()
        query_dict = urllib.parse.parse_qs(query)
        match_id = int(query_dict.get('id', [-1])[0])
        if match_id in GameHandler.matches and (
                not GameHandler.matches[match_id].player_2):
            player_id = self.set_player_id()
            if player_id != GameHandler.matches[match_id].player_1:
                GameHandler.matches[match_id].player_2 = player_id
                GameHandler.matches[match_id].state = 'PLAYER_1_TURN'
            self.send_response(200)
            self.end_headers()
            with open('game.html', 'r') as game_page:
                self.wfile.write(game_page.read().encode())
        else:
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

    def get_query(self):
        """Return the query as a string if the current url has one."""
        url = ':'.join(str(i) for i in self.server.server_address) + self.path
        return urllib.parse.urlparse(url).query

    def do_GET(self):
        """Handle a GET request."""
        path = self.path.replace(self.get_query(), '')
        path = path.replace('?', '')
        paths = {'/' : self.index_page,
                 '/create_game' : self.create_game,
                 '/game_state' : self.game_state,
                 '/make_move' : self.make_move,
                 '/match' : self.match}
        if path in paths:
            paths[path]()
        else:
            self.send_response(301)
            self.send_header('Location', '/')
            self.end_headers()


def run_server():
    """Handle requests in a loop."""
    http_server = http.server.HTTPServer(('127.0.0.1', 8080), GameHandler)
    while True:
        http_server.handle_request()

if __name__ == '__main__':
    run_server()
