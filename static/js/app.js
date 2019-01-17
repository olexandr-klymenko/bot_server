const game_port = '9000';
const BOARD = 'board';
const SCORE = 'score';
const PLAYERS = 'players';
const NAMES = 'names';
const hostname = window.location.hostname;
const url = "ws://" + hostname + ":" + game_port;
const game_board_socket_url = url + "?client_type=Player&name=" + get_url_value('user');
const cell_size = 20;
const score_pane_size = 400;
const score_font = "bold 18px arial";
const score_font_color = "#000000";
const player_name_font = "11px arial";
const playerNameColor = "#ffffff";
const imagesRoot = "static/images/";
const cell_images_info = {
    '=': 'breakable.png',
    '*': 'drill.png',
    '0': 'drill_filled.png',
    ' ': 'empty.png',
    '1': 'empty.png',
    '2': 'empty.png',
    '3': 'empty.png',
    '4': 'empty.png',
    '$': 'gold.png',

    '<': 'guard_looks_left.png',
    '>': 'guard_looks_right.png',
    'X': 'guard_on_ladder.png',
    'd': 'guard_on_pipe_left.png',
    'b': 'guard_on_pipe_right.png',

    '@': 'hero_dies.png',
    '{': 'hero_looks_left.png',
    '}': 'hero_looks_right.png',
    'Y': 'hero_on_ladder.png',
    'C': 'hero_on_pipe_left.png',
    'D': 'hero_on_pipe_right.png',

    'H': 'ladder.png',
    '-': 'pipe.png',

    '(': 'player_looks_left.png',
    ')': 'player_looks_right.png',
    'y': 'player_on_ladder.png',
    'q': 'player_on_pipe_left.png',
    'p': 'player_on_pipe_right.png',

    '#': 'unbreakable.png'
};

const cells_info = get_cells_info();

const movesInfo = {
    'ArrowLeft': 'Left',
    'ArrowUp': 'Up',
    'ArrowRight': 'Right',
    'ArrowDown': 'Down',
    'KeyZ': 'DrillLeft',
    'KeyX': 'DrillRight',
};

function main() {
    $.get("/rest/get_board_size", function (data) {
        websocket_game(parseInt(data));
    });
}


function get_url_value(varSearch) {
    let searchString = window.location.search.substring(1);
    let variableArray = searchString.split('&');
    for (let index = 0; index < variableArray.length; index++) {
        let keyValuePair = variableArray[index].split('=');
        if (keyValuePair[0] === varSearch) {
            return keyValuePair[1];
        } else {
            return ''
        }
    }
}

function websocket_game(board_size) {
    let game_board_socket = game_board_socket_manager(board_size);
    keyboard_manager(game_board_socket)
}

function game_board_socket_manager(board_size) {
    let game_board_socket = new WebSocket(game_board_socket_url);
    let canvas_ctx = get_canvas_context(board_size);

    game_board_socket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        show_game_board(sessionInfo[BOARD], canvas_ctx, board_size);
        show_scores(sessionInfo[PLAYERS][SCORE], canvas_ctx, board_size);
        show_players_names(sessionInfo[PLAYERS][NAMES], canvas_ctx);
    };
    return game_board_socket
}

function get_canvas_context(board_size) {
    let canvas = document.createElement("canvas");
    let ctx = canvas.getContext("2d");
    canvas.width = board_size * cell_size + score_pane_size;
    canvas.height = board_size * cell_size;
    document.body.appendChild(canvas);
    return ctx
}

function get_cells_info() {
    let cells_info = {};
    for (let index in cell_images_info) {
        cells_info[index] = new Image();
        cells_info[index].src = imagesRoot + cell_images_info[index]
    }
    return cells_info
}

function show_game_board(board_message, ctx, board_size) {
    for (let vertical_index = 0; vertical_index < board_size; vertical_index++) {
        for (let horizontal_index = 0; horizontal_index < board_size; horizontal_index++) {
            let current_cell_type = board_message[vertical_index * board_size + horizontal_index];
            ctx.drawImage(
                cells_info[current_cell_type],
                horizontal_index * cell_size,
                vertical_index * cell_size
            );
        }
    }
}

function show_scores(score_message, canvas_ctx, board_size) {
    canvas_ctx.font = score_font;
    canvas_ctx.fillStyle = score_font_color;
    canvas_ctx.clearRect(
        board_size * cell_size,
        0,
        board_size * cell_size + score_pane_size,
        board_size * cell_size + cell_size
    );
    for (let [playerName, score] of Object.entries(score_message)) {
        let delta = Object.keys(score_message).indexOf(playerName) * cell_size;
        canvas_ctx.fillText(
            playerName + ': ' + score,
            board_size * cell_size + cell_size,
            cell_size + delta)
    }
}

function show_players_names(players, canvasCtx) {
    for (let [playerName, value] of Object.entries(players)) {
        let x = value[0];
        let y = value[1];
        write_player_name(
            canvasCtx,
            playerName,
            x,
            y,
            playerNameColor)
    }
}

function write_player_name(context, name, x, y, color) {
    let x_real = x * cell_size;
    let y_real = y * cell_size - 2;
    context.font = player_name_font;
    context.strokeStyle = 'black';
    context.lineWidth = 2;
    context.strokeText(name, x_real, y_real);
    context.fillStyle = color;
    context.fillText(name, x_real, y_real);
}

function keyboard_manager(game_board_socket) {
    window.addEventListener('keyup',
        function (event) {
            if (get_url_value('user') !== '' && event.code in movesInfo) {
                game_board_socket.send(movesInfo[event.code])
            }

        }
    )
}


main();