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

    def check_game_over(self):
        """Check if the match has ended."""

    def check_valid_move(self, move):
        """Check if a move is valid."""


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
        if 'player_id' not in cookie:
            player_id = random.randint(1, 10000000)
            while player_id in GameHandler.player_ids:
                player_id = random.randint(1, 10000000)
            self.send_header('Set-Cookie', 'player_id={}'.format(player_id))
            GameHandler.player_ids.add(player_id)
        return int(cookie['player_id'].value) or player_id

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
            self.send_response(200)
            self.end_headers()
            json.dump({'board' : GameHandler.matches[match_id].board}, self.wfile)
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
            self.send_response(200)
            self.end_headers()
            with open('game.html', 'r') as game_page:
                self.wfile.write(game_page.encode())
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
