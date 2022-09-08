const game_port = '8000';
const BOARD = 'board';
const SCORE = 'score';
const PLAYERS = 'players';
const NAMES = 'names';
const SIZE = 'size';
const hostname = window.location.hostname;
const PATH = '/ws/';
const url = "ws://" + hostname + ":" + game_port + PATH;
const WEB_SOCKET_CONNECT_TIMEOUT = 500;  // NOTE: workaround to handle async websocket and webpage
const gameBoardSocketUrl = url + "?client_type=Player&client_id=" + getUrlValue('user');
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
const DEFAULT_RECONNECTION_RETRY_COUNT = 10;
const RECONNECTION_RETRY_TIMEOUT = 1000;
const cells_info = getCellsInfo();

let boardSize;
let canvasCtx;
let reconnectionRetryCount;
let sessionInfo;


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
    setCanvasContext();
    setTimeout(() => {
        let gameBoardSocket = gameBoardSocketManager();
        keyboardManager(gameBoardSocket)
    }, WEB_SOCKET_CONNECT_TIMEOUT);
    document.body.onresize = () => {
        setCanvasContext();
        showGameBoard();
        showScores();
        showPlayersNames();
    };
}

function gameBoardSocketManager() {
    let gameBoardSocket = new WebSocket(gameBoardSocketUrl);

    gameBoardSocket.onmessage = (event) => {
        sessionInfo = JSON.parse(event.data);
        if (!boardSize) {
            boardSize = sessionInfo[SIZE]
        }
        handleBoardSizeChange();
        showGameBoard();
        showScores();
        showPlayersNames();
    };

    gameBoardSocket.onclose = () => {
        console.log('Connection with game server has been dropped');
        reconnectionRetryCount--;
        if (reconnectionRetryCount > 0) {
            setTimeout(gameBoardSocketManager, RECONNECTION_RETRY_TIMEOUT)
        } else {
            console.log("Couldn't establish connection. Giving up");
        }
    };

    gameBoardSocket.onopen = () => {
        reconnectionRetryCount = DEFAULT_RECONNECTION_RETRY_COUNT;
        console.log('Connection with game server has been established');
    };
    return gameBoardSocket
}

function setCanvasContext() {
    if (canvasCtx) {
        let canvas = document.getElementById('canvas');
        canvas.parentNode.removeChild(canvas);
    }
    let canvas = document.createElement("canvas");
    canvas.id = 'canvas';
    canvasCtx = canvas.getContext("2d");
    canvas.width = $(window).width() - cellSize;
    canvas.height = $(window).height() - cellSize;
    canvas.addEventListener('click', logCoordinates, false);
    document.body.appendChild(canvas);
}

function logCoordinates(event) {
    let x = Number((event.clientX - baselWidth) / cellSize).toFixed();
    let y = Number((event.clientY - baselWidth + 2) / cellSize).toFixed();
    if (x >= 1 && x <= boardSize && y >= 1 && y <= boardSize) {
        console.log({x: x, y: y})
    }
}

function handleBoardSizeChange() {
    let size = sessionInfo[SIZE];
    if (boardSize && size !== boardSize) {
        console.log('Game board size has been changed to ' + size.toString());
        boardSize = size;
        setCanvasContext()
    }
}

function showGameBoard() {
    let boardMessage = sessionInfo[BOARD];
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

function showScores() {
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

function showPlayersNames() {
    let players = sessionInfo[PLAYERS][NAMES];
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