"""
Tic-tac-toe game server.

classes: GameMatch, GameHandler, ThreadingHTTPServer
"""

import random
import socketserver
import http.server
import http.cookies
import urllib.parse
import json
import datetime
import time


class GameMatch:
    """
    Store the state of a single game match.

    instance variables: match_id, player_1, player_2, update_dict,
                        board, state
    methods: __init__, check_game_over, check_valid_move
    """

    def __init__(self, match_id, player_1, board_size=3):
        """Set instance variables."""
        self.match_id = match_id
        self.player_1 = player_1
        self.player_2 = None
        self.update_dict = {1 : False, 2 : False}
        self.board = ['*' * board_size]  * board_size
        self.state = 'WAITING'

    def check_game_over(self):
        """
        Return 'o' or 'x' if the match has ended.
        Otherwise return False.
        """
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
        if all(self.board[n][len(self.board) - n - 1] == 'o'
               for n in range(len(self.board))):
            return 'o'
        if all(self.board[n][len(self.board) - n - 1] == 'x'
               for n in range(len(self.board))):
            return 'x'
        return False

    def check_valid_move(self, tile_x, tile_y):
        """
        Return True if a move is valid.

        (0, 0) is the top left corner.
        """
        move_is_on_board = 0 <= tile_x < len(self.board) and (
            0 <= tile_y < len(self.board))
        spot_is_free = self.board[tile_y][tile_x] == '*'
        return move_is_on_board and spot_is_free


class GameHandler(http.server.BaseHTTPRequestHandler):
    """
    Handle game requests.

    Class variables: matches, player_ids
    Methods: index_page, set_player_id, get_player_id,
             create_game, game_state, wait_for_update, make_move,
             match, get_query, game_javascript, do_GET
    """

    matches = dict()
    player_ids = set()

    def index_page(self):
        """Send the index page as a response."""
        self.send_response(200)
        self.end_headers()
        with open('index.html', 'r') as index_page:
            self.wfile.write(index_page.read().encode())

    def set_player_id(self):
        """
        Set the player_id cookie if it's not already set.
        Return player_id.
        """
        cookie = http.cookies.SimpleCookie(self.headers.get('Cookie', ""))
        player_id = None
        if 'player_id' not in cookie:
            player_id = random.randint(1, 10000000)
            while player_id in GameHandler.player_ids:
                player_id = random.randint(1, 10000000)
            self.send_header('Set-Cookie', 'player_id={}'.format(player_id))
            GameHandler.player_ids.add(player_id)
        return player_id or int(cookie['player_id'].value)

    def get_player_id(self):
        """Return player_id or 0 if it isn't set."""
        cookie = http.cookies.SimpleCookie(self.headers.get('Cookie', ""))
        return int(cookie['player_id'].value) if 'player_id' in cookie else 0

    def create_game(self):
        """Create a new match and set the player_id."""
        self.send_response(303)
        query = self.get_query()
        query_dict = urllib.parse.parse_qs(query)
        size = max(min(int(query_dict.get('size', [3])[0]), 5), 0)
        player_id = self.set_player_id()
        match_id = random.randint(1, 10000000)
        while match_id in GameHandler.matches:
            match_id = random.randint(1, 10000000)
        GameHandler.matches[match_id] = GameMatch(match_id, player_id,
                                                  board_size=size)
        self.send_header('Location', '/match?id={}'.format(match_id))
        self.end_headers()
        self.wfile.write(str(match_id).encode())

    def game_state(self):
        """Send the state of a specific match as a response."""
        query = self.get_query()
        query_dict = urllib.parse.parse_qs(query)
        match_id = int(query_dict.get('id', [-1])[0])
        player_id = self.get_player_id()
        match = GameHandler.matches.get(match_id)
        if match and player_id in (match.player_1, match.player_2):
            player_num = 1 if player_id == match.player_1 else 2
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'board' : match.board,
                                         'state' : match.state,
                                         'player_num' : player_num}).encode())
        else:
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

    def wait_for_update(self):
        """
        Wait until there is an update before sending a response.
        If there hasn't been an update in 60 seconds end the game.
        """
        query = self.get_query()
        query_dict = urllib.parse.parse_qs(query)
        match_id = int(query_dict.get('id', [-1])[0])
        player_id = self.get_player_id()
        match = GameHandler.matches.get(match_id)
        if match and player_id in (match.player_1, match.player_2):
            player_num = 1 if player_id == match.player_1 else 2
            start_time = datetime.datetime.now()
            while match.update_dict[player_num]:
                time.sleep(0.5)
                if (datetime.datetime.now() - start_time).seconds >= 60:
                    if match.state in ('PLAYER_2_TURN', 'WAITING'):
                        match.state = 'PLAYER_1_WIN'
                    elif match.state == 'PLAYER_1_TURN':
                        match.state = 'PLAYER_2_WIN'
                    break
            match.update_dict[player_num] = True
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

    def make_move(self):
        """Change the state of a specific match."""
        query = self.get_query()
        query_dict = urllib.parse.parse_qs(query)
        tile_x = int(query_dict.get('x', [-1])[0])
        tile_y = int(query_dict.get('y', [-1])[0])
        match_id = int(query_dict.get('id', [-1])[0])
        match = GameHandler.matches.get(match_id)
        player_id = self.get_player_id()
        player_num = 0
        if match:
            player_num = {match.player_1 : 1, match.player_2 : 2}.get(
                player_id, 0)
        turn_player_num = 1 if match and match.state == 'PLAYER_1_TURN' else 2
        self.send_response(200)
        self.end_headers()
        if all((tile_x is not None, tile_y is not None, match)) and (
                turn_player_num == player_num) and (
                    match.check_valid_move(tile_x, tile_y)):
            match.board[tile_y] = match.board[tile_y][:tile_x] + (
                'x' if player_num == 1 else 'o') + (
                    match.board[tile_y][min(tile_x + 1, len(match.board)):])
            if all(all(c != '*' for c in s) for s in match.board):
                match.state = 'TIE'
            elif match.check_game_over():
                match.state = 'PLAYER_1_WIN' if player_num == 1 else (
                    'PLAYER_2_WIN')
            else:
                match.state = 'PLAYER_2_TURN' if player_num == 1 else (
                    'PLAYER_1_TURN')
            self.wfile.write(b'success')
            match.update_dict[1] = False
            match.update_dict[2] = False
        else:
            self.wfile.write(b'failure')

    def match(self):
        """
        Send the match page as a response.

        Set player_id cookie if not already set.
        """
        query = self.get_query()
        query_dict = urllib.parse.parse_qs(query)
        match_id = int(query_dict.get('id', [-1])[0])
        match = GameHandler.matches.get(match_id)
        player_id = self.get_player_id()
        response_sent = False
        if match and not match.player_2 and player_id != match.player_1:
            if player_id == 0:
                self.send_response(200)
                player_id = self.set_player_id()
                response_sent = True
            match.player_2 = player_id
            match.state = 'PLAYER_1_TURN'
            match.update_dict[1] = False
        if match and player_id in (match.player_1, match.player_2):
            if not response_sent:
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

    def game_javascript(self):
        """Send game.js as a response."""
        self.send_response(200)
        self.end_headers()
        with open('game.js', 'r') as javascript:
            self.wfile.write(javascript.read().encode())

    def do_GET(self):
        """Handle a GET request."""
        path = self.path.replace(self.get_query(), '')
        path = path.replace('?', '')
        paths = {'/' : self.index_page,
                 '/game.js' : self.game_javascript,
                 '/create_game' : self.create_game,
                 '/game_state' : self.game_state,
                 '/make_move' : self.make_move,
                 '/match' : self.match,
                 '/wait_for_update' : self.wait_for_update}
        if path in paths:
            paths[path]()
        else:
            self.send_response(301)
            self.send_header('Location', '/')
            self.end_headers()


class ThreadingHTTPServer(socketserver.ThreadingMixIn,
                          http.server.HTTPServer):
    """HTTP server with threading."""


def run_server():
    """Start the game server."""
    http_server = ThreadingHTTPServer(('192.168.0.8', 8080), GameHandler)
    http_server.serve_forever()

if __name__ == '__main__':
    run_server()
