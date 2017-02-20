"""Tic-tac-toe game server."""

import random

import http.server
import http.cookies


class GameMatch:
    """Store the state of a single game match."""

    def __init__(self, player_1, board_size=3):
        """Set instance variables."""
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

    def create_game(self):
        """Create a new match and set the player_id."""
        self.set_player_id()
        self.end_headers()

    def join_game(self):
        """
        Add a player to an existing match if there is a free slot.

        Send a response that tells if it was succesful or not.
        """

    def game_state(self):
        """Send the state of a specific match as a response."""

    def make_move(self):
        """Change the state of a specific match."""

    def match(self):
        """Send the match page as a response."""

    def do_GET(self):
        """Handle a GET request."""
        paths = {'/' : self.index_page,
                 '/create_game' : self.create_game,
                 '/join_game' : self.join_game,
                 '/game_state' : self.game_state,
                 '/make_move' : self.make_move,
                 '/match' : self.match}
        if self.path in paths:
            self.send_response(200)
            paths[self.path]()


def run_server():
    """Handle requests in a loop."""
    http_server = http.server.HTTPServer(('127.0.0.1', 8080), GameHandler)
    while True:
        http_server.handle_request()

if __name__ == '__main__':
    run_server()
