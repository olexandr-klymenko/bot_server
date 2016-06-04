var game_port = '9000';
var board_message_re = /^board=(.*)/;
var score_message_re = /^score=(.*)/;
var players_message_re = /^players=(.*)/;
var player_cell_re = /^(\w+),(\d+),(\d+)/;
var hostname = window.location.hostname;
var game_board_socket_url = "ws://" + hostname + ":" + game_port + "?user=" + get_url_value('user');
var cell_size = 20;
var score_pane_size = 400;
var score_font = "bold 18px arial";
var score_font_color = "#000000";
var player_name_font = "11px arial";
var player_name_color = "#ffffff";

var cell_images_info = {
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


function main() {
    $.get("/rest/get_board_size", function (data) {
        websocket_game(parseInt(data));
    });
}


function get_url_value(VarSearch){
    var SearchString = window.location.search.substring(1);
    var VariableArray = SearchString.split('&');
    for(var index = 0; index < VariableArray.length; index++){
        var KeyValuePair = VariableArray[index].split('=');
        if(KeyValuePair[0] == VarSearch){
            return KeyValuePair[1];
        } else {
            return ''
        }
    }
}

function websocket_game(board_size) {
    var game_board_socket = game_board_socket_manager(board_size);
    keyboard_manager(game_board_socket)
}

function game_board_socket_manager(board_size) {
    var game_board_socket = new WebSocket(game_board_socket_url);
    var canvas_ctx = get_canvas_context(board_size);

    var cells_types_info = get_cells_info();
    game_board_socket.onmessage = function(event) {
        var incoming_message = event.data;

        if(incoming_message.match(board_message_re) != null) {
            show_game_board(incoming_message, canvas_ctx, cells_types_info, board_size);

        } else if(incoming_message.match(score_message_re) != null) {
            show_scores(incoming_message, canvas_ctx, board_size);

        } else if (incoming_message.match(players_message_re) != null) {
            show_players_names(incoming_message, canvas_ctx);
        }
    };
    return game_board_socket
}

function get_canvas_context(board_size) {
    var canvas = document.createElement("canvas");
    var ctx = canvas.getContext("2d");
    canvas.width = board_size * cell_size + score_pane_size;
    canvas.height = board_size * cell_size;
    document.body.appendChild(canvas);
    return ctx
}

function get_cells_info() {
    var cells_info = {};
    for (var index in cell_images_info) {
        cells_info[index] = new Image();
        cells_info[index].src = "static/images/" + cell_images_info[index]
    }
    return cells_info
}

function show_game_board(incoming_message, ctx, cells_types_info, board_size) {
    var board_message = incoming_message.replace(board_message_re, "$1");
    for (var vertical_index=0; vertical_index < board_size; vertical_index++) {
        for (var horizontal_index=0; horizontal_index < board_size; horizontal_index++) {
            var current_cell_type = board_message[vertical_index * board_size + horizontal_index];
            var cell_image = cells_types_info[current_cell_type];
            ctx.drawImage(cell_image, horizontal_index * cell_size, vertical_index * cell_size);
        }
    }
}

function show_scores(incoming_message, canvas_ctx, board_size) {
    var score_message = incoming_message.replace(score_message_re, "$1");
    canvas_ctx.font = score_font;
    canvas_ctx.clearRect(board_size * cell_size, 0, board_size * cell_size + score_pane_size, board_size * cell_size + cell_size);
    wrap_text(canvas_ctx, score_message, board_size * cell_size + cell_size, cell_size, score_pane_size, cell_size, score_font_color)
}

function wrap_text(context, text, x, y, maxWidth, lineHeight, fillstyle) {

    context.fillStyle = fillstyle;
    var breaks = text.split('\n');
    var newLines = "";
    for(var index = 0; index < breaks.length; index ++){
        newLines = newLines + breaks[index] + ' breakLine ';
    }

    var words = newLines.split(' ');
    var line = '';
    for(var n = 0; n < words.length; n++) {
        if(words[n] != 'breakLine'){
            var testLine = line + words[n] + ' ';
            var metrics = context.measureText(testLine);
            var testWidth = metrics.width;
            if (testWidth > maxWidth && n > 0) {
                context.fillText(line, x, y);
                line = words[n] + ' ';
                y += lineHeight;
            }
            else {
                line = testLine;
            }
        }else{
            context.fillText(line, x, y);
            line = '';
            y += lineHeight;
        }
    }
    context.fillText(line, x, y);
}

function show_players_names(incoming_message, canvas_ctx) {
    var players = incoming_message.replace(players_message_re, "$1").split(' ');
    for (var index=0; index<players.length; index++) {
        var player_name = players[index].replace(player_cell_re, "$1");
        var x = players[index].replace(player_cell_re, "$2");
        var y = players[index].replace(player_cell_re, "$3");
        write_player_name(canvas_ctx, player_name, x * cell_size, y * cell_size - 2, player_name_color)
    }
}

function write_player_name(context, name, x, y, color) {
    context.fillStyle = color;
    context.font = player_name_font;
    context.fillText(name, x, y);
}

function keyboard_manager(game_board_socket) {
    window.addEventListener('keyup',
        function(e){
            switch(e.keyCode) {
                case 37:
                    var move = 'Left';
                    break;

                case 38:
                    move = 'Up';
                    break;

                case 39:
                    move = 'Right';
                    break;

                case 40:
                    move = 'Down';
                    break;

                case 90:
                    move = 'DrillLeft';
                    break;

                case 88:
                    move = 'DrillRight';
                    break;
            }
            if (get_url_value('user') != ''){
                game_board_socket.send(move)
            }

        }
    )
}


main();