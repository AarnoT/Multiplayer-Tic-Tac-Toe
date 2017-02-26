'use strict';
function setCanvasSize() {
    const size = Math.min(window.innerWidth * 0.6, window.innerHeight * 0.6)
    const canvas = document.getElementById('game_canvas');
    canvas.width = size;
    canvas.height = size;
}
function setHeader() {
    document.getElementById('header').innerHTML = 'Game ID: ' + match_id;
}
function getMatchID() {
    const regex = new RegExp('\\?id=(\\d+)').exec(window.location.href);
    if (regex && regex.length >= 2) {
        const match_id = regex[1];
        return match_id;
    }
    return 0
}
const match_id = getMatchID();
let state = { state : 'WAITING' };
function updateState() {
    const req = new XMLHttpRequest();
    req.responseType = 'json';
    req.open('GET', '/game_state?id=' + match_id);
    req.onreadystatechange = function() {
        if (req.readyState === 4 && req.status === 200) {
            state = req.response;
            document.getElementById('game_state').innerHTML = state.state;
            drawGrid();
            for (let x = 0; x < state.board.length; x++) {
                for (let y = 0; y < state.board.length; y++) {
                    if (state.board[y][x] === 'x') {
                        drawX(x, y);
                    } else if (state.board[y][x] === 'o') {
                        drawO(x, y);
                    }
                }
            }
        }
    }
    req.send(null);
}
function waitForUpdate() {
    updateState();
    const req = new XMLHttpRequest();
    req.timeout = 65 * 1000;
    req.open('GET', '/wait_for_update?id=' + match_id);
    req.onreadystatechange = function() {
        if (req.readyState === 4 && req.status !== 0 &&
                ! state.state.includes('WIN') && ! state.state.includes('TIE')) {
            waitForUpdate();
        }
    }
    req.send(null);
}
function drawGrid() {
    const size = state.board.length;
    const canvas = document.getElementById('game_canvas');
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.beginPath();
    for (let x = canvas.width / size; x < canvas.width; x += canvas.width / size) {
        context.moveTo(x, 0);
        context.lineTo(x, canvas.height);
    }
    for (let y = canvas.height / size; y < canvas.height; y += canvas.height / size) {
        context.moveTo(0, y);
        context.lineTo(canvas.width, y);
    }
    context.stroke();
    context.closePath();
}
function drawX(tile_x, tile_y) {
    const size = state.board.length;
    const canvas = document.getElementById('game_canvas');
    const context = canvas.getContext('2d');
    const tile_size = canvas.width / size;
    context.beginPath();
    context.moveTo(tile_size * (tile_x + 0.1), tile_size * (tile_y + 0.1));
    context.lineTo(tile_size * (tile_x + 0.9), tile_size * (tile_y + 0.9));
    context.moveTo(tile_size * (tile_x + 0.1), tile_size * (tile_y + 0.9));
    context.lineTo(tile_size * (tile_x + 0.9), tile_size * (tile_y + 0.1));
    context.stroke();
    context.closePath();
}
function drawO(tile_x, tile_y) {
    const size = state.board.length;
    const canvas = document.getElementById('game_canvas');
    const context = canvas.getContext('2d');
    const tile_size = canvas.width / size;
    context.beginPath();
    context.arc(tile_size * (tile_x + 0.5), tile_size * (tile_y + 0.5),
                tile_size * 0.4, 0, 2 * Math.PI, false);
    context.stroke();
    context.closePath();
}
function handleClick(event) {
    const size = state.board.length;
    const canvas = document.getElementById('game_canvas');
    const tile_x = Math.min(Math.floor((event.pageX - canvas.offsetLeft) / (canvas.width/size)),
                                       state.board.length);
    const tile_y = Math.min(Math.floor((event.pageY - canvas.offsetTop) / (canvas.width/size)),
                                       state.board.length);
    if ((state.state === 'PLAYER_1_TURN' && state.player_num === 1) ||
            (state.state === 'PLAYER_2_TURN' && state.player_num === 2)) {
        const req = new XMLHttpRequest();
        req.open('GET', `/make_move?id=${match_id}&x=${tile_x}&y=${tile_y}`);
        req.send(null);
    }
}