const GAME_PORT = '9000';
const HOSTNAME = window.location.hostname;
const URL = "ws://" + HOSTNAME + ":" + GAME_PORT;
const ADMIN_SOCKET_URL = URL + "?client_type=Admin";
const ADMIN_URL = '/admin';
const STARTED = 'started';
const SIZE = 'size';
const GUARDS = 'guards';
const DEFAULT_RECONNECTION_RETRY_COUNT = 10;
const RECONNECTION_RETRY_TIMEOUT = 1000;
const PLAYERS_LIST_ID = 'players';
const START_STOP_BUTTON_ID = 'startStopButton';
const REGENERATE_BOARD_BUTTON_ID = 'regenerateBoardButton';
const BOARD_SIZE_SELECT_ID = 'boardSizeSelect';
const ROOT_NODE_ID = 'rootNode';
const BOARD_BLOCKS_NUMBERS = [1, 2, 3, 4, 5];

let adminSocket;
let reconnectionRetryCount;
let playersList;
let startStopButton;
let regenerateBoardButton;
let boardSizeSelect;
let guardsControlBlock;
let guardsNumberButton;
let updateGuardsNumberButton;
let rootNode;


function main() {
    rootNode = document.createElement("div");
    rootNode.id = ROOT_NODE_ID;
    document.body.appendChild(rootNode);

    playersList = document.createElement("ul");
    playersList.id = PLAYERS_LIST_ID;

    startStopButton = document.createElement('button');
    startStopButton.id = START_STOP_BUTTON_ID;

    regenerateBoardButton = getRegenerateBoardButton();
    boardSizeSelect = getBoardSizeInput();

    guardsControlBlock = getGuardsControlBlock();

    rootNode.appendChild(playersList);
    rootNode.appendChild(startStopButton);
    rootNode.appendChild(document.createElement('br'));
    rootNode.appendChild(regenerateBoardButton);
    rootNode.appendChild(boardSizeSelect);
    rootNode.appendChild(guardsControlBlock);
    adminSocket = getAdminSocket();
}

function getAdminSocket() {
    let adminSocket = new WebSocket(ADMIN_SOCKET_URL);
    adminSocket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        console.log(sessionInfo);
        showPlayers(sessionInfo[PLAYERS_LIST_ID]);
        showStartStopButton(sessionInfo[STARTED]);
        document.getElementById(BOARD_SIZE_SELECT_ID).value = sessionInfo[SIZE];
        guardsNumberButton.innerText = sessionInfo[GUARDS]
    };
    adminSocket.onclose = () => {
        console.log('Connection with game server has been dropped');
        $('#' + ROOT_NODE_ID + ' *').attr('disabled', true);
        reconnectionRetryCount--;
        if (reconnectionRetryCount > 0) {
            setTimeout(getAdminSocket, RECONNECTION_RETRY_TIMEOUT)
        } else {
            console.log("Couldn't establish connection. Giving up");
        }
    };
    adminSocket.onopen = () => {
        reconnectionRetryCount = DEFAULT_RECONNECTION_RETRY_COUNT;
        console.log('Connection has been established');
        $('#' + ROOT_NODE_ID + ' *').attr('disabled', false);
    };
    return adminSocket;
}

function showPlayers(players) {
    let playersList = document.getElementById(PLAYERS_LIST_ID);
    playersList.innerHTML = '';
    playersList.innerText = "Players:";

    for (let idx in players) {
        let player = document.createElement('li');
        playersList.appendChild(player);
        player.innerHTML = player.innerHTML + players[idx];
    }
}

function showStartStopButton(isStarted) {
    let startStopButton = document.getElementById(START_STOP_BUTTON_ID);
    if (isStarted) {
        startStopButton.innerText = 'Stop Game';
        startStopButton.removeEventListener("click", handleStart);
        startStopButton.addEventListener("click", handleStop);
    } else {
        startStopButton.innerText = 'Start Game';
        startStopButton.removeEventListener("click", handleStop);
        startStopButton.addEventListener("click", handleStart);
    }
}

function handleStart() {
    let startStopButton = document.getElementById(START_STOP_BUTTON_ID);
    $.post("/admin", {"command": "start"}, () => {
        console.log('Game has been started');
        startStopButton.removeEventListener("click", handleStart);
        startStopButton.addEventListener("click", handleStop);
        startStopButton.innerText = "Stop Game"
    })
}

function handleStop() {
    let startStopButton = document.getElementById(START_STOP_BUTTON_ID);
    $.post(ADMIN_URL, {"command": "stop"}, () => {
        console.log('Game has been stopped');
        startStopButton.removeEventListener("click", handleStop);
        startStopButton.addEventListener("click", handleStart);
        startStopButton.innerText = "Start Game"
    })
}

function getRegenerateBoardButton() {
    let regenerateBoardButton = document.createElement('button');
    regenerateBoardButton.id = REGENERATE_BOARD_BUTTON_ID;
    regenerateBoardButton.innerText = 'Regenerate Game Board';
    regenerateBoardButton.placeholder = 'Enter integer greater that zero';
    regenerateBoardButton.onclick = () => {
        $.post(ADMIN_URL, {
            "command": "regenerate_game_board",
            "args": document.getElementById(BOARD_SIZE_SELECT_ID).value
        }, () => {
            console.log('Game board has been regenerated');
        })
    };
    return regenerateBoardButton
}

function getBoardSizeInput() {
    let boardSizeSelect = document.createElement('select');
    boardSizeSelect.id = BOARD_SIZE_SELECT_ID;
    for(let idx = 0; idx < BOARD_BLOCKS_NUMBERS.length; idx++) {
        let option = new Option(BOARD_BLOCKS_NUMBERS[idx], BOARD_BLOCKS_NUMBERS[idx] + 1);
        boardSizeSelect.appendChild(option);
    }
    return boardSizeSelect
}

function getGuardsControlBlock() {
    let guardsControlBlock = document.createElement('div');
    updateGuardsNumberButton = document.createElement('button');
    updateGuardsNumberButton.innerText = 'Update guards number';
    updateGuardsNumberButton.onclick = () => {
        $.post(ADMIN_URL, {
            "command": "update_guards_number",
            "args": guardsNumberButton.innerText
        }, () => {
            console.log('Guards number has been updated');
        })
    };
    let decreaseGuardsNumberButton = document.createElement('button');
    decreaseGuardsNumberButton.innerText = '-';
    decreaseGuardsNumberButton.onclick = () => {
        if (guardsNumberButton.innerText !== '0') {
            guardsNumberButton.innerText = parseInt(guardsNumberButton.innerText) - 1;
        }
    };

    guardsNumberButton = document.createElement('button');
    let increaseGuardsNumberButton = document.createElement('button');
    increaseGuardsNumberButton.innerText = '+';
    increaseGuardsNumberButton.onclick = () => {
        guardsNumberButton.innerText = parseInt(guardsNumberButton.innerText) + 1;
    };

    guardsControlBlock.appendChild(updateGuardsNumberButton);
    guardsControlBlock.appendChild(decreaseGuardsNumberButton);
    guardsControlBlock.appendChild(guardsNumberButton);
    guardsControlBlock.appendChild(increaseGuardsNumberButton);
    return guardsControlBlock
}

main();

// TODO: add the rest of controls (add/remove guard, add/remove gold, resize/regenerate map, etc)