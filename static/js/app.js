const game_port = '9000';
const BOARD = 'board';
const SCORE = 'score';
const PLAYERS = 'players';
const NAMES = 'names';
const SIZE = 'size';
const hostname = window.location.hostname;
const url = "ws://" + hostname + ":" + game_port;
const WEB_SOCKET_CONNECT_TIMEOUT = 500;  // NOTE: workaround to handle async websocket and webpage
const gameBoardSocketUrl = url + "?client_type=Player&name=" + getUrlValue('user');
const cellSize = 20;
const baselWidth = 10;
const scorePaneSize = 400;
const scoreTitleFont = "14px arial";
const score_font = "bold 18px arial";
const scoreFontColor = "#000000";
const player_name_font = "11px arial";
const playerNameColor = "#ffffff";
const imagesRoot = "static/images/";
const cellImagesInfo = {
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

const cells_info = getCellsInfo();
let boardSize;
let canvasCtx;


function getCellsInfo() {
    let cells_info = {};
    for (let index in cellImagesInfo) {
        cells_info[index] = new Image();
        cells_info[index].src = imagesRoot + cellImagesInfo[index]
    }
    return cells_info
}

const movesInfo = {
    'ArrowLeft': 'Left',
    'ArrowUp': 'Up',
    'ArrowRight': 'Right',
    'ArrowDown': 'Down',
    'KeyZ': 'DrillLeft',
    'KeyX': 'DrillRight',
};


function getUrlValue(varSearch) {
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

function websocketGame() {
    canvasCtx = getCanvasContext();
    setTimeout(() => {
        let gameBoardSocket = gameBoardSocketManager();
        keyboardManager(gameBoardSocket)
    }, WEB_SOCKET_CONNECT_TIMEOUT)
}

function gameBoardSocketManager() {
    let gameBoardSocket = new WebSocket(gameBoardSocketUrl);

    gameBoardSocket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        if (!boardSize) {
            boardSize = sessionInfo[SIZE]
        }
        handleBoardSizeChange(sessionInfo[SIZE]);
        showGameBoard(sessionInfo[BOARD]);
        showScores(sessionInfo);
        showPlayersNames(sessionInfo[PLAYERS][NAMES]);
    };
    return gameBoardSocket
}

function getCanvasContext() {
    if (canvasCtx) {
        let canvas = document.getElementById('canvas');
        canvas.parentNode.removeChild(canvas);
    }
    let canvas = document.createElement("canvas");
    canvas.id = 'canvas';
    let ctx = canvas.getContext("2d");
    canvas.width = $(window).width() - cellSize;
    canvas.height = $(window).height() - cellSize;
    document.body.appendChild(canvas);
    return ctx
}

function handleBoardSizeChange(size) {
    if (boardSize && size !== boardSize) {
        console.log('Game board size has been changed to ' + size.toString());
        boardSize = size;
        canvasCtx = getCanvasContext()
    }
}

function showGameBoard(boardMessage) {
    for (let y in boardMessage) {
        for (let x in boardMessage[y]) {
            canvasCtx.drawImage(
                cells_info[boardMessage[y][x]],
                x * cellSize + baselWidth,
                y * cellSize + baselWidth
            );
        }
    }
    canvasCtx.beginPath();
    canvasCtx.lineWidth = baselWidth;
    canvasCtx.strokeStyle = "blue";
    let baselSize = boardMessage.length * cellSize + baselWidth;
    canvasCtx.rect(baselWidth/2, baselWidth/2, baselSize, baselSize);
    canvasCtx.stroke();
}

function showScores(sessionInfo) {
    let scoreMessage = sessionInfo[PLAYERS][SCORE];
    let boardSize = sessionInfo[SIZE];
    canvasCtx.clearRect(
        boardSize * cellSize + baselWidth * 2,
        0,
        boardSize * cellSize + scorePaneSize,
        boardSize * cellSize + cellSize
    );

    canvasCtx.font = scoreTitleFont;
    canvasCtx.fillStyle = scoreFontColor;
    canvasCtx.fillText(
        "Players:",
        boardSize * (cellSize + 1) + 2 * baselWidth,
        cellSize
    );
    canvasCtx.font = score_font;
    canvasCtx.fillStyle = scoreFontColor;
    for (let [playerName, score] of Object.entries(scoreMessage)) {
        canvasCtx.fillText(
            playerName + ': ' + score,
            boardSize * (cellSize + 1) + 2 * baselWidth,
            cellSize * 2 + Object.keys(scoreMessage).indexOf(playerName) * cellSize)
    }
}

function showPlayersNames(players) {
    for (let [playerName, value] of Object.entries(players)) {
        let x = value[0];
        let y = value[1];
        writePlayerName(
            playerName,
            x,
            y,
            playerNameColor)
    }
}

function writePlayerName(name, x, y, color) {
    let xReal = x * cellSize + baselWidth;
    let yReal = y * cellSize - 2 + baselWidth;
    canvasCtx.font = player_name_font;
    canvasCtx.strokeStyle = 'black';
    canvasCtx.lineWidth = 2;
    canvasCtx.strokeText(name, xReal, yReal);
    canvasCtx.fillStyle = color;
    canvasCtx.fillText(name, xReal, yReal);
}

function keyboardManager(game_board_socket) {
    window.addEventListener('keyup',
        function (event) {
            if (getUrlValue('user') !== '' && event.code in movesInfo) {
                game_board_socket.send(movesInfo[event.code])
            }

        }
    )
}


websocketGame();

// TODO: fix empty cell of players
// TODO: reconnect after server restart