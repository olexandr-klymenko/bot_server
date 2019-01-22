const game_port = '9000';
const hostname = window.location.hostname;
const url = "ws://" + hostname + ":" + game_port;
const admin_socket_url = url + "?client_type=Admin";
const PLAYERS = 'players';
const STARTED = 'started';
const SIZE = 'size';
let adminSocket;
let blocksNumber;


function main() {
    let playersList = document.createElement("ul");
    playersList.id = PLAYERS;

    let startStopButton = document.createElement('button');
    startStopButton.id = 'startStopButton';
    let regenerateBoardButton = getRegenerateBoardButton();
    let boardSizeInput = getBoardSizeInput();

    document.body.appendChild(playersList);
    document.body.appendChild(startStopButton);
    document.body.appendChild(document.createElement('br'));
    document.body.appendChild(regenerateBoardButton);
    document.body.appendChild(boardSizeInput);
    adminSocket = getAdminSocket();
}

function getAdminSocket() {
    let adminSocket = new WebSocket(admin_socket_url);
    adminSocket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        console.log(sessionInfo);
        showPlayers(sessionInfo[PLAYERS]);
        showStartStopButton(sessionInfo[STARTED]);
        blocksNumber = sessionInfo[SIZE];
        document.getElementById('boardSizeInput').value = blocksNumber
    };
    adminSocket.onclose = () => {
        console.log('Connection with game server has been dropped');
        let startStopButton = document.getElementById('startStopButton');
        startStopButton.disabled = true
    };
    return adminSocket;
}

function showPlayers(players) {
    let playersList = document.getElementById(PLAYERS);
    playersList.innerHTML = '';
    playersList.innerText = "Players:";

    for (let idx in players) {
        let player = document.createElement('li');
        playersList.appendChild(player);
        player.innerHTML = player.innerHTML + players[idx];
    }
}

function showStartStopButton(isStarted) {
    let startStopButton = document.getElementById('startStopButton');
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
    let startStopButton = document.getElementById('startStopButton');
    $.post("/admin", {"command": "start"}, () => {
        console.log('Game has been started');
        startStopButton.removeEventListener("click", handleStart);
        startStopButton.addEventListener("click", handleStop);
        startStopButton.innerText = "Stop Game"
    })
}

function handleStop() {
    let startStopButton = document.getElementById('startStopButton');
    $.post("/admin", {"command": "stop"}, () => {
        console.log('Game has been stopped');
        startStopButton.removeEventListener("click", handleStop);
        startStopButton.addEventListener("click", handleStart);
        startStopButton.innerText = "Start Game"
    })
}

function getRegenerateBoardButton() {
    let regenerateBoardButton = document.createElement('button');
    regenerateBoardButton.id = 'regenerateBoardButton';
    regenerateBoardButton.innerText = 'Regenerate Game Board';
    regenerateBoardButton.onclick = () => {
        $.post("/admin", {
            "command": "regenerate_game_board",
            "args": document.getElementById('boardSizeInput').value
        }, () => {
            console.log('Game board has been regenerated');
        })
    };
    return regenerateBoardButton
}

function getBoardSizeInput() {
    let boardSizeInput = document.createElement('input');
    boardSizeInput.type = 'text';
    boardSizeInput.id = 'boardSizeInput';
    boardSizeInput.oninput = (event) => {
        if (!/^\d+$/.test(event.target.value)) {
            alert('Invalid value ' + event.target.value);
            event.target.value = blocksNumber
        }
    };
    return boardSizeInput
}

main();

// TODO: add the rest of controls (add/remove guard, add/remove gold, resize/regenerate map, etc)