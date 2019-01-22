const game_port = '9000';
const hostname = window.location.hostname;
const url = "ws://" + hostname + ":" + game_port;
const admin_socket_url = url + "?client_type=Admin";
const PLAYERS = 'players';
const STARTED = 'started';
let adminSocket = undefined;


function main() {
    let playersList = document.createElement("ul");
    playersList.id = PLAYERS;
    playersList.innerText = "Players:";
    let startStopButton = document.createElement('button');
    startStopButton.id = 'startStopButton';
    document.body.appendChild(playersList);
    document.body.appendChild(startStopButton);
    adminSocket = getAdminSocket();
}

function getAdminSocket() {
    let adminSocket = new WebSocket(admin_socket_url);
    adminSocket.onmessage = (event) => {
        let sessionInfo = JSON.parse(event.data);
        console.log(sessionInfo);
        showPlayers(sessionInfo[PLAYERS]);
        showStartStopButton(sessionInfo[STARTED]);
    };
    return adminSocket;
}

function showPlayers(players) {
    let playersList = document.getElementById(PLAYERS);

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
    adminSocket.send('start');
    console.log('Game has been started');
    startStopButton.removeEventListener("click", handleStart);
    startStopButton.addEventListener("click", handleStop);
    startStopButton.innerText = "Stop Game"
}

function handleStop() {
    let startStopButton = document.getElementById('startStopButton');
    adminSocket.send('stop');
    console.log('Game has been stopped');
    startStopButton.removeEventListener("click", handleStop);
    startStopButton.addEventListener("click", handleStart);
    startStopButton.innerText = "Start Game"
}


main();

// TODO: add the rest of controls (add/remove guard, add/remove gold, resize/regenerate map, etc)
// TODO: add spinner for game started/stopped